from flask import Flask, render_template, request, redirect, session, flash
import psycopg2
import psycopg2.extras
import sqlite3
import qrcode
import uuid
import hashlib
import os
import io
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dpr_secret_key_2024_secure")

# Konfigurasi untuk development
app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "True").lower() == "true"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# PostgreSQL Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "dpr_dimsum")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Database type flag
USE_POSTGRESQL = False


def test_postgresql_connection():
    """Test if PostgreSQL is available"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        conn.close()
        return True
    except:
        return False


# Test PostgreSQL connection
if test_postgresql_connection():
    USE_POSTGRESQL = True
    print("✅ Using PostgreSQL database")
else:
    USE_POSTGRESQL = False
    print("⚠️ PostgreSQL not available, falling back to SQLite")
    print("💡 Please install PostgreSQL and update .env file for production use")


def get_db():
    """Get database connection (PostgreSQL or SQLite fallback)"""
    global USE_POSTGRESQL

    if USE_POSTGRESQL:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
            )
            return conn
        except psycopg2.Error as e:
            print(f"❌ PostgreSQL connection error: {e}")
            print("🔄 Falling back to SQLite")
            USE_POSTGRESQL = False
            # Fallback to SQLite
            conn = sqlite3.connect("database.db")
            conn.row_factory = sqlite3.Row
            return conn
    else:
        # Use SQLite
        conn = sqlite3.connect("database.db")
        conn.row_factory = sqlite3.Row
        return conn


def get_cursor():
    """Get database cursor"""
    db = get_db()
    if USE_POSTGRESQL:
        return db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        return db.cursor()


def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash


def is_logged_in():
    """Check if user is logged in"""
    return session.get("login", False)


# ========================
# LOGIN
# ========================


@app.route("/", methods=["GET", "POST"])
def login():
    if is_logged_in():
        return redirect("/dashboard")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor = get_cursor()
        if USE_POSTGRESQL:
            cursor.execute(
                "SELECT * FROM admin_users WHERE username=%s AND is_active=1",
                (username,),
            )
        else:
            cursor.execute(
                "SELECT * FROM admin_users WHERE username=? AND is_active=1",
                (username,),
            )

        admin = cursor.fetchone()

        if admin and verify_password(password, admin["password_hash"]):
            session["login"] = True
            session["username"] = admin["username"]
            return redirect("/dashboard")

        flash("Login gagal")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ========================
# DASHBOARD
# ========================


@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect("/")

    cursor = get_cursor()
    if USE_POSTGRESQL:
        cursor.execute("SELECT * FROM customers ORDER BY name")
    else:
        cursor.execute("SELECT * FROM customers ORDER BY name")

    customers = cursor.fetchall()

    # Get current user info
    user = {
        "full_name": session.get("username", "Admin"),
        "last_login": session.get(
            "last_login", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ),
    }

    return render_template("dashboard.html", customers=customers, user=user)


# ========================
# CUSTOMER
# ========================


@app.route("/add_customer", methods=["POST"])
def add_customer():
    name = request.form["name"]
    phone = request.form["phone"]

    cursor = get_cursor()
    if USE_POSTGRESQL:
        cursor.execute(
            "INSERT INTO customers (name, phone) VALUES (%s, %s)", (name, phone)
        )
    else:
        cursor.execute(
            "INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone)
        )

    return redirect("/dashboard")


@app.route("/delete_customer/<int:id>")
def delete_customer(id):
    cursor = get_cursor()
    if USE_POSTGRESQL:
        cursor.execute("DELETE FROM qr_tokens WHERE customer_id=%s", (id,))
        cursor.execute("DELETE FROM customers WHERE id=%s", (id,))
    else:
        cursor.execute("DELETE FROM qr_tokens WHERE customer_id=?", (id,))
        cursor.execute("DELETE FROM customers WHERE id=?", (id,))

    return redirect("/dashboard")


@app.route("/edit_customer/<int:id>")
def edit_customer(id):
    if not is_logged_in():
        return redirect("/")

    cursor = get_cursor()
    if USE_POSTGRESQL:
        cursor.execute("SELECT * FROM customers WHERE id=%s", (id,))
    else:
        cursor.execute("SELECT * FROM customers WHERE id=?", (id,))

    customer = cursor.fetchone()

    return render_template("edit_customer.html", customer=customer)


@app.route("/update_customer", methods=["POST"])
def update_customer():
    id = request.form["id"]
    name = request.form["name"]
    phone = request.form["phone"]

    cursor = get_cursor()
    if USE_POSTGRESQL:
        cursor.execute(
            "UPDATE customers SET name=%s, phone=%s WHERE id=%s", (name, phone, id)
        )
    else:
        cursor.execute(
            "UPDATE customers SET name=?, phone=? WHERE id=?", (name, phone, id)
        )

    return redirect("/dashboard")


@app.route("/register", methods=["GET", "POST"])
def register():
    if is_logged_in():
        return redirect("/dashboard")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        full_name = request.form.get("full_name", "").strip()

        # Basic validation
        if not username or not password or not confirm_password or not full_name:
            flash("❌ Semua field harus diisi!", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("❌ Password dan konfirmasi password tidak sama!", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("❌ Password minimal 6 karakter!", "error")
            return render_template("register.html")

        try:
            cursor = get_cursor()

            # Check if username already exists
            if USE_POSTGRESQL:
                cursor.execute(
                    "SELECT id FROM admin_users WHERE username=%s", (username,)
                )
            else:
                cursor.execute(
                    "SELECT id FROM admin_users WHERE username=?", (username,)
                )

            existing_user = cursor.fetchone()

            if existing_user:
                flash("❌ Username sudah digunakan!", "error")
                return render_template("register.html")

            # Create new admin user
            hashed_password = hash_password(password)

            if USE_POSTGRESQL:
                cursor.execute(
                    """INSERT INTO admin_users 
                       (username, password_hash, full_name, is_active, created_at) 
                       VALUES (%s, %s, %s, 1, %s)""",
                    (username, hashed_password, full_name, datetime.now()),
                )
            else:
                cursor.execute(
                    """INSERT INTO admin_users 
                       (username, password_hash, full_name, is_active, created_at) 
                       VALUES (?, ?, ?, 1, ?)""",
                    (username, hashed_password, full_name, datetime.now()),
                )

            flash("✅ Registrasi berhasil! Silakan login.", "success")
            return redirect("/")

        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
            return render_template("register.html")

    return render_template("register.html")


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Basic validation
        if not username or not old_password or not new_password or not confirm_password:
            flash("❌ Semua field harus diisi!", "error")
            return render_template("forgot_password.html")

        if new_password != confirm_password:
            flash("❌ Password baru dan konfirmasi password tidak sama!", "error")
            return render_template("forgot_password.html")

        if len(new_password) < 6:
            flash("❌ Password baru minimal 6 karakter!", "error")
            return render_template("forgot_password.html")

        try:
            cursor = get_cursor()

            if USE_POSTGRESQL:
                cursor.execute(
                    "SELECT * FROM admin_users WHERE username=%s AND is_active=1",
                    (username,),
                )
            else:
                cursor.execute(
                    "SELECT * FROM admin_users WHERE username=? AND is_active=1",
                    (username,),
                )

            admin = cursor.fetchone()

            if admin and verify_password(old_password, admin["password_hash"]):
                # Update password
                hashed_password = hash_password(new_password)

                if USE_POSTGRESQL:
                    cursor.execute(
                        "UPDATE admin_users SET password_hash=%s WHERE id=%s",
                        (hashed_password, admin["id"]),
                    )
                else:
                    cursor.execute(
                        "UPDATE admin_users SET password_hash=? WHERE id=?",
                        (hashed_password, admin["id"]),
                    )

                flash(
                    f"✅ Password untuk username '{username}' berhasil direset! Silakan login dengan password baru.",
                    "success",
                )
                return redirect("/")
            else:
                flash("❌ Username atau password lama salah!", "error")

        except Exception as e:
            flash("❌ Terjadi kesalahan sistem. Silakan coba lagi.", "error")

    return render_template("forgot_password.html")


# ========================
# QR GENERATE
# ========================

BASE_URL = "https://aplikasi-dpr-production.up.railway.app"


@app.route("/generate_qr/<int:id>", methods=["POST"])
def generate_qr(id):
    rakyat = int(request.form["rakyat"])
    pejabat = int(request.form["pejabat"])

    token = str(uuid.uuid4())

    cursor = get_cursor()
    if USE_POSTGRESQL:
        cursor.execute(
            "INSERT INTO qr_tokens(token, customer_id, rakyat, pejabat) VALUES(%s,%s,%s,%s)",
            (token, id, rakyat, pejabat),
        )
    else:
        cursor.execute(
            "INSERT INTO qr_tokens(token, customer_id, rakyat, pejabat) VALUES(?,?,?,?)",
            (token, id, rakyat, pejabat),
        )

    url = f"{BASE_URL}/scan/{token}"

    img = qrcode.make(url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render_template("qr.html", qr=img_base64)


# ========================
# SCAN QR
# ========================


@app.route("/scan/<token>")
def scan(token):
    cursor = get_cursor()
    if USE_POSTGRESQL:
        cursor.execute("SELECT * FROM qr_tokens WHERE token=%s", (token,))
    else:
        cursor.execute("SELECT * FROM qr_tokens WHERE token=?", (token,))

    data = cursor.fetchone()

    if not data:
        return "QR tidak valid"

    if data["used"] == 1:
        return "QR sudah digunakan"

    if USE_POSTGRESQL:
        cursor.execute(
            "UPDATE customers SET rakyat=rakyat+%s, pejabat=pejabat+%s WHERE id=%s",
            (data["rakyat"], data["pejabat"], data["customer_id"]),
        )
        cursor.execute("UPDATE qr_tokens SET used=1 WHERE token=%s", (token,))
    else:
        cursor.execute(
            "UPDATE customers SET rakyat=rakyat+?, pejabat=pejabat+? WHERE id=?",
            (data["rakyat"], data["pejabat"], data["customer_id"]),
        )
        cursor.execute("UPDATE qr_tokens SET used=1 WHERE token=?", (token,))

    return "Berhasil scan QR 🎉"


# ========================
# ERROR HANDLERS
# ========================


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template("owner_notification.html"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template("owner_notification.html"), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all other exceptions"""
    return render_template("owner_notification.html"), 500


# ========================
# INIT DATABASE
# ========================


def init_db():
    """Initialize database"""
    db = get_db()
    cursor = db.cursor()

    if USE_POSTGRESQL:
        # PostgreSQL syntax
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_users(
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                full_name TEXT,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS customers(
                id SERIAL PRIMARY KEY,
                name TEXT,
                phone TEXT,
                rakyat INTEGER DEFAULT 0,
                pejabat INTEGER DEFAULT 0
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS qr_tokens(
                id SERIAL PRIMARY KEY,
                token TEXT,
                customer_id INTEGER,
                rakyat INTEGER,
                pejabat INTEGER,
                used INTEGER DEFAULT 0
            )
        """
        )
    else:
        # SQLite syntax
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                full_name TEXT,
                last_login DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS customers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                rakyat INTEGER DEFAULT 0,
                pejabat INTEGER DEFAULT 0
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS qr_tokens(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT,
                customer_id INTEGER,
                rakyat INTEGER,
                pejabat INTEGER,
                used INTEGER DEFAULT 0
            )
        """
        )

    db.commit()

    # Create default admin if not exists
    create_default_admin()

    print("🚀 DPR Dimsum Application Starting...")
    print("📱 Login Page: http://localhost:5000")
    print("🔐 Default Login: owner / 123")


def create_default_admin():
    """Create default admin user if not exists"""
    db = get_db()
    cursor = db.cursor()

    # Check if admin exists
    if USE_POSTGRESQL:
        cursor.execute("SELECT id FROM admin_users LIMIT 1")
    else:
        cursor.execute("SELECT id FROM admin_users LIMIT 1")

    existing_admin = cursor.fetchone()

    if not existing_admin:
        # Create default admin
        default_password = "123"
        hashed_password = hash_password(default_password)

        if USE_POSTGRESQL:
            cursor.execute(
                """INSERT INTO admin_users 
                   (username, password_hash, full_name, is_active, created_at) 
                   VALUES (%s, %s, %s, 1, %s)""",
                ("owner", hashed_password, "Default Owner", datetime.now()),
            )
        else:
            cursor.execute(
                """INSERT INTO admin_users 
                   (username, password_hash, full_name, is_active, created_at) 
                   VALUES (?, ?, ?, 1, ?)""",
                ("owner", hashed_password, "Default Owner", datetime.now()),
            )

        db.commit()

        print("👤 Default admin user created: owner / 123")
    else:
        print("👤 Admin users already exist, keeping existing accounts")

    cursor.close()
    db.close()


if __name__ == "__main__":
    # Initialize database
    init_db()

    # Jalankan aplikasi dengan konfigurasi development
    print("🚀 DPR Dimsum Application Starting...")
    print("📱 Login Page: http://localhost:5000")
    print("🔐 Default Login: owner / 123")
    app.run(debug=True, host="0.0.0.0", port=5000)
