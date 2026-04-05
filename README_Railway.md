# DPR Dimsum - Railway Deployment

## 🚀 Deploy ke Railway

### 📋 Prerequisites:
- GitHub repository
- Railway account
- SQLite database (included)

### 🔧 Setup:

1. **Push ke GitHub**
   ```bash
   git add .
   git commit -m "Ready for Railway deployment"
   git push origin main
   ```

2. **Deploy ke Railway**
   - Login ke Railway
   - Klik "New Project"
   - Pilih "Deploy from GitHub repo"
   - Pilih repository DPR-Dimsum
   - Railway akan auto-detect Flask app

3. **Environment Variables**
   ```env
   PORT=5000
   SECRET_KEY=dpr_secret_key_2024_secure
   ```

### 📁 File Structure:
```
DPR/
├── app.py              # Main Flask app
├── Procfile           # Railway process file
├── requirements.txt    # Python dependencies
├── .env      # Environment template
├── database.db       # SQLite database
├── templates/        # HTML templates
└── static/          # CSS & assets
```

### 🌐 URL Setelah Deploy:
- **Application**: `https://dpr-dimsum.up.railway.app`
- **Login**: owner / 123

### 📊 Features:
- ✅ SQLite database (auto-created)
- ✅ QR code generation
- ✅ Customer management
- ✅ Admin authentication
- ✅ Mobile responsive

### 🔧 Railway Configuration:
- **Runtime**: Python 3.9+
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Port**: 5000

### 💾 Database:
- **Type**: SQLite (database.db)
- **Location**: Same directory as app.py
- **Backup**: Auto-backup ke Railway storage

### 📱 Testing:
1. Buka URL Railway
2. Login dengan owner / 123
3. Test add customer
4. Test generate QR
5. Test scan QR

### 🔄 Auto-Deploy:
- Set up GitHub webhook
- Auto-deploy on push to main
- Zero-downtime deployment

### 📞 Support:
- Railway logs: Check di dashboard
- Database: SQLite file di Railway storage
- Issues: Check Railway deployment logs
