from flask import Flask, render_template, request, redirect, session, flash
<<<<<<< HEAD
import psycopg2
import psycopg2.extras
import sqlite3
=======
>>>>>>> e1385c467a769dacb26b117910e0754c7b950225
import qrcode
import uuid
import hashlib
import os
<<<<<<< HEAD
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dpr_secret_key_2024_secure")

# Konfigurasi untuk development
app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "True").lower() == "true"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
=======
import io
import psycopg2
import psycopg2.extras
import base64

app = Flask(__name__)
app.secret_key = "dpr_secret_key_2024_secure"
>>>>>>> e1385c467a769dacb26b117910e0754c7b950225

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
<<<<<<< HEAD
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
=======
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = True
    return conn
>>>>>>> e1385c467a769dacb26b117910e0754c7b950225

def get_cursor():
    db = get_db()
<<<<<<< HEAD
    cursor = db.cursor()

    if USE_POSTGRESQL:
        # PostgreSQL syntax
        # Create qr_tokens table
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

        # Create admin users table
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

        # Create customers table
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
    else:
        # SQLite syntax
        # Create qr_tokens table
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

        # Create admin users table
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

        # Create customers table
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


def check_admin_exists():
    """Check if any admin user exists"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM admin_users LIMIT 1")
    admin = cursor.fetchone()
    cursor.close()
    db.close()
    return admin is not None

=======
    return db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# ========================
# AUTH
# ========================
>>>>>>> e1385c467a769dacb26b117910e0754c7b950225

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    return hash_password(password) == password_hash

def is_logged_in():
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
        cursor.execute(
            "SELECT * FROM admin_users WHERE username=%s AND is_active=1",
            (username,)
        )
        admin = cursor.fetchone()

<<<<<<< HEAD
        try:
            db = get_db()

            if USE_POSTGRESQL:
                cursor = db.cursor(cursor_factory=psycopg2.extras.DictRow)
                cursor.execute(
                    "SELECT * FROM admin_users WHERE username=%s AND is_active=1",
                    (username,),
                )
                admin = cursor.fetchone()

                if admin and verify_password(password, admin["password_hash"]):
                    # Update last login
                    cursor.execute(
                        "UPDATE admin_users SET last_login=%s WHERE id=%s",
                        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), admin["id"]),
                    )
                    db.commit()

                    # Create session
                    session["login"] = True
                    session["username"] = admin["username"]
                    session["full_name"] = admin["full_name"]
                    session["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    session["login_time"] = datetime.now().timestamp()

                    flash(
                        f"✅ Selamat datang kembali, {admin['full_name']}!", "success"
                    )
                    return redirect("/dashboard")
                else:
                    flash("❌ Username atau password salah!", "error")

                cursor.close()
            else:
                # SQLite
                admin = db.execute(
                    "SELECT * FROM admin_users WHERE username=? AND is_active=1",
                    (username,),
                ).fetchone()

                if admin and verify_password(password, admin["password_hash"]):
                    # Update last login
                    db.execute(
                        "UPDATE admin_users SET last_login=? WHERE id=?",
                        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), admin["id"]),
                    )
                    db.commit()

                    # Create session
                    session["login"] = True
                    session["username"] = admin["username"]
                    session["full_name"] = admin["full_name"]
                    session["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    session["login_time"] = datetime.now().timestamp()

                    flash(
                        f"✅ Selamat datang kembali, {admin['full_name']}!", "success"
                    )
                    return redirect("/dashboard")
                else:
                    flash("❌ Username atau password salah!", "error")

            db.close()

        except Exception as e:
            flash("❌ Terjadi kesalahan sistem. Silakan coba lagi.", "error")
            print(f"Login error: {e}")
=======
        if admin and verify_password(password, admin["password_hash"]):
            session["login"] = True
            session["username"] = admin["username"]
            return redirect("/dashboard")

        flash("Login gagal")
>>>>>>> e1385c467a769dacb26b117910e0754c7b950225

    return render_template("login.html")

# ========================
# DASHBOARD
# ========================

@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect("/")

    cursor = get_cursor()
    cursor.execute("SELECT * FROM customers ORDER BY name")
    customers = cursor.fetchall()

    return render_template("dashboard.html", customers=customers)

# ========================
# CUSTOMER
# ========================

@app.route("/add_customer", methods=["POST"])
def add_customer():
    name = request.form["name"]
    phone = request.form["phone"]

    cursor = get_cursor()
    cursor.execute(
        "INSERT INTO customers (name, phone) VALUES (%s, %s)",
        (name, phone)
    )

    return redirect("/dashboard")

@app.route("/delete_customer/<int:id>")
def delete_customer(id):
    cursor = get_cursor()
    cursor.execute("DELETE FROM qr_tokens WHERE customer_id=%s", (id,))
    cursor.execute("DELETE FROM customers WHERE id=%s", (id,))
    return redirect("/dashboard")

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
    cursor.execute(
        "INSERT INTO qr_tokens(token, customer_id, rakyat, pejabat) VALUES(%s,%s,%s,%s)",
        (token, id, rakyat, pejabat)
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

    cursor.execute("SELECT * FROM qr_tokens WHERE token=%s", (token,))
    data = cursor.fetchone()

    if not data:
        return "QR tidak valid"

    if data["used"] == 1:
        return "QR sudah digunakan"

    cursor.execute(
        "UPDATE customers SET rakyat=rakyat+%s, pejabat=pejabat+%s WHERE id=%s",
        (data["rakyat"], data["pejabat"], data["customer_id"])
    )

    cursor.execute("UPDATE qr_tokens SET used=1 WHERE token=%s", (token,))

    return "Berhasil scan QR 🎉"

# ========================
# LOGOUT
# ========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
