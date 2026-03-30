from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import qrcode
import uuid
import hashlib
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "dpr_secret_key_2024_secure"  # More secure secret key


# ========================
# DATABASE
# ========================


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    db = get_db()

    # Create qr_tokens table
    db.execute(
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
    db.execute(
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

    db.commit()

    # Create default admin user if not exists
    admin = db.execute(
        "SELECT * FROM admin_users WHERE username=?", ("owner",)
    ).fetchone()
    if not admin:
        password_hash = hashlib.sha256("123".encode()).hexdigest()
        db.execute(
            "INSERT INTO admin_users (username, password_hash, full_name) VALUES (?, ?, ?)",
            ("owner", password_hash, "Owner DPR Dimsum"),
        )
        db.commit()


init_db()


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
# LOGIN & REGISTER
# ========================


@app.route("/reset_admin", methods=["GET", "POST"])
def reset_admin():
    """Reset all admin users - only for development/setup"""
    if request.method == "POST":
        try:
            db = get_db()

            # Delete all admin users
            db.execute("DELETE FROM admin_users")
            db.commit()

            flash(
                "✅ Semua akun owner telah direset! Silakan register akun baru.",
                "success",
            )
            return redirect("/register")

        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
            return redirect("/")

    return render_template("reset_admin.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # Redirect to dashboard if already logged in
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
            db = get_db()

            # Check if username already exists
            existing_user = db.execute(
                "SELECT id FROM admin_users WHERE username=?",
                (username,),
            ).fetchone()

            if existing_user:
                flash("❌ Username sudah digunakan!", "error")
                return render_template("register.html")

            # Check if any admin exists
            existing_admin = db.execute(
                "SELECT id FROM admin_users LIMIT 1",
            ).fetchone()

            if existing_admin:
                flash("❌ Admin sudah terdaftar! Hubungi administrator.", "error")
                return render_template("register.html")

            # Create new admin user
            hashed_password = hash_password(password)
            db.execute(
                """INSERT INTO admin_users 
                   (username, password_hash, full_name, is_active, created_at) 
                   VALUES (?, ?, ?, 1, ?)""",
                (username, hashed_password, full_name, datetime.now()),
            )
            db.commit()

            flash("✅ Registrasi berhasil! Silakan login.", "success")
            return redirect("/")

        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
            return render_template("register.html")

    return render_template("register.html")


@app.route("/", methods=["GET", "POST"])
def login():
    # Redirect to dashboard if already logged in
    if is_logged_in():
        return redirect("/dashboard")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Basic validation
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

                flash(f"✅ Selamat datang kembali, {admin['full_name']}!", "success")
                return redirect("/dashboard")
            else:
                flash("❌ Username atau password salah!", "error")

        except Exception as e:
            flash("❌ Terjadi kesalahan sistem. Silakan coba lagi.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Logout user and clear session"""
    session.clear()
    flash("✅ Anda telah berhasil logout!", "success")
    return redirect("/")


@app.route("/profile")
def profile():
    """User profile page"""
    if not is_logged_in():
        return redirect("/")

    current_user = get_current_user()
    return render_template("profile.html", user=current_user)


# ========================
# DASHBOARD
# ========================


@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        flash("❌ Silakan login terlebih dahulu!", "error")
        return redirect("/")

    db = get_db()
    customers = db.execute("SELECT * FROM customers ORDER BY name").fetchall()

    # Get current user info
    current_user = get_current_user()

    return render_template("dashboard.html", customers=customers, user=current_user)


# ========================
# TAMBAH CUSTOMER
# ========================


@app.route("/add_customer", methods=["POST"])
def add_customer():

    name = request.form["name"]
    phone = request.form["phone"]

    db = get_db()

    db.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone))

    db.commit()

    return redirect("/dashboard")


# ========================
# HALAMAN EDIT CUSTOMER
# ========================


@app.route("/edit_customer/<int:id>")
def edit_customer(id):

    db = get_db()

    customer = db.execute("SELECT * FROM customers WHERE id=?", (id,)).fetchone()

    return render_template("edit_customer.html", customer=customer)


# ========================
# SIMPAN SETTING KUPON
# ========================


@app.route("/prepare_coupon", methods=["POST"])
def prepare_coupon():

    id = request.form["id"]
    rakyat = int(request.form["rakyat"])
    pejabat = int(request.form["pejabat"])

    session["pending_id"] = id
    session["pending_rakyat"] = rakyat
    session["pending_pejabat"] = pejabat

    return redirect("/generate_qr")


# ========================
# GENERATE QR
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

    url = f"https://lithic-tripinnately-noe.ngrok-free.dev/scan/{token}"

    img = qrcode.make(url)

    path = "static/qr.png"

    img.save(path)

    return render_template("qr.html", qr=path)


@app.route("/scan/<token>")
def scan(token):

    db = get_db()

    data = db.execute("SELECT * FROM qr_tokens WHERE token=?", (token,)).fetchone()

    if not data:
        return "QR tidak valid"

    if data["used"] == 1:
        return "QR sudah digunakan"

    db.execute(
        "UPDATE customers SET rakyat=rakyat+?, pejabat=pejabat+? WHERE id=?",
        (data["rakyat"], data["pejabat"], data["customer_id"]),
    )

    db.execute("UPDATE qr_tokens SET used=1 WHERE token=?", (token,))

    db.commit()

    customer = db.execute(
        "SELECT * FROM customers WHERE id=?", (data["customer_id"],)
    ).fetchone()

    return render_template("message.html", customer=customer)


@app.route("/update_coupon", methods=["POST"])
def update_coupon():

    id = request.form["id"]

    rakyat = max(0, int(request.form["rakyat"]))
    pejabat = max(0, int(request.form["pejabat"]))

    db = get_db()

    db.execute(
        "UPDATE customers SET rakyat=?, pejabat=? WHERE id=?", (rakyat, pejabat, id)
    )

    db.commit()

    return redirect("/dashboard")


# ========================
# SCAN QR (UPDATE DATABASE)
# ========================


@app.route("/confirm/<int:id>/<int:rakyat>/<int:pejabat>")
def confirm(id, rakyat, pejabat):

    db = get_db()

    # tambah kupon ke database
    db.execute(
        "UPDATE customers SET rakyat = rakyat + ?, pejabat = pejabat + ? WHERE id = ?",
        (rakyat, pejabat, id),
    )

    db.commit()

    # ambil data terbaru
    customer = db.execute("SELECT * FROM customers WHERE id=?", (id,)).fetchone()

    return render_template("message.html", customer=customer)


@app.route("/generate_claim/<int:id>/<paket>")
def generate_claim(id, paket):

    token = str(uuid.uuid4())

    db = get_db()

    db.execute(
        "INSERT INTO qr_tokens(token, customer_id, rakyat, pejabat) VALUES(?,?,?,?)",
        (token, id, 0, 0),
    )

    db.commit()

    url = f"https://lithic-tripinnately-noe.ngrok-free.dev/claim/{token}/{paket}"

    img = qrcode.make(url)

    path = "static/claim_qr.png"

    img.save(path)

    return render_template("qr.html", qr=path)


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


@app.route("/update_customer", methods=["POST"])
def update_customer():

    id = request.form["id"]
    name = request.form["name"]
    phone = request.form["phone"]

    db = get_db()
    db.execute("UPDATE customers SET name=?, phone=? WHERE id=?", (name, phone, id))
    db.commit()

    return redirect("/dashboard")


@app.route("/delete_customer/<int:id>")
def delete_customer(id):

    db = get_db()

    # Hapus semua QR tokens terkait customer
    db.execute("DELETE FROM qr_tokens WHERE customer_id=?", (id,))

    # Hapus customer
    db.execute("DELETE FROM customers WHERE id=?", (id,))

    db.commit()

    return redirect("/dashboard")


app.run(debug=True)
