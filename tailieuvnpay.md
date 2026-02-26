# Tài liệu tích hợp VNPay Payment Gateway - QHUN22

> **Ngày tích hợp:** 26/02/2026  
> **Cập nhật lần cuối:** 26/02/2026  
> **Môi trường:** Sandbox (TEST)  
> **Framework:** Django 4.2.11  

---

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Thông tin cấu hình VNPay](#2-thông-tin-cấu-hình-vnpay)
3. [Danh sách file đã tạo / chỉnh sửa](#3-danh-sách-file-đã-tạo--chỉnh-sửa)
4. [Chi tiết từng thành phần](#4-chi-tiết-từng-thành-phần)
   - 4.1 [Settings – Cấu hình VNPay](#41-settings--cấu-hình-vnpay)
   - 4.2 [Model – VNPayPayment](#42-model--vnpaypayment)
   - 4.3 [Model – Order (cập nhật)](#43-model--order-cập-nhật)
   - 4.4 [Utility – VNPayUtil](#44-utility--vnpayutil)
   - 4.5 [Views – Xử lý thanh toán](#45-views--xử-lý-thanh-toán)
   - 4.6 [URLs – Định tuyến](#46-urls--định-tuyến)
   - 4.7 [Template – Giao diện checkout](#47-template--giao-diện-checkout)
   - 4.8 [JavaScript – Xử lý phía client](#48-javascript--xử-lý-phía-client)
   - 4.9 [Admin – Quản lý trong Django Admin](#49-admin--quản-lý-trong-django-admin)
   - 4.10 [Migration – Database](#410-migration--database)
   - 4.11 [Template – Trang đặt hàng thành công](#411-template--trang-đặt-hàng-thành-công)
5. [Luồng thanh toán (Payment Flow)](#5-luồng-thanh-toán-payment-flow)
6. [Chi tiết kỹ thuật: Checksum & Bảo mật](#6-chi-tiết-kỹ-thuật-checksum--bảo-mật)
7. [Mã lỗi VNPay (Response Codes)](#7-mã-lỗi-vnpay-response-codes)
8. [Chuyển sang môi trường Production](#8-chuyển-sang-môi-trường-production)
9. [Troubleshooting](#9-troubleshooting)
10. [Lịch sử cập nhật (Changelog)](#10-lịch-sử-cập-nhật-changelog)

---

## 1. Tổng quan

Tích hợp cổng thanh toán **VNPay** vào trang checkout của QHUN22 Mobile Shop. Trước đó, VNPay được hiển thị với badge **"Bảo trì"** và không cho chọn. Sau khi tích hợp:

- Bỏ trạng thái bảo trì, cho phép user chọn VNPay làm phương thức thanh toán
- Khi user chọn VNPay → Click "ĐẶT HÀNG" → Redirect sang môi trường sandbox VNPay
- Sau khi thanh toán thành công → Tự động tạo Order với mã tra cứu `QHUN` + 5 số random → Redirect sang trang thành công
- Sau khi thanh toán thất bại → Redirect về checkout với thông báo lỗi
- Không cần cài thêm package nào (không có package `vnpay` trên PyPI), tự implement bằng `hashlib`, `hmac`, `urllib`

---

## 2. Thông tin cấu hình VNPay

| Thông tin | Giá trị |
|-----------|---------|
| **Terminal ID (vnp_TmnCode)** | `981P6A3M` |
| **Secret Key (vnp_HashSecret)** | `3MNKGRKED41AFWF4KJH88GCWH9KS73N5` |
| **URL Thanh toán (Sandbox)** | `https://sandbox.vnpayment.vn/paymentv2/vpcpay.html` |
| **Return URL** | `http://localhost:8000/vnpay/return/` |
| **IPN URL** | `http://localhost:8000/vnpay/ipn/` |
| **API Version** | `2.1.0` |
| **Command** | `pay` |
| **Order Type** | `billpayment` |

---

## 3. Danh sách file đã tạo / chỉnh sửa

### File mới tạo

| File | Mô tả |
|------|--------|
| `store/vnpay_utils.py` | Class tiện ích VNPay (tạo URL, checksum, verify response) |
| `store/migrations/0024_vnpay_payment.py` | Migration tạo bảng `VNPayPayment` |
| `store/migrations/0025_order_code_payment_method.py` | Migration thêm `order_code`, `payment_method`, `vnpay_order_code` vào Order |
| `templates/store/order_success.html` | Trang thông báo đặt hàng thành công |

### File đã chỉnh sửa

| File | Thay đổi |
|------|----------|
| `config/settings.py` | Thêm block `VNPAY_CONFIG` |
| `store/models.py` | Thêm model `VNPayPayment`, cập nhật Order (thêm `order_code`, `payment_method`, `vnpay_order_code`) |
| `store/views.py` | Thêm 4 views: `vnpay_create`, `vnpay_return`, `vnpay_ipn`, `order_success` |
| `config/urls.py` | Thêm route `/vnpay/return/` và `/vnpay/ipn/` |
| `store/urls.py` | Thêm route `/vnpay/create/` và `/order/success/<order_code>/` |
| `templates/store/checkout.html` | Bỏ badge "Bảo trì" VNPay, thêm biến JS |
| `static/js/checkout.js` | Thêm hàm `initiateVNPayPayment()`, xử lý khi chọn VNPay |
| `store/admin.py` | Đăng ký `VNPayPayment` vào Django Admin |

---

## 4. Chi tiết từng thành phần

### 4.1 Settings – Cấu hình VNPay

**File:** `config/settings.py`

Thêm dictionary `VNPAY_CONFIG` ở cuối file:

```python
VNPAY_CONFIG = {
    'vnp_TmnCode': os.getenv('VNPAY_TMN_CODE', '981P6A3M'),
    'vnp_HashSecret': os.getenv('VNPAY_HASH_SECRET', '3MNKGRKED41AFWF4KJH88GCWH9KS73N5'),
    'vnp_Url': os.getenv('VNPAY_URL', 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'),
    'vnp_ReturnUrl': os.getenv('VNPAY_RETURN_URL', 'http://localhost:8000/vnpay/return/'),
    'vnp_IpnUrl': os.getenv('VNPAY_IPN_URL', 'http://localhost:8000/vnpay/ipn/'),
    'vnp_OrderType': 'billpayment',
    'vnp_Version': '2.1.0',
    'vnp_Command': 'pay',
}
```

**Đặc điểm:**

- Tất cả giá trị nhạy cảm đều hỗ trợ đọc từ biến môi trường (`.env`) thông qua `os.getenv()`
- Giá trị mặc định là thông tin sandbox để dev có thể chạy ngay mà không cần `.env`
- Khi chuyển production, chỉ cần thay đổi biến môi trường, không cần sửa code

**Biến môi trường tương ứng (nếu muốn dùng `.env`):**

```env
VNPAY_TMN_CODE=981P6A3M
VNPAY_HASH_SECRET=3MNKGRKED41AFWF4KJH88GCWH9KS73N5
VNPAY_URL=https://sandbox.vnpayment.vn/paymentv2/vpcpay.html
VNPAY_RETURN_URL=http://localhost:8000/vnpay/return/
VNPAY_IPN_URL=http://localhost:8000/vnpay/ipn/
```

---

### 4.2 Model – VNPayPayment

**File:** `store/models.py`

```python
class VNPayPayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ thanh toán'),
        ('paid', 'Đã thanh toán'),
        ('failed', 'Thất bại'),
        ('cancelled', 'Đã hủy'),
    ]

    user              = ForeignKey(CustomUser)          # Khách hàng
    amount            = DecimalField(max_digits=15)     # Số tiền (VND)
    order_code        = CharField(max_length=50)        # Mã đơn hàng VNPay (unique)
    transaction_no    = CharField(max_length=50)        # Mã giao dịch từ VNPay trả về
    transaction_status= CharField(max_length=20)        # Mã trạng thái VNPay
    status            = CharField(max_length=20)        # Trạng thái nội bộ
    response_code     = CharField(max_length=10)        # Response code từ VNPay
    response_message  = CharField(max_length=255)       # Message từ VNPay
    pay_method        = CharField(max_length=50)        # Phương thức thanh toán
    created_at        = DateTimeField(auto_now_add)     # Thời gian tạo
    updated_at        = DateTimeField(auto_now)         # Cập nhật cuối
    paid_at           = DateTimeField(null=True)        # Thời gian thanh toán thành công
```

**Ý nghĩa các trạng thái:**

| Status | Mô tả | Khi nào xảy ra |
|--------|--------|-----------------|
| `pending` | Chờ thanh toán | Vừa tạo yêu cầu, chưa redirect sang VNPay |
| `paid` | Đã thanh toán | VNPay trả `vnp_ResponseCode = '00'` |
| `failed` | Thất bại | VNPay trả code khác `'00'` (bị từ chối, lỗi, v.v.) |
| `cancelled` | Đã hủy | User hủy giao dịch trên trang VNPay (code `'99'`) |

**Format mã đơn hàng (`order_code`):**

```
QHun-YYYYMMDDHHMMSS-XXXXXXXX
```

- Prefix `QHun-` → nhận diện thương hiệu
- `YYYYMMDDHHMMSS` → timestamp chính xác đến giây
- `XXXXXXXX` → 8 ký tự random từ UUID (tránh trùng)
- Ví dụ: `QHun-20260226143052-A1B2C3D4`

---

### 4.3 Model – Order (cập nhật)

**File:** `store/models.py`

Thêm 3 field mới vào model `Order` để hỗ trợ VNPay và mã tra cứu:

```python
class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'COD'),
        ('vietqr', 'VietQR'),
        ('vnpay', 'VNPay'),
    ]
    
    order_code = CharField(max_length=20, unique=True)      # Mã tra cứu: QHUN + 5 số
    payment_method = CharField(max_length=20, choices=...)   # Phương thức thanh toán
    vnpay_order_code = CharField(max_length=50, blank=True)  # Liên kết với VNPayPayment
    # ... các field cũ giữ nguyên
```

**Mã tra cứu đơn hàng (`order_code`):**

- Format: `QHUN` + 5 số ngẫu nhiên → Ví dụ: `QHUN38291`
- Unique trong DB, dùng để khách tra cứu đơn hàng
- Tạo bằng `'QHUN' + str(random.randint(10000, 99999))`

**Liên kết VNPay:**

- `vnpay_order_code` lưu `order_code` từ `VNPayPayment` (format `QHun-YYYYMMDDHHMMSS-XXXXXXXX`)
- Dùng để trace ngược từ Order → VNPayPayment khi cần kiểm tra giao dịch

---

### 4.4 Utility – VNPayUtil

**File:** `store/vnpay_utils.py`

Class `VNPayUtil` chứa toàn bộ logic xử lý VNPay, gồm 6 static methods:

#### `get_config()`

- Trả về dictionary `VNPAY_CONFIG` từ `settings.py`

#### `generate_order_code()`

- Tạo mã đơn hàng unique format `QHun-YYYYMMDDHHMMSS-XXXXXXXX`
- Sử dụng `timezone.now()` (múi giờ Việt Nam) + `uuid4`

#### `calculate_checksum(data, secret_key)`

- **Thuật toán:** HMAC-SHA512
- **Quy trình:**
  1. Sắp xếp tất cả tham số theo key (alphabetical order)
  2. Tạo hash data string: `key1=quote_plus(value1)&key2=quote_plus(value2)&...`
  3. Tính HMAC-SHA512 với secret key
  4. Trả về hex string
- **⚠️ QUAN TRỌNG:** Dùng `urllib.parse.quote_plus()` cho từng value riêng lẻ, **KHÔNG** dùng `urllib.parse.urlencode()` cho cả dict (có thể gây sai checksum)

```python
# ĐÚng (VNPay standard):
sorted_keys = sorted(data.keys())
hash_data = '&'.join(f"{k}={urllib.parse.quote_plus(str(data[k]))}" for k in sorted_keys)
signature = hmac.new(secret_key.encode(), hash_data.encode(), hashlib.sha512).hexdigest()
```

#### `build_payment_url(amount, order_code, order_description, ip_address, return_url)`

- Xây dựng URL thanh toán đầy đủ để redirect user sang VNPay
- **Lưu ý quan trọng:** `vnp_Amount` phải nhân 100 (VNPay tính bằng xu, không phải VND)
  - Ví dụ: 35.990.000 VND → gửi `3599000000`
- **⚠️ CHỈ gửi các tham số chuẩn VNPay v2.1.0** (không gửi `vnp_NotifyUrl` hay tham số tự đặt)
- Tham số được gửi lên VNPay:

| Param | Giá trị | Mô tả |
|-------|---------|--------|
| `vnp_Version` | `2.1.0` | Phiên bản API |
| `vnp_Command` | `pay` | Loại command |
| `vnp_TmnCode` | `981P6A3M` | Mã website |
| `vnp_Amount` | `amount * 100` | Số tiền (xu) |
| `vnp_CreateDate` | `YYYYMMDDHHmmss` | Thời gian tạo |
| `vnp_CurrCode` | `VND` | Đơn vị tiền tệ |
| `vnp_IpAddr` | IP khách | Địa chỉ IP |
| `vnp_Locale` | `vn` | Ngôn ngữ |
| `vnp_OrderInfo` | Mô tả | Nội dung thanh toán (CHỈ ASCII) |
| `vnp_OrderType` | `billpayment` | Loại đơn hàng |
| `vnp_ReturnUrl` | URL return | URL VNPay redirect về (SẠCH, không query params) |
| `vnp_TxnRef` | `order_code` | Mã đơn hàng |

> `vnp_SecureHash` được append riêng vào cuối URL, không nằm trong data tính checksum.

#### `verify_payment_response(response_data, secret_key)`

- Xác minh response từ VNPay khi redirect về hoặc gọi IPN
- **Quy trình:**
  1. Lấy `vnp_SecureHash` từ response
  2. Loại bỏ `vnp_SecureHash` và `vnp_SecureHashType` khỏi data
  3. Tính lại checksum từ data còn lại
  4. So sánh checksum tính được với `vnp_SecureHash` → nếu khác → FAKE response
  5. Kiểm tra `vnp_ResponseCode`:
     - `'00'` → Thành công → return `(True, "OK")`
     - Khác → Thất bại → return `(False, message)`

#### `get_response_message(response_code)`

- Chuyển mã lỗi VNPay thành message tiếng Việt dễ đọc

---

### 4.5 Views – Xử lý thanh toán

**File:** `store/views.py`

Thêm 4 views mới ở cuối file (sau phần QR Payment):

---

#### View 1: `vnpay_create` — Tạo yêu cầu thanh toán

```
POST /vnpay/create/
```

**Decorators:** `@login_required`, `@require_POST`, `@csrf_exempt`

**Input (POST body – FormData):**

| Param | Type | Mô tả |
|-------|------|--------|
| `amount` | float | Số tiền cần thanh toán (VND) |
| `order_description` | string | Mô tả đơn hàng |
| `items_param` | string | Danh sách item IDs (ví dụ: `1,2,3`) |

**Xử lý:**

1. Validate `amount > 0`
2. Gọi `VNPayUtil.generate_order_code()` tạo mã đơn hàng unique
3. Lấy IP address từ `HTTP_X_FORWARDED_FOR` hoặc `REMOTE_ADDR`
4. Tạo bản ghi `VNPayPayment` trong DB (status = `pending`)
5. **Lưu `items_param` vào Django session** (`request.session['vnpay_items_param']`) — KHÔNG đưa vào URL
6. Build `return_url` **sạch** (chỉ `/vnpay/return/`, không kèm query params)
7. Gọi `VNPayUtil.build_payment_url()` với `order_description` **chỉ ASCII** (không dùng ký tự unicode)
8. Trả JSON `{ success: true, payment_url: "https://sandbox.vnpayment.vn/...", order_code: "QHun-..." }`

> **⚠️ Lưu ý:** Return URL phải sạch (không query params) vì VNPay sẽ append `?vnp_...` params vào. Nếu URL đã có `?xxx=yyy` thì VNPay append thêm `?vnp_...` → URL bị malformed, gây lỗi.

**Output (JSON):**

```json
{
    "success": true,
    "payment_url": "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?vnp_Amount=3599000000&...",
    "order_code": "QHun-20260226143052-A1B2C3D4"
}
```

---

#### View 2: `vnpay_return` — Xử lý redirect từ VNPay

```
GET /vnpay/return/?vnp_TxnRef=...&vnp_ResponseCode=...&vnp_SecureHash=...
```

**Decorator:** `@login_required`

**Xử lý:**

1. Lấy toàn bộ GET params, **lọc chỉ các param có prefix `vnp_`** (loại bỏ params rác)
2. Lấy `items_param` từ session (`request.session.get('vnpay_items_param')`)
3. Tìm `VNPayPayment` theo `vnp_TxnRef` (= `order_code`)
4. Gọi `VNPayUtil.verify_payment_response()` để xác minh checksum và response code
5. Cập nhật bản ghi `VNPayPayment`:
   - Thành công (`'00'`): status = `paid`, lưu `paid_at`
   - Thất bại: status = `failed`, lưu `response_message`
6. **Nếu thành công:**
   - Tạo `Order` mới với `order_code` = `'QHUN' + 5 số ngẫu nhiên`, `payment_method = 'vnpay'`
   - Liên kết Order với VNPayPayment qua `vnpay_order_code`
   - Xóa Cart items đã thanh toán khỏi giỏ hàng
   - Xóa session data (`vnpay_items_param`)
   - **Redirect → `/order/success/<order_code>/`** (trang chúc mừng)
7. **Nếu thất bại:**
   - Redirect về `/checkout/?items=1,2,3` kèm Django message lỗi

**Flow redirect (thành công):**

```
VNPay sandbox → GET /vnpay/return/?vnp_TxnRef=QHun-xxx&vnp_ResponseCode=00&...
    → Django: lọc vnp_ params → verify checksum
    → Update VNPayPayment (status=paid)
    → Create Order (order_code=QHUN38291, payment_method=vnpay)
    → Delete cart items
    → Redirect → /order/success/QHUN38291/
```

---

#### View 3: `vnpay_ipn` — Xử lý IPN callback từ VNPay

```
POST /vnpay/ipn/
```

**Decorators:** `@csrf_exempt`, `@require_http_methods(["POST"])`

> **IPN (Instant Payment Notification):** VNPay server gọi trực tiếp đến server của ta (server-to-server) để xác nhận thanh toán. Đây là kênh xác nhận đáng tin cậy hơn Return URL (vì user có thể đóng browser trước khi redirect về).

**Xử lý:**

1. Lấy toàn bộ POST params
2. Verify checksum
3. Cập nhật `VNPayPayment`
4. Trả JSON response cho VNPay:
   - `{'RspCode': '00', 'Message': 'Confirmed'}` → VNPay biết ta đã nhận
   - `{'RspCode': '01', 'Message': '...'}` → Lỗi order
   - `{'RspCode': '02', 'Message': '...'}` → Checksum sai

**Lưu ý:**

- View này **KHÔNG** có `@login_required` vì VNPay server gọi, không phải user
- Cần `@csrf_exempt` vì VNPay không gửi CSRF token
- Trong sandbox, VNPay có thể không gọi IPN nếu URL không public (localhost). IPN chỉ hoạt động khi deploy lên server thật

---

#### View 4: `order_success` — Trang chúc mừng đặt hàng thành công

```
GET /order/success/<order_code>/
```

**Decorator:** `@login_required`

**Xử lý:**

1. Nhận `order_code` từ URL (ví dụ: `QHUN38291`)
2. Tìm `Order` theo `order_code` + `user` hiện tại (chỉ xem được đơn hàng của mình)
3. Render template `order_success.html` với context: `order`, `order_code`, `total_amount`, `payment_method`, `status`, `created_at`

**Giao diện:**

- Animated checkmark icon (SVG animation)
- Hiển thị mã đơn hàng `QHUN38291` (click để copy)
- Bảng thông tin: tổng tiền, phương thức, trạng thái, ngày đặt
- Confetti animation khi load trang
- Nút "Tra cứu đơn hàng" và "Về trang chủ"

---

### 4.6 URLs – Định tuyến

#### File: `config/urls.py` (Root URLs)

```python
from store import views as store_views

urlpatterns = [
    # ...
    path('vnpay/return/', store_views.vnpay_return, name='vnpay_return'),
    path('vnpay/ipn/', store_views.vnpay_ipn, name='vnpay_ipn'),
    path('', include('store.urls')),
]
```

- `/vnpay/return/` và `/vnpay/ipn/` được đặt ở root `config/urls.py` (không nằm trong `store/urls.py`) vì:
  - VNPay redirect về URL cố định, cần match chính xác
  - Tránh prefix `/store/` không cần thiết
  - IPN URL cần public, không nên nằm trong app namespace

#### File: `store/urls.py` (App URLs)

```python
path('vnpay/create/', views.vnpay_create, name='vnpay_create'),
path('order/success/<str:order_code>/', views.order_success, name='order_success'),
```

- API tạo thanh toán: `store:vnpay_create`
- Trang thành công: `store:order_success` (nhận `order_code` từ URL)
- Frontend gọi qua `{% url "store:vnpay_create" %}`

**Tổng hợp URL:**

| URL | Method | View | Mô tả |
|-----|--------|------|--------|
| `/vnpay/create/` | POST | `vnpay_create` | Frontend gọi để tạo payment URL |
| `/vnpay/return/` | GET | `vnpay_return` | VNPay redirect user về đây |
| `/vnpay/ipn/` | POST | `vnpay_ipn` | VNPay server gọi xác nhận |
| `/order/success/<code>/` | GET | `order_success` | Trang chúc mừng đặt hàng thành công |

---

### 4.7 Template – Giao diện checkout

**File:** `templates/store/checkout.html`

#### Thay đổi 1: Bỏ badge "Bảo trì" cho VNPay

**Trước:**

```html
<div class="qh-checkout-pay-opt disabled" data-pay-type="vnpay">
    ...
    <span class="qh-checkout-pay-badge">Bảo trì</span>
</div>
```

**Sau:**

```html
<div class="qh-checkout-pay-opt" data-pay-type="vnpay">
    ...
    <span class="qh-checkout-pay-check"><i class="ri-checkbox-circle-fill"></i></span>
</div>
```

- Bỏ class `disabled` → user có thể click chọn
- Thay badge "Bảo trì" bằng checkbox icon (giống COD, VIETQR)

#### Thay đổi 2: Thêm biến JavaScript

```html
<script>
    var QH_VNPAY_CREATE_URL = '{% url "store:vnpay_create" %}';
    var QH_CHECKOUT_ITEMS_PARAM = '{{ items_param }}';
</script>
```

- `QH_VNPAY_CREATE_URL`: URL endpoint tạo thanh toán VNPay
- `QH_CHECKOUT_ITEMS_PARAM`: Danh sách item IDs để truyền qua VNPay return URL

---

### 4.8 JavaScript – Xử lý phía client

**File:** `static/js/checkout.js`

#### Thay đổi 1: Xử lý khi chọn VNPAY trong Payment Selection

```javascript
// VNPAY → hide QR, restore total
else if (payType === 'vnpay') {
    hideQrBox();
    if (summaryTotalEl) {
        summaryTotalEl.textContent = formatPrice(totalAmount);
    }
}
```

- Khi user click chọn VNPAY → ẩn QR box (nếu đang hiện) và khôi phục tổng tiền

#### Thay đổi 2: Hàm `initiateVNPayPayment()`

```javascript
function initiateVNPayPayment() {
    // 1. Disable nút "ĐẶT HÀNG", đổi text
    submitBtn.disabled = true;
    submitBtn.textContent = 'Đang chuyển hướng đến VNPay...';

    // 2. Tạo FormData gửi lên server
    var formData = new FormData();
    formData.append('amount', totalAmount);
    formData.append('order_description', '...');
    formData.append('items_param', QH_CHECKOUT_ITEMS_PARAM);

    // 3. POST tới /vnpay/create/
    fetch(QH_VNPAY_CREATE_URL, {
        method: 'POST',
        headers: { 'X-CSRFToken': QH_CSRF_TOKEN },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success && data.payment_url) {
            // 4. Redirect sang VNPay sandbox
            window.location.href = data.payment_url;
        } else {
            // Hiển thị lỗi, enable lại nút
        }
    })
    .catch(err => {
        // Lỗi mạng, enable lại nút
    });
}
```

#### Thay đổi 3: Xử lý nút "ĐẶT HÀNG"

```javascript
// VNPAY → chuyển hướng sang cổng thanh toán VNPay
if (payType === 'vnpay') {
    initiateVNPayPayment();
    return;
}
```

- Khi user chọn VNPay rồi click "ĐẶT HÀNG" → gọi `initiateVNPayPayment()` thay vì hiện toast "đang phát triển"

---

### 4.9 Admin – Quản lý trong Django Admin

**File:** `store/admin.py`

```python
@admin.register(VNPayPayment)
class VNPayPaymentAdmin(admin.ModelAdmin):
    list_display = ['order_code', 'user', 'amount', 'status', 'transaction_no', 'created_at', 'paid_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_code', 'transaction_no', 'user__email']
    readonly_fields = ['order_code', 'transaction_no', 'response_code', 'response_message',
                       'created_at', 'updated_at', 'paid_at']
```

- Truy cập `/admin/store/vnpaypayment/` để xem danh sách giao dịch VNPay
- Lọc theo `status`, `created_at`
- Tìm kiếm theo `order_code`, `transaction_no`, `user email`
- Các field từ VNPay trả về là readonly (không cho sửa)

---

### 4.10 Migration – Database

**File:** `store/migrations/0024_vnpay_payment.py`

- Migration tự động tạo bảng `store_vnpaypayment` trong SQLite
- Đã chạy `makemigrations` + `migrate` thành công
- Phụ thuộc migration `0023_pending_qr_payment`

**File:** `store/migrations/0025_order_code_payment_method.py`

- Thêm 3 field mới cho `Order`: `order_code`, `payment_method`, `vnpay_order_code`
- `order_code` có `unique=True`

---

### 4.11 Template – Trang đặt hàng thành công

**File:** `templates/store/order_success.html`

Template hiển thị khi đơn hàng VNPay thành công. Gồm:

#### Giao diện chính

- **Animated checkmark:** SVG animation (vòng tròn + dấu tick) hiển thị ngay khi load
- **Tiêu đề:** "Đặt hàng thành công!"
- **Mã đơn hàng:** Hiển thị lớn, in đậm (ví dụ: `QHUN38291`), click để copy vào clipboard
- **Bảng thông tin:**
  - Mã đơn hàng
  - Tổng tiền (format VND)  
  - Phương thức thanh toán
  - Trạng thái
  - Ngày đặt hàng
- **Nút action:**
  - "Tra cứu đơn hàng" → link đến trang order tracking
  - "Về trang chủ" → link đến homepage

#### Hiệu ứng

- **Confetti animation:** 50 hạt confetti đa màu sắc rơi từ trên xuống khi load trang (CSS keyframes)
- **Copy to clipboard:** Click vào mã đơn hàng → copy + hiển thị tooltip "Đã sao chép!"
- **Responsive design:** Hiện tốt trên mobile và desktop

#### Styling

- Kế thừa biến CSS từ `base.html` (`var(--qh-card-bg)`, etc.)
- Font: Signika (Google Fonts)
- Icons: RemixIcon (CDN)

---

## 5. Luồng thanh toán (Payment Flow)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CHECKOUT PAGE                                │
│                                                                     │
│  1. User chọn sản phẩm → vào trang checkout                       │
│  2. User chọn phương thức thanh toán: [COD] [VIETQR] [VNPAY]      │
│  3. User chọn VNPAY → click nút "ĐẶT HÀNG"                       │
│                                                                     │
│  ┌─── JavaScript (checkout.js) ───┐                                │
│  │ initiateVNPayPayment()          │                                │
│  │ → Disable nút "ĐẶT HÀNG"      │                                │
│  │ → POST /vnpay/create/          │                                │
│  └─────────────┬──────────────────┘                                │
└────────────────┼────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DJANGO SERVER                                   │
│                                                                     │
│  vnpay_create (views.py):                                          │
│  → Tạo order_code: QHun-20260226143052-A1B2C3D4                   │
│  → Lưu VNPayPayment (status=pending) vào DB                       │
│  → Build VNPay URL với checksum HMAC-SHA512                        │
│  → Trả JSON { payment_url: "https://sandbox.vnpayment.vn/..." }   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 BROWSER REDIRECT                                    │
│                                                                     │
│  window.location.href = payment_url                                │
│  → Browser chuyển sang trang VNPay sandbox                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│               VNPAY SANDBOX PAYMENT PAGE                            │
│                                                                     │
│  → User chọn ngân hàng / thẻ                                      │
│  → User nhập thông tin thanh toán                                  │
│  → User xác nhận OTP                                               │
│  → Thanh toán thành công / thất bại / hủy                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
   (Redirect)        (Server-to-Server)
        │                 │
        ▼                 ▼
┌───────────────┐ ┌───────────────────┐
│ vnpay_return  │ │    vnpay_ipn      │
│ (GET)         │ │    (POST)         │
│               │ │                   │
│ → Verify hash │ │ → Verify hash     │
│ → Update DB   │ │ → Update DB       │
│ → Create Order│ │ → Return JSON     │
│ → Redirect    │ │   {RspCode: '00'} │
│   success page│ │                   │
│               │ │ VNPay server      │
│ User thấy     │ │ xác nhận          │
│ kết quả       │ │                   │
└───────────────┘ └───────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                TRANG ĐẶT HÀNG THÀNH CÔNG                           │
│                                                                     │
│  URL: /order/success/QHUN38291/                                    │
│                                                                     │
│  Thành công:                                                        │
│  → Hiển thị animated checkmark                                     │
│  → Mã đơn hàng: QHUN38291 (click to copy)                         │
│  → Thông tin: tổng tiền, phương thức, trạng thái, ngày đặt        │
│  → Confetti animation                                               │
│  → Nút: "Tra cứu đơn hàng" / "Về trang chủ"                      │
│                                                                     │
│  Thất bại:                                                          │
│  → Redirect về /checkout/?items=1,2,3                              │
│  → Django messages: "Thanh toán VNPay thất bại: [lý do]"          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Chi tiết kỹ thuật: Checksum & Bảo mật

### Tại sao cần checksum?

VNPay sử dụng **HMAC-SHA512** để đảm bảo:

1. **Tính toàn vẹn (Integrity):** Dữ liệu không bị thay đổi giữa đường
2. **Xác thực (Authentication):** Chỉ ai có `vnp_HashSecret` mới tạo được checksum hợp lệ
3. **Chống giả mạo (Anti-tampering):** Attacker không thể sửa `amount` rồi gọi return URL

### Quy trình tạo checksum (Gửi đi)

```
1. Chuẩn bị params: {vnp_Amount: 3599000000, vnp_TmnCode: '981P6A3M', ...}
2. Sort theo key: vnp_Amount, vnp_Command, vnp_CreateDate, ...
3. URL encode: vnp_Amount=3599000000&vnp_Command=pay&vnp_CreateDate=20260226143052&...
4. HMAC-SHA512(query_string, secret_key) → hex string
5. Append vnp_SecureHash vào URL
```

### Quy trình verify checksum (Nhận về)

```
1. Lấy vnp_SecureHash từ response
2. Bỏ vnp_SecureHash và vnp_SecureHashType khỏi response
3. Sort + URL encode phần còn lại
4. HMAC-SHA512(query_string, secret_key) → expected_hash
5. So sánh expected_hash == vnp_SecureHash
   → Giống → Dữ liệu hợp lệ
   → Khác → Dữ liệu bị giả mạo, reject!
```

### Lưu ý bảo mật

- **KHÔNG BAO GIỜ** lưu `vnp_HashSecret` trong source code khi deploy production → dùng biến môi trường
- Return URL và IPN URL nên dùng **HTTPS** khi production
- IPN endpoint cần `@csrf_exempt` nhưng verify bằng checksum thay thế
- Luôn verify checksum **TRƯỚC** khi xử lý kết quả

---

## 7. Mã lỗi VNPay (Response Codes)

| Code | Ý nghĩa |
|------|----------|
| `00` | Giao dịch thành công |
| `01` | Giao dịch bị từ chối (thẻ/tài khoản) |
| `02` | Không liên lạc được máy chủ ngân hàng |
| `03` | Merchant không hợp lệ |
| `04` | Đơn vị tiền tệ không hỗ trợ |
| `05` | Chấp nhận nhưng thiếu thông tin thanh toán |
| `06` | Lỗi trong quá trình xử lý |
| `07` | Merchant không được phép giao dịch này |
| `08` | Interchange không hỗ trợ |
| `09` | Đặc tính giao dịch không hỗ trợ |
| `10` | Ngân hàng không hỗ trợ giao dịch |
| `11` | Thẻ hết hạn hoặc bị khóa |
| `12` | Thẻ chưa đăng ký |
| `13` | Phương thức không hợp lệ |
| `14` | Tài khoản không hỗ trợ hoặc bị khóa |
| `15` | Ngân hàng từ chối |
| `20` | Người phát hành thẻ từ chối |
| `99` | **Người dùng hủy giao dịch** |

---

## 8. Chuyển sang môi trường Production

Khi cần chuyển từ sandbox sang production, thực hiện:

### Bước 1: Cập nhật biến môi trường (`.env`)

```env
VNPAY_TMN_CODE=<Mã TmnCode production>
VNPAY_HASH_SECRET=<Secret key production>
VNPAY_URL=https://pay.vnpay.vn/vpcpay.html
VNPAY_RETURN_URL=https://yourdomain.com/vnpay/return/
VNPAY_IPN_URL=https://yourdomain.com/vnpay/ipn/
```

### Bước 2: Đảm bảo HTTPS

- Return URL và IPN URL **phải** dùng `https://`
- Cấu hình SSL certificate cho domain

### Bước 3: Đăng ký IPN URL với VNPay

- Liên hệ VNPay để đăng ký IPN URL production
- VNPay sẽ test IPN endpoint trước khi bật live

### Bước 4: Test end-to-end

- Test với số tiền nhỏ
- Verify checksum hoạt động đúng
- Kiểm tra IPN callback nhận được

---

## 9. Troubleshooting

### Lỗi: "Có lỗi xảy ra trong quá trình xử lý" (VNPay sandbox)

> Đây là lỗi thực tế đã gặp và sửa trong dự án này.

**Nguyên nhân (4 lỗi cùng lúc):**

1. **`vnp_NotifyUrl` không hợp lệ:** Gửi tham số `vnp_NotifyUrl` (IPN URL) trong request — đây KHÔNG phải tham số chuẩn VNPay v2.1.0, gây lỗi phía VNPay
2. **Return URL chứa query params:** URL có dạng `/vnpay/return/?order_code=xxx&items_param=yyy` → VNPay append thêm `?vnp_...` → URL bị malformed (2 dấu `?`)
3. **Checksum sai format:** Dùng `urllib.parse.urlencode()` cho cả dict → encoding khác với VNPay standard (`quote_plus` per value)
4. **Unicode trong `order_description`:** `formatPrice()` JS trả về `35.990.000đ` (chứa ký tự `đ` unicode) → gây lỗi checksum

**Giải pháp:**

1. Xóa `vnp_NotifyUrl` khỏi params (IPN URL đăng ký qua VNPay portal, không gửi trong request)
2. Return URL sạch (`/vnpay/return/`), lưu `items_param` vào Django session
3. Tính checksum bằng `quote_plus()` cho từng value riêng lẻ
4. `order_description` chỉ dùng ASCII: `'Thanh toan QHUN22 - 35990000 VND'`

### Lỗi: "Checksum không hợp lệ" khi VNPay trả về

**Nguyên nhân:**

- Secret key không đúng
- Custom params (không có prefix `vnp_`) bị tính vào checksum khi verify

**Giải pháp:**

- Kiểm tra `vnp_HashSecret` trong settings
- Khi verify, **chỉ lấy params có prefix `vnp_`** để tính checksum (loại bỏ params rác)
- Log `expected_hash` và `vnp_SecureHash` để debug

### Lỗi: VNPay không gọi IPN

**Nguyên nhân:**

- IPN URL là `localhost` → VNPay server không truy cập được

**Giải pháp:**

- Dùng ngrok/cloudflare tunnel để expose localhost khi dev
- Hoặc bỏ qua IPN khi dev, chỉ dựa vào Return URL

### Lỗi: "Số tiền không hợp lệ"

**Nguyên nhân:**

- Không nhân 100 (VNPay yêu cầu đơn vị xu)

**Giải pháp:**

- Kiểm tra `vnp_Amount = int(amount * 100)` trong `build_payment_url()`

### Lỗi: Nút "ĐẶT HÀNG" bị disable mãi

**Nguyên nhân:**

- Fetch request thất bại nhưng không catch được

**Giải pháp:**

- Đã xử lý trong `.catch()` → enable lại nút và hiện toast lỗi

---

## 10. Lịch sử cập nhật (Changelog)

### v1.1 – Sửa lỗi VNPay sandbox + Trang đặt hàng thành công

**Lỗi gặp phải:** VNPay sandbox trả về "Có lỗi xảy ra trong quá trình xử lý"

**Các thay đổi:**

#### Bugfixes

1. **Xóa `vnp_NotifyUrl`** khỏi `build_payment_url()` — không phải tham số chuẩn VNPay v2.1.0
2. **Return URL sạch** — không kèm query params, lưu `items_param` vào Django session
3. **Checksum format chuẩn** — dùng `quote_plus()` per value thay vì `urlencode()` cho dict
4. **ASCII-only `order_description`** — loại bỏ ký tự unicode `đ` từ `formatPrice()`
5. **Lọc `vnp_` params khi verify** — chỉ tính checksum trên params có prefix `vnp_`

#### Features mới

1. **Model `Order` cập nhật** — thêm `order_code` (QHUN + 5 số), `payment_method`, `vnpay_order_code`
2. **Trang đặt hàng thành công** — `/order/success/<order_code>/` với animated checkmark, confetti, copy order code
3. **Tạo Order tự động** — `vnpay_return` tạo Order khi thanh toán thành công, xóa cart items
4. **View `order_success`** — hiển thị thông tin đơn hàng + mã tra cứu
5. **Migration `0025_order_code_payment_method.py`** — thêm fields mới cho Order

#### Files thay đổi

- `store/vnpay_utils.py` — sửa checksum, xóa `vnp_NotifyUrl`
- `store/views.py` — sửa `vnpay_create`, viết lại `vnpay_return`, thêm `order_success`
- `store/models.py` — thêm 3 fields cho Order
- `store/urls.py` — thêm route `order/success/`
- `static/js/checkout.js` — sửa `order_description` ASCII-only
- `templates/store/order_success.html` — template mới
- `store/migrations/0025_order_code_payment_method.py` — migration mới
