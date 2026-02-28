# TÀI LIỆU CHATBOT QHUN22

## 📋 TỔNG QUAN

Chatbot QHUN22 là hệ thống trợ lý AI được tích hợp vào website, sử dụng Claude API (claude-3-haiku) để tư vấn khách hàng về sản phẩm điện thoại.

---

## 🗂️ CẤU TRÚC FILE

### Backend
- **`store/chatbot_service.py`** - Logic xử lý chatbot chính
- **`store/claude_service.py`** - Service gọi Claude API
- **`store/views.py`** (line 4919-4950) - API endpoint `/api/chatbot/`

### Frontend
- **`static/js/chatbot.js`** - JavaScript xử lý UI chatbot
- **`static/css/chatbot.css`** - CSS styling cho chatbot widget
- **`templates/base.html`** - HTML template chứa chatbot widget

---

## 🔧 CẤU HÌNH

### Claude API
- **Model**: `claude-3-haiku-20240307`
- **API URL**: `https://api.anthropic.com/v1/messages`
- **API Key**: Lấy từ biến môi trường `ANTHROPIC_API_KEY`
- **Timeout**: 15 giây
- **Default Max Tokens**: 400

### Token Limits
- **NORMAL_MAX_TOKENS**: 250 (cho câu hỏi thông thường)
- **COMPARE_MAX_TOKENS**: 350 (cho so sánh sản phẩm) ⚠️ **CẦN TĂNG LÊN 600**

---

## 🎯 INTENT DETECTION

Chatbot sử dụng regex patterns để phát hiện intent của người dùng:

### 1. **ORDER** - Kiểm tra đơn hàng
- Pattern: `ORDER_PATTERNS` + `ORDER_CODE_PATTERN`
- Code pattern hiện tại: `\b(QH\d{6,})\b` ⚠️ **CHỈ NHẬN QH + 6+ SỐ**
- Cần sửa thành: `\b(QH\d{6,}|QHUN\d+)\b` để nhận cả QHUN format

### 2. **COMPARE** - So sánh sản phẩm
- Pattern: `COMPARE_PATTERNS`
- Keywords: "so sánh", "vs", "versus", "hay hơn", "khác gì", etc.

### 3. **CONSULT** - Tư vấn chọn máy
- Pattern: `CONSULT_PATTERNS`
- Keywords: "tư vấn", "gợi ý", "nên mua máy nào", "trong tầm giá", etc.

### 4. **PRICE** - Hỏi giá
- Pattern: `PRICE_PATTERNS`
- Keywords: "giá", "bao nhiêu tiền", "giá bn", etc.

### 5. **STOCK** - Kiểm tra tồn kho
- Pattern: `STOCK_PATTERNS`
- Keywords: "còn hàng không", "hết hàng chưa", "có sẵn không", etc.

### 6. **SPEC** - Thông số kỹ thuật
- Pattern: `SPEC_PATTERNS`
- Keywords: "pin", "camera", "chip", "màn hình", "ram", "rom", etc.

### 7. **VARIANT** - Phiên bản/màu sắc
- Pattern: `VARIANT_PATTERNS`
- Keywords: "màu gì", "dung lượng nào", "phiên bản nào", etc.

### 8. **LIST_PRODUCTS** - Liệt kê sản phẩm
- Pattern: `LIST_PRODUCT_PATTERNS`
- Keywords: "mẫu nào", "bán gì", "có những gì", etc.

### 9. **GREETING** - Chào hỏi
- Pattern: `GREETING_PATTERNS`
- Keywords: "xin chào", "chào shop", "hello", "help", etc.

### 10. **STAFF** - Gặp nhân viên
- Pattern: `STAFF_PATTERNS`
- Keywords: "gặp nhân viên", "người thật", "chuyển nhân viên", etc.

### 11. **INSTALLMENT** - Trả góp
- Pattern: `INSTALLMENT_PATTERNS`
- Keywords: "trả góp", "trả góp 0%", "mua trả góp", etc.

### 12. **WARRANTY** - Bảo hành
- Pattern: `WARRANTY_PATTERNS`
- Keywords: "bảo hành", "warranty", "đổi trả", etc.

---

## 📝 PROMPTS

### SYSTEM_PROMPT
```
Bạn là trợ lý bán hàng của QHUN22 – cửa hàng điện thoại chính hãng.

NGUYÊN TẮC BẮT BUỘC:
1. Chỉ được sử dụng dữ liệu được cung cấp trong phần "DỮ LIỆU HỆ THỐNG".
2. Tuyệt đối không bịa thông tin. Không sử dụng kiến thức bên ngoài.
3. Nếu dữ liệu không có thông tin để trả lời, hãy nói: "Mình chưa có thông tin này, anh/chị liên hệ hotline để được hỗ trợ nhé!"
4. Không nhắc đến việc bạn là AI. Không giải thích cách bạn hoạt động.
5. Không lặp lại câu hỏi của khách.
6. Xưng "mình", gọi khách là "anh/chị".
7. Trả lời bằng tiếng Việt.
8. Không sử dụng emoji hay icon.
9. Không bịa ra sản phẩm không có trong dữ liệu. Chỉ nhắc đến sản phẩm đã được cung cấp.
```

### NORMAL_USER_TEMPLATE
```
DỮ LIỆU HỆ THỐNG:
{context}

CÂU HỎI KHÁCH:
"{message}"

YÊU CẦU:
- Trả lời ngắn gọn tối đa.
- Không quá 6 dòng.
- Không quá 120 từ.
- Chỉ nêu thông tin quan trọng nhất.
- Tập trung giúp khách ra quyết định mua.
- Không trình bày dạng bảng.
- Không dùng emoji hay icon.
```

### COMPARE_SYSTEM_EXTRA
```
KHI SO SÁNH SẢN PHẨM:
1. Chỉ so sánh dựa trên dữ liệu được cung cấp.
2. Không sử dụng bảng Markdown.
3. Trình bày dạng bullet point rõ ràng.
4. So sánh tối đa 5 tiêu chí quan trọng nhất: Màn hình, Chip/Hiệu năng, Pin, Camera, Giá.
5. Chỉ nêu điểm khác biệt chính, không lặp lại điểm giống nhau.
6. Không quá 12 dòng. ⚠️ **CẦN TĂNG LÊN 20-25 DÒNG ĐỂ TRẢ LỜI ĐẦY ĐỦ**
7. Kết thúc bằng 1 câu gợi ý nên chọn máy nào theo nhu cầu.
8. Không viết dài dòng.
9. Không dùng emoji hay icon.
```

### COMPARE_USER_TEMPLATE
```
DỮ LIỆU SẢN PHẨM ĐỂ SO SÁNH:
{combined_context}

YÊU CẦU:
"{message}"

Hãy so sánh theo đúng quy tắc.
```

---

## 🔄 FLOW XỬ LÝ

### 1. Người dùng gửi tin nhắn
- Frontend: `chatbot.js` → `callAPI()`
- POST đến `/api/chatbot/` với `{message: "..."}`

### 2. API Endpoint (`views.py`)
- Validate message (max 500 ký tự)
- Gọi `ChatbotService.process_message()`
- Trả về JSON: `{message: "...", suggestions: [...]}`

### 3. ChatbotService (`chatbot_service.py`)
- **Bước 1**: Detect intent bằng regex patterns
- **Bước 2**: Xử lý theo intent:
  - **Fixed responses**: Không gọi Claude (greeting, staff, warranty, etc.)
  - **Product queries**: Detect product names → Build context → Gọi Claude
  - **Compare**: Detect 2+ products → Build combined context → Gọi Claude với COMPARE_MAX_TOKENS

### 4. Claude API (`claude_service.py`)
- Gửi request với system prompt + user message
- Nhận response text
- Trả về cho ChatbotService

### 5. Frontend hiển thị
- `addBotMessage()` hiển thị response
- Format markdown (bold, line breaks)
- Hiển thị suggestions buttons

---

## 🐛 CÁC VẤN ĐỀ ĐÃ PHÁT HIỆN

### 1. ⚠️ Mã đơn hàng không nhận diện được QHUN format
**Vấn đề**: Pattern hiện tại `\b(QH\d{6,})\b` chỉ nhận QH + 6+ số
- ✅ Nhận: `QH250101`, `QH123456`
- ❌ Không nhận: `QHUN38453`, `QHUN123`

**Giải pháp**: Sửa pattern thành `\b(QH\d{6,}|QHUN\d+)\b`

### 2. ⚠️ So sánh bị cắt do giới hạn tokens
**Vấn đề**: `COMPARE_MAX_TOKENS = 350` quá thấp, response bị cắt giữa chừng
- Ví dụ: "iPhone 17 Pro Max có pin dung lượng lớ..." (bị cắt)

**Giải pháp**: 
- Tăng `COMPARE_MAX_TOKENS` lên `600`
- Cập nhật prompt: "Không quá 20-25 dòng" thay vì "Không quá 12 dòng"

### 3. ⚠️ Bot trả lời cứng nhắc khi không tìm thấy mã đơn
**Vấn đề**: Khi không match pattern, bot luôn trả: "Anh/chị cho mình mã đơn hàng (VD: QH250101)..."
- Không nhận diện được mã QHUN format
- Không thông minh trong việc extract mã từ câu hỏi tự nhiên

**Giải pháp**: 
- Sửa pattern để nhận cả QHUN
- Cải thiện logic extract mã đơn từ message

### 4. ⚠️ Prompt so sánh quá hạn chế
**Vấn đề**: "Không quá 12 dòng" khiến response không đầy đủ
- Thiếu thông tin quan trọng
- Không đủ chi tiết để người dùng quyết định

**Giải pháp**: Tăng lên 20-25 dòng, cho phép so sánh chi tiết hơn

---

## 📊 DỮ LIỆU SẢN PHẨM

### Product Context Structure
```
San pham: {name}
Tinh trang: CON HANG / HET HANG
Mo ta: {description}
Gia: {min_price} den {max_price}
Mau sac: {colors}
Dung luong: {storages}
Gia theo dung luong:
  - {storage}: {price}
Thong so ky thuat:
  - {label}: {value}
Noi dung: {content}
```

### Product Detection
- **Exact match**: Tìm tên sản phẩm trong message
- **Fuzzy match**: Match theo tokens (tối thiểu 2 tokens)
- **Longest match**: Ưu tiên tên dài hơn khi có nhiều match

---

## 🎨 UI/UX

### Chatbot Widget
- **Position**: Fixed bottom-right
- **FAB**: Circular button với gradient (primary → secondary)
- **Window**: 380px width, max-height 540px
- **Z-index**: 
  - FAB: 9998
  - Window: 9999
  - Compare bar: 10001 (đã sửa để đè lên chatbot)

### Responsive
- Mobile: Full screen width, max-height 100dvh

---

## 🔐 SECURITY

### API Endpoint
- CSRF exempt: `@csrf_exempt`
- POST only: `@require_POST`
- Message length limit: 500 ký tự
- Input validation: Strip whitespace, check empty

### Error Handling
- Try-catch trong `chatbot_api()`
- Logging errors với `logging.getLogger(__name__).exception()`
- Return friendly error message cho user

---

## 📈 SUGGESTIONS

Chatbot trả về suggestions để người dùng click nhanh:
- Menu suggestions: ["Tư vấn chọn máy", "So sánh sản phẩm", "Kiểm tra đơn hàng", "Gặp nhân viên"]
- Product suggestions: Tên sản phẩm liên quan
- Context suggestions: Dựa trên intent và sản phẩm đang hỏi

---

## 🛠️ CÁCH SỬA CÁC VẤN ĐỀ

### 1. Sửa Pattern Mã Đơn Hàng
**File**: `store/chatbot_service.py` (line 185)
```python
# Cũ
ORDER_CODE_PATTERN = re.compile(r"\b(QH\d{6,})\b", re.IGNORECASE)

# Mới
ORDER_CODE_PATTERN = re.compile(r"\b(QH\d{6,}|QHUN\d+)\b", re.IGNORECASE)
```

### 2. Tăng Max Tokens Cho So Sánh
**File**: `store/chatbot_service.py` (line 66)
```python
# Cũ
COMPARE_MAX_TOKENS = 350

# Mới
COMPARE_MAX_TOKENS = 600
```

### 3. Cải Thiện Prompt So Sánh
**File**: `store/chatbot_service.py` (line 45-55)
```python
COMPARE_SYSTEM_EXTRA = """
KHI SO SÁNH SẢN PHẨM:
1. Chỉ so sánh dựa trên dữ liệu được cung cấp.
2. Không sử dụng bảng Markdown.
3. Trình bày dạng bullet point rõ ràng.
4. So sánh các tiêu chí quan trọng: Màn hình, Chip/Hiệu năng, Pin, Camera, Giá, RAM, ROM.
5. Chỉ nêu điểm khác biệt chính, không lặp lại điểm giống nhau.
6. Có thể viết 20-25 dòng để trả lời đầy đủ và chi tiết.
7. Kết thúc bằng 1 câu gợi ý nên chọn máy nào theo nhu cầu.
8. Trả lời đầy đủ, không bỏ sót thông tin quan trọng.
9. Không dùng emoji hay icon."""
```

---

## 📞 LIÊN HỆ & HỖ TRỢ

- **Hotline**: 0123.456.789
- **Facebook**: QHUN22
- **Staff message**: "Anh/chị vui lòng liên hệ hotline 0123.456.789 hoặc fanpage Facebook QHUN22 để được nhân viên hỗ trợ trực tiếp nhé!"

---

## 📝 GHI CHÚ

- Chatbot chỉ sử dụng dữ liệu từ database, không bịa thông tin
- Tất cả responses đều bằng tiếng Việt
- Không sử dụng emoji trong responses
- Xưng "mình", gọi khách "anh/chị"
- Max 500 ký tự cho input message
- Timeout 15 giây cho Claude API calls

---

**Cập nhật lần cuối**: 2024
**Version**: 1.0
