# QHUN22 MOBILE SHOP - HỆ THỐNG THƯƠNG MẠI ĐIỆN TỬ BÁN ĐIỆN THOẠI

**Đồ án: Phát triển ứng dụng Python**
**Sinh viên: Trương Quang Huy**

---

## TÓM TẮT DỰ ÁN

Đây là hệ thống thương mại điện tử bán điện thoại di động, xây dựng bằng Django 4.2. Hệ thống hỗ trợ:

- Mua sắm, đặt hàng, tra cứu đơn hàng
- Thanh toán qua VNPay, MoMo, VietQR
- Đăng nhập bằng Google OAuth2
- Chatbot AI (Claude) hỗ trợ tư vấn sản phẩm
- Quản trị hệ thống (Dashboard Admin)
- Xuất báo cáo doanh thu ra Excel

---

## 1. YÊU CẦU HỆ THỐNG

| Phần mềm | Phiên bản |
|----------|-----------|
| Python | 3.10 trở lên |
| Pip | Mới nhất |
| RAM | 2GB trở lên |
| Ổ đĩa trống | 5GB trở lên |

---

## 2. CÀI ĐẶT TRÊN MÁY LOCAL

### Bước 1: Tải source code về máy

Tải toàn bộ mã nguồn vào một thư mục.

### Bước 2: Tạo môi trường ảo (Virtual Environment)

```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt (Windows)
.venv\Scripts\activate

# Kích hoạt (Linux/Mac)
source .venv/bin/activate
```

### Bước 3: Cài đặt thư viện

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 4: Tạo file cấu hình .env

Tạo file `.env` trong thư mục gốc, nội dung ví dụ:

```env
SECRET_KEY=qhun22-secret-key-local-dev
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Email (dùng Gmail)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Các API keys khác (để trống hoặc giá trị mặc định)
VNPAY_URL=https://sandbox.vnpayment.vn/paymentv2/vpcpay.html
VNPAY_RETURN_URL=http://localhost:8000/vnpay/return/
MOMO_ENDPOINT=https://test-payment.momo.vn/v2/gateway/api/create
MOMO_RETURN_URL=http://localhost:8000/momo/return/
```

> **Lưu ý về Email:** Nếu dùng Gmail, cần tạo App Password thay vì mật khẩu thông thường. Xem hướng dẫn: https://support.google.com/accounts/answer/185833

### Bước 5: Khởi tạo cơ sở dữ liệu

```bash
# Tạo các bảng dữ liệu
python manage.py migrate

# Tạo tài khoản quản trị (Admin)
python manage.py createsuperuser
# Nhập email và mật khẩu theo yêu cầu
```

### Bước 6: Thu thập file tĩnh

```bash
# Thu thập file CSS, JS vào thư mục staticfiles
python manage.py collectstatic
```

### Bước 7: Khởi động máy chủ

```bash
python manage.py runserver
```

Truy cập: **http://127.0.0.1:8000/**

---

## 3. HƯỚNG DẪN DEPLOY LÊN HOSTING (VPS/CPANEL)

### Bước 1: Chuẩn bị file cấu hình production

Tạo file `.env` trong thư mục gốc trên server với nội dung:

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

> **Quan trọng:** Thay `SECRET_KEY` bằng chuỗi ngẫu nhiên 50+ ký tự. Không dùng key mặc định!

### Bước 2: Tải code lên hosting

Upload toàn bộ mã nguồn (trừ `.pyc`, `__pycache__`, `.venv`) lên server.

### Bước 3: Cài đặt Python trên server

```bash
# Tạo môi trường ảo
python3 -m venv venv

# Kích hoạt
source venv/bin/activate

# Cài đặt thư viện
pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 4: Thu thập file tĩnh

```bash
python manage.py collectstatic --noinput
```

### Bước 5: Cấu hình Web Server

**Nếu dùng Nginx + Gunicorn:**

```nginx
location /static/ {
    alias /path/to/staticfiles/;
}

location /media/ {
    alias /path/to/media/;
}
```

**Nếu dùng Apache (.htaccess hoặc VirtualHost):**

```apache
Alias /static/ /path/to/staticfiles/
Alias /media/ /path/to/media/
```

### Bước 6: Khởi động lại dịch vụ

```bash
# Gunicorn
gunicorn config.wsgi:application --bind 127.0.0.1:8000

# Hoặc systemd service
sudo systemctl restart qhun22
```

---

## 4. CÁC CHỨC NĂNG CHÍNH

### 4.1. Danh sách sản phẩm
- Hiển thị sản phẩm theo danh mục, thương hiệu
- Lọc theo giá, dung lượng, màu sắc
- Tìm kiếm với gợi ý (Autocomplete)
- So sánh sản phẩm

### 4.2. Giỏ hàng và đặt hàng
- Thêm/bớt sản phẩm khỏi giỏ hàng
- Nhập mã giảm giá (Coupon)
- Chọn phương thức thanh toán: VietQR, VNPay, MoMo, Tiền mặt

### 4.3. Quản lý đơn hàng
- Tra cứu trạng thái đơn hàng
- Xem chi tiết đơn hàng
- Yêu cầu hủy đơn / Hoàn tiền

### 4.4. Tài khoản người dùng
- Đăng ký / Đăng nhập
- Đăng nhập bằng Google
- Quên mật khẩu (gửi OTP qua email)
- Cập nhật thông tin cá nhân

### 4.5. Chatbot AI
- Tư vấn sản phẩm bằng tiếng Việt
- Trả lời câu hỏi về sản phẩm, giá cả
- Tìm kiếm sản phẩm theo yêu cầu

### 4.6. Bảng điều khiển Quản trị (Admin)
- Quản lý sản phẩm, thương hiệu, màu sắc, dung lượng
- Quản lý đơn hàng, cập nhật trạng thái
- Quản lý người dùng
- Xem báo cáo doanh thu (theo tháng, năm)
- Xuất báo cáo ra file Excel

---

## 5. CẤU TRÚC THƯ MỤC

```
qhun22/
├── config/                  # Cấu hình Django (settings.py, urls.py)
├── store/                   # Ứng dụng chính
│   ├── models.py           # Các bảng dữ liệu
│   ├── views.py            # Các hàm xử lý request
│   ├── urls.py             # Đường dẫn (routes)
│   └── chatbot_service.py  # Chatbot AI (Claude)
├── templates/               # Các file HTML
├── static/                  # File CSS, JS, hình ảnh
├── media/                   # Hình ảnh sản phẩm, banner
├── staticfiles/             # File tĩnh đã thu thập
├── docs/                    # Tài liệu đồ án
├── db.sqlite3               # Cơ sở dữ liệu
├── manage.py                # Lệnh quản lý Django
├── requirements.txt         # Danh sách thư viện
├── .env                     # Cấu hình môi trường (không push lên git!)
└── README.md                # File này
```

---

## 6. CÁC LỆNH QUẢN LÝ THƯỜNG DÙNG

```bash
# Khởi động máy chủ
python manage.py runserver

# Tạo bảng dữ liệu
python manage.py migrate
```
