# HƯỚNG DẪN SETUP QHUN22 TRÊN MÁY MỚI

> Tài liệu dành cho việc clone project về máy mới và chạy được server trong thời gian ngắn nhất.

---

## 📋 Yêu cầu hệ thống

| Thành phần | Yêu cầu |
|:-----------|:---------|
| **OS** | Windows 10/11 (64-bit) |
| **Python** | 3.10.x (bắt buộc, khuyến nghị cài qua python.org) |
| **RAM** | Tối thiểu 4GB (8GB nếu dùng AI module) |
| **Disk** | ~500MB cho venv + packages |
| **Internet** | Cần khi cài packages lần đầu |

---

## 🚀 Cách 1: Setup tự động (Khuyến nghị)

### Bước 1 — Cài Python 3.10

1. Tải từ: <https://www.python.org/downloads/release/python-31011/>
2. Chạy installer, **tick ☑ "Add Python to PATH"** và **☑ "Install py launcher"**
3. Xác nhận: mở CMD gõ `py -3.10 --version` → phải ra `Python 3.10.x`

### Bước 2 — Chạy file bat

```
Click chuột phải vào qhun22.bat → "Run as administrator"
```

Hoặc mở CMD admin tại thư mục project:
```cmd
cd /d D:\PyToong\qhun22
qhun22.bat
```

### Bước 3 — Chọn lệnh 0

```
Chọn [0] Setup Full Tự Động
```

Script sẽ **tự động** chạy toàn bộ:
1. Kiểm tra Python 3.10
2. Xóa venv cũ (nếu bị lỗi user khác) → tạo venv mới
3. Nâng cấp pip/setuptools/wheel
4. Cài `requirements.txt` (core Django)
5. Cài `ai/ai_requirements.txt` (AI module, nếu có)
6. Cài thêm `Pillow`, `PyJWT`, `cryptography` (thường thiếu)
7. Chạy `migrate --run-syncdb`
8. Kiểm tra file `.env`
9. Hiển thị tổng kết

### Bước 4 — Tạo file `.env`

Nếu chưa có file `.env` trong thư mục gốc, tạo mới với nội dung:

```env
# === Django ===
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# === VNPay (sandbox) ===
VNPAY_TMN_CODE=
VNPAY_HASH_SECRET=
VNPAY_URL=https://sandbox.vnpayment.vn/paymentv2/vpcpay.html
VNPAY_RETURN_URL=http://localhost:8000/vnpay/return/
VNPAY_IPN_URL=http://localhost:8000/vnpay/ipn/

# === MoMo (test) ===
MOMO_PARTNER_CODE=MOMO
MOMO_ACCESS_KEY=
MOMO_SECRET_KEY=
MOMO_ENDPOINT=
MOMO_RETURN_URL=
MOMO_IPN_URL=

# === VietQR ===
BANK_ID=TCB
BANK_ACCOUNT_NO=
BANK_ACCOUNT_NAME=

# === Cloudflare Turnstile ===
CLOUDFLARE_TURNSTILE_SITE_KEY=
CLOUDFLARE_TURNSTILE_SECRET_KEY=

# === Google OAuth2 ===
GOOGLE_OAUTH2_CLIENT_ID=
GOOGLE_OAUTH2_CLIENT_SECRET=

# === Claude AI (Chatbot) ===
ANTHROPIC_API_KEY=

# === Email (Gmail SMTP) ===
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

### Bước 5 — Khởi động server

```
Chọn [1] Khởi động Server
```

Truy cập: <http://127.0.0.1:8000/>

---

## 🔧 Cách 2: Setup thủ công (CMD/PowerShell)

```bash
# 1. Di chuyển vào thư mục project
cd /d D:\PyToong\qhun22

# 2. Tạo virtual environment
py -3.10 -m venv .venv

# 3. Kích hoạt venv
# CMD:
.venv\Scripts\activate.bat
# PowerShell:
.venv\Scripts\Activate.ps1

# 4. Nâng cấp pip
python -m pip install --upgrade pip setuptools wheel

# 5. Cài thư viện core
pip install -r requirements.txt

# 6. Cài thêm packages thường thiếu
pip install Pillow PyJWT cryptography

# 7. (Tùy chọn) Cài module AI
pip install -r ai/ai_requirements.txt

# 8. Chạy migration
python manage.py migrate --run-syncdb

# 9. Tạo tài khoản admin (lần đầu)
python manage.py createsuperuser

# 10. Chạy server
python manage.py runserver
```

---

## ⚠️ Lỗi thường gặp & Cách fix

### 1. `Python was not found` hoặc `'python' is not recognized`

**Nguyên nhân:** Python chưa cài hoặc chưa thêm vào PATH.

**Fix:**
```
1. Cài Python 3.10 từ python.org
2. Khi cài, tick ☑ "Add Python to PATH"
3. Mở CMD mới, gõ: py -3.10 --version
```

### 2. `No Python at 'C:\Users\XXX\...\python.exe'`

**Nguyên nhân:** Venv được tạo trên máy khác (user khác), đường dẫn Python không khớp.

**Fix:**
```bash
# Xóa venv cũ
rmdir /s /q venv
rmdir /s /q .venv

# Tạo lại venv
py -3.10 -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

> **Đây là lỗi RẤT phổ biến** khi copy project giữa các máy. File bat mới (lệnh 0) sẽ tự phát hiện và fix lỗi này.

### 3. `ModuleNotFoundError: No module named 'django'`

**Nguyên nhân:** Chưa kích hoạt venv hoặc chưa cài packages.

**Fix:**
```bash
.venv\Scripts\activate.bat    # Kích hoạt venv trước
pip install -r requirements.txt
```

### 4. `ModuleNotFoundError: No module named 'jwt'`

**Nguyên nhân:** `PyJWT` không nằm trong `requirements.txt` nhưng `django-allauth` (Google OAuth) cần nó.

**Fix:**
```bash
pip install PyJWT cryptography
```

### 5. `Cannot use ImageField because Pillow is not installed`

**Nguyên nhân:** `Pillow` không nằm trong `requirements.txt` nhưng Django `ImageField` cần nó.

**Fix:**
```bash
pip install Pillow
```

### 6. `ImportError: ... allauth ...`

**Nguyên nhân:** `django-allauth` phiên bản mới thay đổi API.

**Fix:**
```bash
pip install -U django-allauth
```

### 7. `OperationalError: no such table`

**Nguyên nhân:** Chưa chạy migrate.

**Fix:**
```bash
python manage.py migrate --run-syncdb
```

### 8. `CSRF verification failed` hoặc `Forbidden (403)`

**Nguyên nhân:** Truy cập server bằng domain/IP không nằm trong `ALLOWED_HOSTS`.

**Fix:** Thêm domain vào file `.env`:
```env
ALLOWED_HOSTS=127.0.0.1,localhost,192.168.1.100
```

### 9. Chatbot không trả lời / lỗi 500

**Nguyên nhân:** Thiếu `ANTHROPIC_API_KEY` hoặc chưa cài AI packages.

**Fix:**
```bash
# Thêm key vào .env
ANTHROPIC_API_KEY=sk-ant-xxxxxxx

# Cài AI packages
pip install -r ai/ai_requirements.txt
```

### 10. PowerShell: `cannot be loaded because running scripts is disabled`

**Nguyên nhân:** Execution policy chặn script `.ps1`.

**Fix (chạy PowerShell as Admin):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 11. `pip install` bị lỗi build wheel (C++ required)

**Nguyên nhân:** Một số package AI cần compiler C++.

**Fix:**
```
1. Cài "Build Tools for Visual Studio" từ:
   https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Chọn "Desktop development with C++"
3. Chạy lại pip install
```

---

## 📂 Cấu trúc thư mục quan trọng

```
qhun22/
├── .env                  ← File cấu hình (KHÔNG push git) 
├── .venv/                ← Virtual environment (KHÔNG push git)
├── db.sqlite3            ← Database SQLite (có data mẫu)
├── manage.py             ← Django CLI
├── requirements.txt      ← Packages core
├── qhun22.bat            ← Script quản lý (chạy trên Windows)
├── ai/                   ← Module AI/Chatbot
│   └── ai_requirements.txt  ← Packages AI riêng
├── config/               ← Settings Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── store/                ← App chính (models, views, urls)
├── templates/            ← HTML templates
├── static/               ← CSS, JS, logos
├── media/                ← File upload (ảnh SP, banner)
├── data/                 ← Vector store cho AI
├── logs/                 ← Log chatbot
└── docs/                 ← Tài liệu kỹ thuật
```

---

## 🔑 Checklist sau khi setup

- [ ] Python 3.10 đã cài và có trong PATH
- [ ] Venv đã tạo thành công (`.venv/` hoặc `venv/`)
- [ ] `pip install -r requirements.txt` không lỗi
- [ ] `pip install Pillow PyJWT cryptography` đã cài
- [ ] File `.env` đã tạo
- [ ] `python manage.py migrate` chạy xong
- [ ] `python manage.py runserver` → truy cập được <http://127.0.0.1:8000/>
- [ ] (Tùy chọn) `python manage.py createsuperuser` → vào admin
- [ ] (Tùy chọn) AI packages: `pip install -r ai/ai_requirements.txt`

---

## 📌 Lệnh hữu ích

| Lệnh | Mô tả |
|:------|:-------|
| `python manage.py runserver` | Chạy server dev (port 8000) |
| `python manage.py runserver 9000` | Chạy server dev (port tùy chọn) |
| `python manage.py migrate` | Chạy migration database |
| `python manage.py createsuperuser` | Tạo tài khoản admin |
| `python manage.py collectstatic` | Thu thập static files (production) |
| `pip freeze > requirements_freeze.txt` | Xuất danh sách package hiện tại |
| `deactivate` | Thoát virtual environment |
