from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import qrcode
import uuid
import hashlib
import os
import base64
from io import BytesIO
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret")


def get_db():
    """Get database connection"""
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash


def is_logged_in():
    """Check if user is logged in"""
    return "login" in session and session.get("login", False)


def get_current_user():
    """Get current logged in user info"""
    if is_logged_in():
        return {
            "username": session.get("username"),
            "full_name": session.get("full_name"),
            "last_login": session.get("last_login"),
        }
    return None


# ========================
# LOGIN
# ========================


@app.route("/", methods=["GET", "POST"])
def login():
    if is_logged_in():
        return redirect("/dashboard")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("❌ Username dan password harus diisi!", "error")
            return render_template("login.html")

        try:
            db = get_db()
            admin = db.execute(
                "SELECT * FROM admin_users WHERE username=? AND is_active=1",
                (username,),
            ).fetchone()

            if admin and verify_password(password, admin["password_hash"]):
                db.execute(
                    "UPDATE admin_users SET last_login=? WHERE id=?",
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), admin["id"]),
                )
                db.commit()

                session["login"] = True
                session["username"] = admin["username"]
                session["full_name"] = admin["full_name"]
                session["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                flash(f"✅ Selamat datang kembali, {admin['full_name']}!", "success")
                return redirect("/dashboard")
            else:
                flash("❌ Username atau password salah!", "error")

            db.close()

        except Exception as e:
            flash("❌ Terjadi kesalahan sistem. Silakan coba lagi.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("✅ Anda telah berhasil logout!", "success")
    return redirect("/")


# ========================
# REGISTER & FORGOT PASSWORD
# ========================


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validasi input
        if not full_name or not username or not password:
            flash("❌ Semua field harus diisi!", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("❌ Password tidak cocok!", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("❌ Password minimal 6 karakter!", "error")
            return render_template("register.html")

        try:
            db = get_db()

            # Cek username sudah ada
            existing_user = db.execute(
                "SELECT id FROM admin_users WHERE username=?", (username,)
            ).fetchone()

            if existing_user:
                flash("❌ Username sudah digunakan!", "error")
                return render_template("register.html")

            # Buat user baru
            hashed_password = hash_password(password)
            db.execute(
                """INSERT INTO admin_users 
                   (username, password_hash, full_name, is_active, created_at) 
                   VALUES (?, ?, ?, 1, ?)""",
                (username, hashed_password, full_name, datetime.now()),
            )
            db.commit()

            flash("✅ Akun berhasil dibuat! Silakan login.", "success")
            return redirect("/")

        except Exception as e:
            flash("❌ Terjadi kesalahan. Silakan coba lagi.", "error")
            return render_template("register.html")

    return render_template("register.html")


@app.route("/forgot_password")
def forgot_password():
    return render_template("forgot_password.html")


@app.route("/profile")
def profile():
    if not is_logged_in():
        return redirect("/")
    current_user = get_current_user()
    return render_template("profile.html", user=current_user)


@app.route("/generate_claim/<int:id>/<paket>")
def generate_claim(id, paket):
    if not is_logged_in():
        return redirect("/")

    token = str(uuid.uuid4())

    db = get_db()
    db.execute(
        "INSERT INTO qr_tokens(token, customer_id, rakyat, pejabat) VALUES(?,?,?,?)",
        (token, id, 0, 0),
    )
    db.commit()

    base_url = request.host_url.rstrip("/")
    url = f"{base_url}/claim/{token}/{paket}"

    img = qrcode.make(url)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render_template("qr.html", qr=qr_base64)


@app.route("/claim/<token>/<paket>")
def claim(token, paket):
    db = get_db()
    data = db.execute("SELECT * FROM qr_tokens WHERE token=?", (token,)).fetchone()

    if not data:
        return "QR tidak valid"

    if data["used"] == 1:
        return "QR sudah digunakan"

    if paket == "rakyat":
        db.execute("UPDATE customers SET rakyat=0 WHERE id=?", (data["customer_id"],))
        message = "Selamat anda mendapatkan 1 paket rakyat gratis"
    else:
        db.execute("UPDATE customers SET pejabat=0 WHERE id=?", (data["customer_id"],))
        message = "Selamat anda mendapatkan 1 paket pejabat gratis"

    db.execute("UPDATE qr_tokens SET used=1 WHERE token=?", (token,))
    db.commit()

    return render_template("claim_success.html", message=message)


@app.route("/quick_update/<int:id>/<paket>/<aksi>")
def quick_update(id, paket, aksi):
    if not is_logged_in():
        return redirect("/")

    db = get_db()
    customer = db.execute("SELECT * FROM customers WHERE id=?", (id,)).fetchone()

    rakyat = customer["rakyat"]
    pejabat = customer["pejabat"]

    if paket == "rakyat":
        if aksi == "plus":
            rakyat += 1
        else:
            rakyat = max(0, rakyat - 1)
    elif paket == "pejabat":
        if aksi == "plus":
            pejabat += 1
        else:
            pejabat = max(0, pejabat - 1)

    db.execute(
        "UPDATE customers SET rakyat=?, pejabat=? WHERE id=?", (rakyat, pejabat, id)
    )
    db.commit()

    return redirect("/edit_customer/" + str(id))


# ========================
# DASHBOARD
# ========================


@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect("/")

    db = get_db()
    customers = db.execute("SELECT * FROM customers ORDER BY name").fetchall()
    current_user = get_current_user()

    return render_template("dashboard.html", customers=customers, user=current_user)


# ========================
# CUSTOMER
# ========================


@app.route("/add_customer", methods=["POST"])
def add_customer():
    name = request.form["name"]
    phone = request.form["phone"]

    db = get_db()
    db.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone))
    db.commit()

    return redirect("/dashboard")


@app.route("/delete_customer/<int:id>")
def delete_customer(id):
    db = get_db()
    db.execute("DELETE FROM qr_tokens WHERE customer_id=?", (id,))
    db.execute("DELETE FROM customers WHERE id=?", (id,))
    db.commit()

    return redirect("/dashboard")


@app.route("/edit_customer/<int:id>")
def edit_customer(id):
    if not is_logged_in():
        return redirect("/")

    db = get_db()
    customer = db.execute("SELECT * FROM customers WHERE id=?", (id,)).fetchone()

    return render_template("edit_customer.html", customer=customer)


@app.route("/update_customer", methods=["POST"])
def update_customer():
    id = request.form["id"]
    name = request.form["name"]
    phone = request.form["phone"]

    db = get_db()
    db.execute("UPDATE customers SET name=?, phone=? WHERE id=?", (name, phone, id))
    db.commit()

    return redirect("/dashboard")


# ========================
# QR GENERATE
# ========================


@app.route("/generate_qr/<int:id>", methods=["POST"])
def generate_qr(id):
    rakyat = int(request.form["rakyat"])
    pejabat = int(request.form["pejabat"])

    token = str(uuid.uuid4())

    db = get_db()
    db.execute(
        "INSERT INTO qr_tokens(token, customer_id, rakyat, pejabat) VALUES(?,?,?,?)",
        (token, id, rakyat, pejabat),
    )
    db.commit()

    # Use dynamic base URL for Railway
    if request.environ.get("HTTP_X_FORWARDED_PROTO"):
        base_url = f"{request.environ.get('HTTP_X_FORWARDED_PROTO')}://{request.environ.get('HTTP_HOST')}"
    else:
        base_url = request.host_url.rstrip("/")

    url = f"{base_url}/scan/{token}"

    print(f"📷 QR URL generated: {url}")

    img = qrcode.make(url)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render_template("qr.html", qr=qr_base64)


@app.route("/scan/<token>")
def scan(token):
    print(f"🔍 Scanning QR token: {token}")

    db = get_db()
    data = db.execute("SELECT * FROM qr_tokens WHERE token=?", (token,)).fetchone()

    if not data:
        print("❌ QR tidak valid")
        return "QR tidak valid"

    if data["used"] == 1:
        print("❌ QR sudah digunakan")
        return "QR sudah digunakan"

    print(
        f"📊 Processing: rakyat={data['rakyat']}, pejabat={data['pejabat']}, customer_id={data['customer_id']}"
    )

    db.execute(
        "UPDATE customers SET rakyat=rakyat+?, pejabat=pejabat+? WHERE id=?",
        (data["rakyat"], data["pejabat"], data["customer_id"]),
    )
    db.execute("UPDATE qr_tokens SET used=1 WHERE token=?", (token,))
    db.commit()

    customer = db.execute(
        "SELECT * FROM customers WHERE id=?", (data["customer_id"])
    ).fetchone()

    print(f"✅ QR scanned successfully for customer: {customer['name']}")

    return render_template("message.html", customer=customer)


# ========================
# ERROR HANDLERS
# ========================


@app.errorhandler(404)
def not_found(error):
    return render_template("owner_notification.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("owner_notification.html"), 500


@app.errorhandler(Exception)
def handle_exception(error):
    return render_template("owner_notification.html"), 500


# ========================
# INIT DATABASE
# ========================


def init_db():
    """Initialize database"""
    db = get_db()
    cursor = db.cursor()

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

    cursor.execute("SELECT id FROM admin_users LIMIT 1")
    existing_admin = cursor.fetchone()

    if not existing_admin:
        default_password = "123"
        hashed_password = hash_password(default_password)

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
    init_db()
    app.run()
