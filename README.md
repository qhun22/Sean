# QHUN22 MOBILE SHOP - HE THONG THUONG MAI DIEN TU BAN DIEN THOAI

**Do an: Phat trien ung dung Python**
**Sinh vien: Truong Quang Huy**

---

## TOM TAT DU AN

Day la he thong thuong mai dien tu ban dien thoai di dong, xay dung bang Django 4.2. He thong ho tro:

- Mua sam, dat hang, tra cuu don hang
- Thanh toan qua VNPay, MoMo, VietQR
- Dang nhap bang Google OAuth2
- Chatbot AI (Claude) ho tro tu van san pham
- Quan tri he thong (Dashboard Admin)
- Xuat bao cao doanh thu ra Excel

---

## 1. YEU CAU HE THONG

| Phan mem | Phien ban |
|----------|-----------|
| Python | 3.10 tro len |
| Pip | Moi nhat |
| RAM | 2GB tro len |
| O dia trong | 5GB tro len |

---

## 2. CAI DAT MAY TINH (LOCAL)

### Buoc 1: Tai source code ve may

Download toan bo source code vao mot thu muc.

### Buoc 2: Tao moi truong ao (Virtual Environment)

```bash
# Tao moi truong ao
python -m venv .venv

# Kich hoat (Windows)
.venv\Scripts\activate

# Kich hoat (Linux/Mac)
source .venv/bin/activate
```

### Buoc 3: Cai dat thu vien

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Buoc 4: Tao file cau hinh .env

Tao file ten `.env` trong thu muc goc, noi dung nhu sau:

```env
SECRET_KEY=qhun22-secret-key-local-dev
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Email (dung Gmail)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Cac API keys khac (deu trong hoac gia tri mac dinh)
VNPAY_URL=https://sandbox.vnpayment.vn/paymentv2/vpcpay.html
VNPAY_RETURN_URL=http://localhost:8000/vnpay/return/
MOMO_ENDPOINT=https://test-payment.momo.vn/v2/gateway/api/create
MOMO_RETURN_URL=http://localhost:8000/momo/return/
```

> **Luu y ve Email:** Neu dung Gmail, can tao App Password thay vi mat khau thuong. Xem huong dan: https://support.google.com/accounts/answer/185833

### Buoc 5: Khoi tao co so du lieu

```bash
# Tao cac bang du lieu
python manage.py migrate

# Tao tai khoan quan tri (Admin)
python manage.py createsuperuser
# Nhap email va mat khau theo yeu cau
```

### Buoc 6: Thu muc static va media

```bash
# Thu thap file CSS, JS vao thu muc staticfiles
python manage.py collectstatic
```

### Buoc 7: Khoi dong may chu

```bash
python manage.py runserver
```

Truy cap: **http://127.0.0.1:8000/**

---

## 3. HUONG DAN DEPLOY LEN HOSTING (VPS/CPANEL)

### Buoc 1: Chuan bi file cau hinh production

Tao file `.env` trong thu muc goc tren server voi noi dung:

```env
SECRET_KEY=tao-chuoi-bao-mat-50-ky-tu-ngau-nhien
DEBUG=False
ALLOWED_HOSTS=qhun22.com,www.qhun22.com

EMAIL_HOST_USER=qhun22@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

VNPAY_URL=https://sandbox.vnpayment.vn/paymentv2/vpcpay.html
VNPAY_RETURN_URL=https://qhun22.com/vnpay/return/
VNPAY_IPN_URL=https://qhun22.com/vnpay/ipn/

MOMO_ENDPOINT=https://test-payment.momo.vn/v2/gateway/api/create
MOMO_RETURN_URL=https://qhun22.com/momo/return/
MOMO_IPN_URL=https://qhun22.com/momo/ipn/
```

> **Quan trong:** Thay `SECRET_KEY` bang chuoi ngau nhien 50+ ky tu. Khong dung key mac dinh!

### Buoc 2: Tai file len hosting

Upload toan bo source code (tru `.pyc`, `__pycache__`, `.venv`) len server.

### Buoc 3: Cai dat Python tren server

```bash
# Tao moi truong ao
python3 -m venv venv

# Kich hoat
source venv/bin/activate

# Cai dat thu vien
pip install --upgrade pip
pip install -r requirements.txt
```

### Buoc 4: Thu thap file tinh (Static Files)

```bash
python manage.py collectstatic --noinput
```

### Buoc 5: Cau hinh Web Server

**Neu dung Nginx + Gunicorn:**

```nginx
location /static/ {
    alias /path/to/staticfiles/;
}

location /media/ {
    alias /path/to/media/;
}
```

**Neu dung Apache (.htaccess hoac VirtualHost):**

```apache
Alias /static/ /path/to/staticfiles/
Alias /media/ /path/to/media/
```

### Buoc 6: Khoi dong lai service

```bash
# Gunicorn
gunicorn config.wsgi:application --bind 127.0.0.1:8000

# Hoac systemd service
sudo systemctl restart qhun22
```

---

## 4. CAC CHUC NANG CHINNH

### 4.1. Danh sach san pham
- Hien thi san pham theo danh muc, thuong hieu
- Loc theo gia, dung luong, mau sac
- Tim kiem voi goi y (Autocomplete)
- So sanh san pham

### 4.2. Gio hang va dat hang
- Them/bot san pham khoi gio hang
- Nhap ma giam gia (Coupon)
- Chon phuong thuc thanh toan: VietQR, VNPay, MoMo, Tien mat

### 4.3. Quan ly don hang
- Tra cuu trang thai don hang
- Xem chi tiet don hang
- Yeu cau huy don / Hoan tien

### 4.4. Tai khoan nguoi dung
- Dang ky / Dang nhap
- Dang nhap bang Google
- Quen mat khau (gui OTP qua email)
- Cap nhat thong tin ca nhan

### 4.5. Chatbot AI
- Tu van san pham bang tieng Viet
- Tra loi cau hoi ve san pham, gia ca
- Tim kiem san pham theo yeu cau

### 4.6. Bang dieu khien Quan tri (Admin)
- Quan ly san pham, thuong hieu, mau sac, dung luong
- Quan ly don hang, cap nhat trang thai
- Quan ly nguoi dung
- Xem bao cao doanh thu (Theo thang, nam)
- Xuat bao cao ra file Excel

---

## 5. CAU TRUC THU MUC

```
qhun22/
├── config/                  # Cau hinh Django (settings.py, urls.py)
├── store/                   # Ung dung chinh
│   ├── models.py           # Cac bang du lieu
│   ├── views.py            # Cac ham xu ly request
│   ├── urls.py             # Duong dan (routes)
│   └── chatbot_service.py  # Chatbot AI (Claude)
├── templates/               # Cac file HTML
├── static/                  # File CSS, JS, hinh anh
├── media/                   # Hinh anh san pham, banner
├── staticfiles/             # File tinh da thu thap
├── docs/                    # Tai lieu do an
├── db.sqlite3               # Co so du lieu
├── manage.py                # Lenh quan ly Django
├── requirements.txt         # Danh sach thu vien
├── .env                     # Cau hinh moi truong (khong push len git!)
└── README.md                # File nay
```

---

## 6. CAC LENH QUAN LY THUONG DUNG

```bash
# Khoi dong may chu
python manage.py runserver

# Tao bang du lieu
python manage.py migrate

# Tao tai khoan admin
python manage.py createsuperuser

# Thu thap file tinh
python manage.py collectstatic

# Xem duong dan
python manage.py show_urls

# Kiem tra loi cau hinh
python manage.py check

# Shell Python
python manage.py shell
```

---

## 7. GIAI QUYET SU CO THUONG GAP

### Loi: "Module not found"
```bash
pip install ten-module
```

### Loi: "Database locked"
Thoat tat ca trinh duyet, tat server, chay lai.

### Loi: "Email not sent"
1. Kiem tra `EMAIL_HOST_USER` va `EMAIL_HOST_PASSWORD`
2. Dam bao da tao App Password tren Gmail
3. Kiem tra dia chi email nhan co dung khong

### Loi: "Static files not loading"
```bash
python manage.py collectstatic
```
Kiem tra cau hinh `STATIC_ROOT` trong `settings.py`.

### Loi: "DEBUG=False nhung website loi"
Kiem tra `ALLOWED_HOSTS` trong `.env` da chua domain chua.

---

## 8. THONG TIN LIEN HE

- **Sinh vien:** Truong Quang Huy
- **Email:** qhun22@gmail.com
- **Website:** https://qhun22.com

---

## 9. CAM ON

Cam on da su dung san pham!

---

**Cap nhat lan cuoi:** 30/04/2026
