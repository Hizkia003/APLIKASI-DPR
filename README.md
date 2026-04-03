# 🍔 DPR Dimsum Application

Aplikasi manajemen kupon dimsum dengan sistem login dan QR code generation.

## 🚀 Quick Start

### 1. **Install Dependencies**

```bash
pip install flask qrcode[pil] sqlite3
```

### 2. **Run Application**

```bash
python app.py
```

### 3. **Access Application**

- **URL**: http://localhost:5000
- **Auto-Reset**: Semua akun otomatis dihapus setiap start
- **First Time**: Akan diarahkan ke registrasi (belum ada admin)
- **Login Setelah Registrasi**: Gunakan credentials yang didaftarkan

## 📱 Features

### 🔐 **Smart Authentication System**

- **Auto-Reset**: Hapus semua admin setiap aplikasi dibuka
- **Auto-Check**: Cek keberadaan admin user
- **First Access**: Redirect ke registrasi (belum ada admin)
- **Login Page**: Halaman utama setelah admin terdaftar
- **Registration**: Hanya boleh 1 admin user
- **Session Management**: Secure session handling
- **Auto-redirect**: Login otomatis ke dashboard jika sudah login

### 📊 **Dashboard**

- **Customer Management**: Tambah, edit, hapus pelanggan
- **Coupon Tracking**: Monitor kupon rakyat dan pejabat
- **Statistics**: Real-time statistik pelanggan
- **Action Buttons**: Edit, delete, klaim kupon

### 📱 **QR Code Generation**

- **Dynamic QR**: Generate QR code untuk tambah kupon
- **Mobile Friendly**: Responsive design untuk semua device
- **Instructions**: Cara scan QR code yang jelas

### 🎯 **Coupon System**

- **Dual Types**: Kupon Rakyat & Kupon Pejabat
- **Progress Tracking**: Visual progress bars
- **Claim System**: Klaim hadiah setelah 15 kupon
- **Auto-reset**: Reset otomatis setelah klaim

## 🎨 Design Features

### 📱 **Responsive Design**

- **Desktop**: Full-featured layout
- **Tablet**: Optimized medium screens
- **Mobile**: Compact touch-friendly interface

### 🎨 **Modern UI**

- **Gradient Buttons**: Beautiful gradient effects
- **Smooth Animations**: CSS transitions dan hover effects
- **Icon Integration**: Emoji icons untuk visual appeal
- **Consistent Theme**: Unified purple gradient theme

### 🔙 **Enhanced Back Button**

- **Bold Icon**: `◀` arrow yang tebal
- **Modern Styling**: Rounded square dengan gradient
- **Interactive**: Hover dan active animations
- **Consistent**: Same design across all pages

## 📁 File Structure

```
DPR/
├── app.py                 # Main Flask application
├── database.db            # SQLite database
├── static/
│   └── style.css         # Global styles
├── templates/
│   ├── login.html         # Login page (FIRST PAGE)
│   ├── register.html       # Registration page
│   ├── dashboard.html      # Main dashboard
│   ├── edit_customer.html # Edit customer with single-row layout
│   ├── qr.html           # QR code generation
│   ├── message.html       # Success messages
│   ├── claim_success.html # Claim confirmation
│   ├── profile.html       # User profile
│   └── reset_admin.html  # Admin reset
└── README.md             # This file
```

## 🔧 Configuration

### 📊 **Database Setup**

- **Auto-initialization**: Database dibuat otomatis
- **Default Admin**: User `owner` dengan password `123`
- **Tables**: `customers`, `admin_users`, `qr_tokens`

### 🛡️ **Security**

- **Password Hashing**: SHA-256 encryption
- **Session Management**: Secure Flask sessions
- **Input Validation**: Form validation untuk semua input
- **SQL Injection Protection**: Parameterized queries

## 📱 Routes Structure

### 🔐 **Authentication Routes**

- `/` - **Login page (HALAMAN PERTAMA)**
- `/register` - Registration page
- `/logout` - Logout and clear session
- `/profile` - User profile

### 📊 **Main Routes**

- `/dashboard` - Main dashboard (requires login)
- `/add_customer` - Add new customer (POST)
- `/edit_customer/<id>` - Edit customer page
- `/update_customer` - Update customer data (POST)
- `/delete_customer/<id>` - Delete customer

### 📱 **QR & Coupon Routes**

- `/generate_qr/<id>` - Generate QR code for customer
- `/generate_claim/<id>/<type>` - Generate claim page
- `/update_coupon` - Update coupon manually (POST)
- `/delete_customer/<id>` - Delete customer with confirmation

## 🎯 Usage Instructions

### 1. **First Time Setup**

1. Run `python app.py`
2. **Console Output**:
   ```
   🗑️ Semua akun owner telah dihapus otomatis!
   📝 Silakan registrasi akun baru.
   ```
3. Open http://localhost:5000
4. **Auto-redirect ke registrasi** (belum ada admin)
5. Register akun owner pertama kali
6. Login dengan credentials yang didaftarkan
7. Add customers dan manage coupons

### 2. **Daily Operations**

1. Run `python app.py` (auto-reset semua akun)
2. Open http://localhost:5000
3. **Register akun baru** (karena semua akun dihapus)
4. Login dengan credentials baru
5. Add new customers
6. Generate QR codes untuk tambah kupon
7. Monitor progress kupon
8. Process klaim saat 15 kupon tercapai

### 3. **Admin Management**

- **Auto-Reset**: Setiap start aplikasi, semua akun dihapus
- **Single Admin**: Hanya 1 admin user yang aktif
- **Fresh Start**: Selalu mulai dengan akun baru
- **No Manual Reset**: Tidak perlu fitur hapus manual

### 4. **Security Benefits**

- **Clean State**: Tidak ada admin lama yang tersimpan
- **Single Access**: Hanya 1 user yang bisa login
- **Session Security**: Auto-clear saat aplikasi restart
- **No Default Accounts**: Tidak ada credentials bawaan

## 🎨 Customization

### 🎨 **Theme Colors**

- **Primary**: `#667eea` (Purple)
- **Secondary**: `#764ba2` (Dark Purple)
- **Success**: `#28a745` (Green)
- **Danger**: `#dc3545` (Red)

### 📱 **Responsive Breakpoints**

- **Desktop**: `> 1024px`
- **Tablet**: `≤ 768px`
- **Mobile**: `≤ 480px`
- **Small Mobile**: `≤ 360px`

## 🚀 Deployment

### 🐳 **Development**

```bash
python app.py
# Debug mode enabled
# Auto-reload on changes
```

### 🏭 **Production**

```bash
export FLASK_ENV=production
python app.py
# Debug mode disabled
# Optimized for production
```

## 📞 Troubleshooting

### 🔧 **Common Issues**

1. **Database Error**: Hapus `database.db` dan restart
2. **Port Conflict**: Ubah port di `app.run()`
3. **QR Code Error**: Install `qrcode[pil]` package
4. **Static Files**: Check `static/` folder permissions

### 🐛 **Debug Mode**

- **Enabled**: `app.config['DEBUG'] = True`
- **Logs**: Console output untuk debugging
- **Auto-reload**: Restart on file changes

## 📝 Notes

- **First Page**: Login page selalu muncul pertama
- **Default Admin**: `owner` / `123` (ubah setelah setup)
- **Mobile Ready**: Responsive design untuk semua devices
- **Security**: Password hashing dan session management
- **Scalable**: Easy to add new features

---

🍔 **DPR Dimsum** - Aplikasi manajemen kupon modern dengan QR code integration!
