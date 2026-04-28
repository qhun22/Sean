# QHUN22 MOBILE - HỆ THỐNG THƯƠNG MẠI ĐIỆN TỬ BÁN ĐIỆN THOẠI DI ĐỘNG

**Đồ án: Phát triển ứng dụng Python**
**Sinh viên thực hiện: Trương Quang Huy**

## 1. MỤC TIÊU VÀ PHẠM VI ĐẦU RA
Dự án QHUN22 Mobile được xây dựng với mục tiêu mô phỏng và thực thi một hệ thống thương mại điện tử hoàn chỉnh, áp dụng thực tế cho ngành hàng thiết bị di động. Hệ thống đảm bảo đáp ứng toàn diện các yêu cầu về mặt nghiệp vụ, từ khâu tương tác người dùng đến xử lý đơn hàng và thống kê quản trị.

### Phạm vi hệ thống:
- Kiến trúc 3 tầng rõ ràng, tích hợp đa nền tảng công nghệ.
- Tổ chức phân quyền chặt chẽ theo 3 cấp độ người dùng: Khách vãng lai (Guest), Khách hàng (User), Quản trị viên (Admin).
- Tích hợp công nghệ AI (RAG) và các cổng thanh toán điện tử thực tế.
- Đáp ứng trên 5 thực thể dữ liệu có quan hệ ràng buộc, đảm bảo tính toàn vẹn của CSDL.

## 2. KIẾN TRÚC HỆ THỐNG & CÔNG NGHỆ
Hệ thống sử dụng mô hình MVC (Model-View-Controller) thông qua kiến trúc MVT (Model-View-Template) của Django.

### Danh sách công nghệ:
- **Ngôn ngữ lập trình:** Python 3.10+
- **Web Framework:** Django 4.2
- **Cơ sở dữ liệu:** SQLite3 (Môi trường Phát triển) / PostgreSQL (Môi trường Production)
- **Giao diện (Frontend):** HTML5, CSS3, Vanilla JavaScript (Thiết kế Responsive, hỗ trợ Mobile First)
- **Thanh toán điện tử:** VNPay, MoMo, VietQR
- **Trí tuệ nhân tạo (AI Chatbot):** Anthropic Claude API, FAISS (Vector Database), Sentence-Transformers
- **Bảo mật:** Cloudflare Turnstile (Anti-Bot), django-allauth, OAuth2 (Google Login)

## 3. CHỨC NĂNG CỐT LÕI

### Nhóm chức năng Khách hàng (User/Guest)
- **Xác thực Người dùng:** Đăng ký, đăng nhập, xác thực qua Google OAuth2, khôi phục mật khẩu bằng OTP.
- **Trải nghiệm Mua sắm:** Tìm kiếm sản phẩm (hỗ trợ Autocomplete), lọc sản phẩm theo tiêu chí (Giá, Thương hiệu, Dung lượng), So sánh sản phẩm.
- **Quản lý Đơn hàng:** Thêm vào giỏ hàng, quản lý mã giảm giá (Coupon), thanh toán tích hợp API, tra cứu trạng thái đơn hàng thực tế.
- **Tương tác:** Chatbot AI tư vấn sản phẩm, đánh giá sản phẩm, quản lý danh sách yêu thích (Wishlist).

### Nhóm chức năng Quản trị (Admin Dashboard)
- **Quản trị Dữ liệu (CRUD):** Quản lý Sản phẩm, Thương hiệu, Biến thể sản phẩm (Màu sắc, Dung lượng), Bài viết (Blog), Banner quảng cáo, Chương trình Khuyến mãi (Hot Sale).
- **Quản trị Đơn hàng:** Theo dõi đơn hàng, cập nhật trạng thái, xử lý yêu cầu hoàn tiền/hủy đơn.
- **Quản trị Người dùng:** Quản lý danh sách khách hàng, phân quyền truy cập.
- **Báo cáo & Thống kê:** Biểu đồ doanh thu (Theo Tháng/Năm), top sản phẩm bán chạy, xuất báo cáo ra file Excel.

## 4. THIẾT KẾ CƠ SỞ DỮ LIỆU
Hệ thống xây dựng hơn 10 thực thể dữ liệu với các mối quan hệ ràng buộc (1-n, n-n).
- **Thực thể trung tâm:** CustomUser, Product, Brand, Category.
- **Thực thể giao dịch:** Order, OrderItem, Cart, CartItem, PendingQRPayment, Coupon.
- **Thực thể phụ trợ:** ProductReview, BlogPost, SiteConfig.

## 5. HƯỚNG DẪN TRIỂN KHAI VÀ CÀI ĐẶT LOCAL

Yêu cầu tiên quyết: Máy tính đã cài đặt Python 3.10+ và Pip.

### Phương pháp 1: Tự động (Dành cho Windows)
Dự án cung cấp sẵn script tự động hóa toàn bộ quá trình cài đặt.
1. Mở thư mục chứa source code.
2. Chạy file `qhun22.bat`.
3. Nhập phím `0` (Setup full local) để hệ thống tự động tạo Virtual Environment, cài đặt dependencies, migrate CSDL và khởi tạo server.

### Phương pháp 2: Thủ công (Cross-platform)
Mở Terminal/Command Prompt tại thư mục gốc của dự án và chạy các lệnh sau:
```bash
# 1. Tạo và kích hoạt môi trường ảo
python -m venv .venv
# Trường hợp Windows:
.venv\Scripts\activate
# Trường hợp Linux/MacOS:
source .venv/bin/activate

# 2. Cài đặt thư viện
pip install --upgrade pip
pip install -r requirements.txt
pip install -r ai/ai_requirements.txt

# 3. Chuẩn bị Cơ sở dữ liệu
python manage.py migrate
python manage.py createsuperuser

# 4. Khởi chạy máy chủ cục bộ
python manage.py runserver
```
Truy cập: `http://127.0.0.1:8000/`

## 6. CẤU HÌNH MÔI TRƯỜNG (.env)
Để đảm bảo an toàn thông tin, toàn bộ khóa bí mật (API Keys, Secrets) không được code cứng vào source. Người triển khai cần tạo file `.env` tại thư mục gốc.
Mẫu file cấu hình:

```env
# Core Django
SECRET_KEY=chuoi-bao-mat-cua-django
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Cổng thanh toán VNPay
VNPAY_TMN_CODE=
VNPAY_HASH_SECRET=
VNPAY_URL=https://sandbox.vnpayment.vn/paymentv2/vpcpay.html
VNPAY_RETURN_URL=http://localhost:8000/vnpay/return/
VNPAY_IPN_URL=http://localhost:8000/vnpay/ipn/

# Cổng thanh toán MoMo
MOMO_PARTNER_CODE=MOMO
MOMO_ACCESS_KEY=
MOMO_SECRET_KEY=
MOMO_ENDPOINT=https://test-payment.momo.vn/v2/gateway/api/create
MOMO_RETURN_URL=http://localhost:8000/momo/return/
MOMO_IPN_URL=http://localhost:8000/momo/ipn/

# Thanh toán VietQR
BANK_ID=TCB
BANK_ACCOUNT_NO=
BANK_ACCOUNT_NAME=

# Xác thực và AI
CLOUDFLARE_TURNSTILE_SITE_KEY=
CLOUDFLARE_TURNSTILE_SECRET_KEY=
GOOGLE_OAUTH2_CLIENT_ID=
GOOGLE_OAUTH2_CLIENT_SECRET=
ANTHROPIC_API_KEY=

# Cấu hình Email (Gửi OTP)
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

## 7. LƯU Ý KHI TRIỂN KHAI LÊN PRODUCTION (CPANEL/VPS)
Khi triển khai dự án lên môi trường máy chủ thực tế, cần đặc biệt tuân thủ các quy tắc sau:
1. Chuyển `DEBUG=False` trong file `.env`.
2. Khai báo đầy đủ tên miền vào `ALLOWED_HOSTS`.
3. Chạy lệnh `python manage.py collectstatic` để hệ thống tập hợp toàn bộ file tĩnh (CSS, JS, Video) vào thư mục chung, ngăn chặn tình trạng lỗi giao diện hoặc không phát được video.
4. Đảm bảo cấu hình Routing (Web Server) trỏ chính xác thư mục `/static` và `/media`.

## 8. TÀI LIỆU MINH CHỨNG
Kiểm thử đã được viết sẵn tại thư mục `store/tests/`. Chạy kiểm thử bằng lệnh: `python manage.py test`.
- Báo cáo tổng hợp kiến trúc: `docs/BAI DU AN_PTUD Python_Nhom 06.pdf`
- Tài liệu Test case thanh toán: `docs/dulieuthanhtoan.md`
