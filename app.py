from flask import Flask, render_template, request, redirect, session, flash
import qrcode
import uuid
import hashlib
import os
import io
import psycopg2
import psycopg2.extras
import base64

app = Flask(__name__)
app.secret_key = "dpr_secret_key_2024_secure"

# ========================
# DATABASE
# ========================

def get_db():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = True
    return conn

def get_cursor():
    db = get_db()
    return db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# ========================
# AUTH
# ========================

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

        if admin and verify_password(password, admin["password_hash"]):
            session["login"] = True
            session["username"] = admin["username"]
            return redirect("/dashboard")

        flash("Login gagal")

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
