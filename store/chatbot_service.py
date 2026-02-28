import re
import json
import logging
import time
from typing import Any

from django.db.models import Q, Sum

from .models import Product, ProductDetail, ProductSpecification, ProductVariant, ProductContent, Order
from .claude_service import ClaudeService

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
# PROMPTS
# ════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Bạn là trợ lý bán hàng của QHUN22 – cửa hàng điện thoại chính hãng.

NGUYÊN TẮC BẮT BUỘC:
1. Chỉ được sử dụng dữ liệu được cung cấp trong phần "DỮ LIỆU HỆ THỐNG".
2. Tuyệt đối không bịa thông tin. Không sử dụng kiến thức bên ngoài.
3. Nếu dữ liệu không có thông tin để trả lời, hãy nói: "Mình chưa có thông tin này, anh/chị liên hệ hotline để được hỗ trợ nhé!"
4. Không nhắc đến việc bạn là AI. Không giải thích cách bạn hoạt động.
5. Không lặp lại câu hỏi của khách.
6. Xưng "mình", gọi khách là "anh/chị".
7. Trả lời bằng tiếng Việt.
8. Không sử dụng emoji hay icon.
9. Không bịa ra sản phẩm không có trong dữ liệu. Chỉ nhắc đến sản phẩm đã được cung cấp."""

NORMAL_USER_TEMPLATE = """DỮ LIỆU HỆ THỐNG:
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
- Không dùng emoji hay icon."""

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

COMPARE_USER_TEMPLATE = """DỮ LIỆU SẢN PHẨM ĐỂ SO SÁNH:
{combined_context}

YÊU CẦU:
"{message}"

Hãy so sánh theo đúng quy tắc."""

NORMAL_MAX_TOKENS = 250
COMPARE_MAX_TOKENS = 600

# ════════════════════════════════════════════════════════════════
# FIXED MESSAGES
# ════════════════════════════════════════════════════════════════

NOT_FOUND_MSG = "Hiện tại QHUN22 chưa kinh doanh sản phẩm này. Anh/chị có muốn mình tư vấn mẫu khác không?"

MENU_MSG = "Mình có thể hỗ trợ anh/chị những gì nè?"
MENU_SUGGESTIONS = [
    "Tư vấn chọn máy",
    "So sánh sản phẩm",
    "Kiểm tra đơn hàng",
    "Gặp nhân viên",
]

STAFF_MSG = "Anh/chị vui lòng liên hệ hotline 0123.456.789 hoặc fanpage Facebook QHUN22 để được nhân viên hỗ trợ trực tiếp nhé!"

INSTALLMENT_MSG = (
    "QHUN22 hỗ trợ trả góp 0% lãi suất qua thẻ tín dụng và các công ty tài chính.\n"
    "Anh/chị liên hệ hotline 0123.456.789 hoặc đến trực tiếp cửa hàng để được hướng dẫn chi tiết nhé!"
)

WARRANTY_MSG = (
    "Tất cả sản phẩm tại QHUN22 đều là hàng chính hãng, bảo hành 12 tháng tại trung tâm bảo hành ủy quyền.\n"
    "Ngoài ra, QHUN22 hỗ trợ đổi trả trong 7 ngày nếu sản phẩm lỗi từ nhà sản xuất.\n"
    "Anh/chị cần hỗ trợ thêm về bảo hành sản phẩm nào không?"
)

# ════════════════════════════════════════════════════════════════
# INTENT PATTERNS
# ════════════════════════════════════════════════════════════════

GREETING_PATTERNS = re.compile(
    r"(xin chào|chào bạn|chào shop|chào\b|hello\b|^hi\b|^hey\b|alo\b|"
    r"ê shop|shop ơi|ad ơi|admin ơi|"
    r"có ai không|có ai trực không|tư vấn giúp|giúp mình với|"
    r"^help\b|^support\b|mình cần hỗ trợ|cho mình hỏi|hỏi chút)",
    re.IGNORECASE,
)

LIST_PRODUCT_PATTERNS = re.compile(
    r"(mẫu nào|những mẫu|có những gì|bán gì|sản phẩm nào|có gì|"
    r"danh sách máy|các máy đang bán|các mẫu iphone|các dòng iphone|"
    r"shop có bán|hiện có những|hiện đang bán|còn những máy nào|"
    r"có những dòng nào|đang kinh doanh gì|bán những gì|"
    r"có bán|đang bán gì|shop có gì|có máy nào|liệt kê)",
    re.IGNORECASE,
)

PRICE_PATTERNS = re.compile(
    r"(\bgiá\b|bao nhiêu tiền|bao nhiêu\b|giá bn|bn tiền|bao tiền|"
    r"giá sao|giá nhiêu|giá hiện tại|giá bây giờ|"
    r"bao nhiu|giá cả|mức giá|giá khoảng|"
    r"giá rẻ nhất|giá thấp nhất|giá cao nhất|"
    r"nhiêu tiền|bao nhiêu v|bao nhiêu ạ)",
    re.IGNORECASE,
)

STOCK_PATTERNS = re.compile(
    r"(còn hàng không|còn không|còn máy không|hết hàng chưa|"
    r"có hàng không|có sẵn không|còn sẵn không|"
    r"tình trạng|stock|hàng còn không|còn k|"
    r"còn bán không|hết chưa|còn hay hết|"
    r"mua được không|đặt được không|order được không)",
    re.IGNORECASE,
)

VARIANT_PATTERNS = re.compile(
    r"(màu gì|có màu gì|mấy màu|màu nào đẹp|màu nào|có mấy màu|"
    r"phiên bản nào|bản nào|dung lượng nào|có bản nào|"
    r"bao nhiêu gb|bao nhiêu tb|ram bao nhiêu|rom bao nhiêu|"
    r"có bao nhiêu phiên bản|mấy bản|mấy gb|bản gì|"
    r"màu đẹp nhất|nên chọn màu|màu nào bền)",
    re.IGNORECASE,
)

SPEC_PATTERNS = re.compile(
    r"(\bpin\b|mấy mah|camera|bao nhiêu mp|"
    r"chip gì|chip nào|màn hình|"
    r"cấu hình|thông số|spec\b|"
    r"\bram\b|\brom\b|bộ nhớ|dung lượng trong|"
    r"sạc nhanh|có sạc không dây|"
    r"kháng nước|chống nước|ip68|ip67|"
    r"nặng bao nhiêu|kích thước|trọng lượng|"
    r"tần số quét|\bhz\b|độ sáng|\bnit\b|"
    r"hiệu năng|mạnh không|chơi game|"
    r"chụp ảnh|quay phim|selfie)",
    re.IGNORECASE,
)

COMPARE_PATTERNS = re.compile(
    r"(so sánh|vs|versus|hay hơn|khác gì|"
    r"khác nhau|nên mua cái nào|chọn cái nào|"
    r"so với|đặt cạnh|so giùm|so giúp|"
    r"hơn gì|thua gì|ưu điểm hơn|nhược điểm)",
    re.IGNORECASE,
)

CONSULT_PATTERNS = re.compile(
    r"(tư vấn|gợi ý|recommend|suggest|"
    r"nên mua máy nào|chọn máy nào|"
    r"máy nào tốt|máy nào đáng mua|"
    r"trong tầm giá|budget|dưới \d+|trên \d+|"
    r"\d+\s*(triệu|tr|m)|"
    r"máy nào phù hợp|phù hợp với|"
    r"máy nào chơi game|máy chụp ảnh đẹp|máy pin trâu|"
    r"dùng lâu|bền|đáng tiền)",
    re.IGNORECASE,
)

ORDER_PATTERNS = re.compile(
    r"(đơn hàng|mã đơn|order|kiểm tra đơn|"
    r"tra cứu đơn|tracking|đơn của tôi|"
    r"đơn của mình|giao tới đâu rồi|"
    r"đơn tới đâu|bao giờ giao|khi nào nhận)",
    re.IGNORECASE,
)

ORDER_CODE_PATTERN = re.compile(r"\b(QH\d{6,}|QHUN\d+)\b", re.IGNORECASE)

# Session keys (multi-turn)
PENDING_COMPARE_KEY = "qh_chatbot_pending_compare"
PENDING_COMPARE_TTL_SEC = 10 * 60

INSTALLMENT_PATTERNS = re.compile(
    r"(trả góp|trả góp 0%|trả góp không lãi|"
    r"mua trả góp|trả trước bao nhiêu|"
    r"góp mỗi tháng bao nhiêu|"
    r"hỗ trợ trả góp|có trả góp|góp được không|"
    r"mua góp|chia kỳ|thanh toán góp)",
    re.IGNORECASE,
)

WARRANTY_PATTERNS = re.compile(
    r"(bảo hành bao lâu|bảo hành mấy tháng|"
    r"bảo hành chính hãng không|bảo hành ở đâu|"
    r"đổi trả|chính sách bảo hành|"
    r"bảo hành|warranty|đổi máy|trả máy|"
    r"lỗi thì sao|hư thì sao|bể màn)",
    re.IGNORECASE,
)

STAFF_PATTERNS = re.compile(
    r"(gặp nhân viên|người thật|"
    r"nói chuyện với người|gặp tư vấn viên|"
    r"kết nối nhân viên|chuyển nhân viên|"
    r"gọi nhân viên|cần người hỗ trợ)",
    re.IGNORECASE,
)

PRODUCT_NAME_PATTERNS = re.compile(
    r"(iphone|samsung|xiaomi|oppo|vivo|realme|huawei|nokia|pixel|"
    r"galaxy|redmi|note|pro|ultra|plus|max|lite|se|mini|air|fold|flip)",
    re.IGNORECASE,
)

# ════════════════════════════════════════════════════════════════
# UTILS
# ════════════════════════════════════════════════════════════════

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_SKU_PREFIX_RE = re.compile(r"^[A-Z0-9]{4,8}\s*-\s*", re.IGNORECASE)


def _format_price(value) -> str:
    try:
        v = int(value)
        if v <= 0:
            return None
        return f"{v:,}₫".replace(",", ".")
    except (TypeError, ValueError):
        return None


def _strip_html(text: str) -> str:
    return _HTML_TAG_RE.sub("", text).strip()


def _clean_color_name(raw: str) -> str:
    return _SKU_PREFIX_RE.sub("", raw).strip()


def _get_product_price_range(product: Product) -> tuple:
    """Return (min_price_str, max_price_str) from variants, or product.price."""
    try:
        variants = product.detail.variants.all()
        prices = [v.price for v in variants if v.price and v.price > 0]
        if prices:
            return _format_price(min(prices)), _format_price(max(prices))
    except Exception:
        pass
    p = _format_price(product.price)
    return p, p


def _get_product_colors(product: Product) -> list[str]:
    try:
        variants = product.detail.variants.all()
        return list(dict.fromkeys(_clean_color_name(v.color_name) for v in variants))
    except Exception:
        return []


def _get_product_storages(product: Product) -> list[str]:
    try:
        variants = product.detail.variants.all()
        return list(dict.fromkeys(v.storage for v in variants if v.storage))
    except Exception:
        return []


def _get_storage_prices(product: Product) -> dict:
    try:
        variants = product.detail.variants.all()
        sp = {}
        for v in variants:
            if v.storage and v.price and v.price > 0 and v.storage not in sp:
                sp[v.storage] = v.price
        return sp
    except Exception:
        return {}


def _parse_spec_json(spec_json) -> list[str]:
    if not spec_json:
        return []
    data = spec_json if isinstance(spec_json, (dict, list)) else json.loads(spec_json)

    lines = []
    groups = data.get("groups", data) if isinstance(data, dict) else data

    if isinstance(groups, list):
        for group in groups:
            if isinstance(group, dict) and "items" in group:
                for item in group["items"]:
                    label = item.get("label", "")
                    value = item.get("value", "")
                    if label and value:
                        lines.append(f"  - {label}: {value.replace(chr(10), ', ')}")
            elif isinstance(group, dict):
                for k, v in group.items():
                    lines.append(f"  - {k}: {v}")
    elif isinstance(groups, dict):
        for k, v in groups.items():
            if isinstance(v, dict):
                for sk, sv in v.items():
                    lines.append(f"  - {sk}: {sv}")
            else:
                lines.append(f"  - {k}: {v}")

    return lines[:35]


# ════════════════════════════════════════════════════════════════
# CHATBOT SERVICE
# ════════════════════════════════════════════════════════════════

class ChatbotService:

    def __init__(self):
        self.claude = ClaudeService()

    # ── Intent detection (thứ tự quan trọng!) ───────────────────
    def detect_intent(self, message: str) -> str:
        msg = message.strip()

        if ORDER_PATTERNS.search(msg) or ORDER_CODE_PATTERN.search(msg):
            return "order"

        if LIST_PRODUCT_PATTERNS.search(msg):
            return "list_products"

        if COMPARE_PATTERNS.search(msg):
            return "compare"

        if CONSULT_PATTERNS.search(msg):
            return "consult"

        if SPEC_PATTERNS.search(msg):
            return "spec"

        if PRICE_PATTERNS.search(msg):
            return "price"

        if STOCK_PATTERNS.search(msg):
            return "stock"

        if VARIANT_PATTERNS.search(msg):
            return "variant"

        if INSTALLMENT_PATTERNS.search(msg):
            return "installment"

        if WARRANTY_PATTERNS.search(msg):
            return "warranty"

        if STAFF_PATTERNS.search(msg):
            return "staff"

        if GREETING_PATTERNS.search(msg):
            return "greeting"

        if PRODUCT_NAME_PATTERNS.search(msg):
            return "product_mention"

        return "unknown"

    # ── Product name detection ──────────────────────────────────
    def detect_product_names(self, message: str) -> list[str]:
        products = Product.objects.filter(is_active=True).values_list("name", flat=True)
        found = []
        msg_lower = message.lower()
        for name in products:
            if name.lower() in msg_lower:
                found.append(name)

        if not found:
            found = self._fuzzy_match(msg_lower, products)

        if len(found) > 1:
            found.sort(key=lambda n: -len(n))
            longest = found[0]
            found = [n for n in found if n.lower() not in longest.lower() or n == longest]
            if not found:
                found = [longest]

        return found

    def _fuzzy_match(self, msg_lower: str, product_names) -> list[str]:
        # Tokenize into single-word tokens (previous pattern produced multi-word tokens → poor matching)
        tokens = re.findall(r"[a-zA-Z0-9]+", msg_lower)
        candidates: list[tuple[str, int]] = []
        for name in product_names:
            name_lower = name.lower()
            name_tokens = set(re.findall(r"[a-zA-Z0-9]+", name_lower))
            match_count = sum(1 for t in tokens if t in name_tokens or any(t in nt for nt in name_tokens))
            if match_count >= 2 or (len(name_tokens) == 1 and match_count >= 1 and len(tokens) <= 3):
                candidates.append((name, match_count))
        candidates.sort(key=lambda x: -x[1])
        return [c[0] for c in candidates[:3]]

    def _get_pending_compare_base(self, session) -> str | None:
        if not session:
            return None
        try:
            data = session.get(PENDING_COMPARE_KEY)
            if not isinstance(data, dict):
                return None
            base = (data.get("base") or "").strip()
            ts = float(data.get("ts") or 0)
            if not base:
                return None
            if not ts or (time.time() - ts) > PENDING_COMPARE_TTL_SEC:
                session.pop(PENDING_COMPARE_KEY, None)
                return None
            return base
        except Exception:
            return None

    def _set_pending_compare_base(self, session, base_name: str) -> None:
        if not session:
            return
        try:
            session[PENDING_COMPARE_KEY] = {"base": base_name, "ts": time.time()}
            session.modified = True
        except Exception:
            pass

    def _clear_pending_compare(self, session) -> None:
        if not session:
            return
        try:
            session.pop(PENDING_COMPARE_KEY, None)
            session.modified = True
        except Exception:
            pass

    # ── Build product context for Claude ────────────────────────
    def _build_product_context(self, product: Product) -> str:
        parts = [f"San pham: {product.name}"]

        if product.stock > 0:
            parts.append("Tinh trang: CON HANG")
        else:
            parts.append("Tinh trang: HET HANG")

        try:
            detail = product.detail

            if detail.description:
                desc = _strip_html(detail.description[:400])
                if desc:
                    parts.append(f"Mo ta: {desc}")

            variants = detail.variants.all()
            if variants.exists():
                prices = [v.price for v in variants if v.price and v.price > 0]
                if prices:
                    min_p = _format_price(min(prices))
                    max_p = _format_price(max(prices))
                    if min_p and max_p and min_p != max_p:
                        parts.append(f"Gia: tu {min_p} den {max_p}")
                    elif min_p:
                        parts.append(f"Gia: {min_p}")

                colors = list(dict.fromkeys(_clean_color_name(v.color_name) for v in variants))
                if colors:
                    parts.append(f"Mau sac: {', '.join(colors)}")

                storages = list(dict.fromkeys(v.storage for v in variants if v.storage))
                if storages:
                    parts.append(f"Dung luong: {', '.join(storages)}")

                storage_prices = {}
                for v in variants:
                    if v.storage and v.price and v.price > 0 and v.storage not in storage_prices:
                        storage_prices[v.storage] = v.price
                if storage_prices:
                    price_lines = [f"  - {s}: {_format_price(p)}" for s, p in storage_prices.items() if _format_price(p)]
                    if price_lines:
                        parts.append("Gia theo dung luong:\n" + "\n".join(price_lines))
            else:
                p_price = _format_price(product.price)
                if p_price:
                    parts.append(f"Gia: {p_price}")
                if product.original_price and product.original_price > product.price:
                    op = _format_price(product.original_price)
                    if op:
                        parts.append(f"Gia goc: {op} (giam {product.get_discount_percent()}%)")

            try:
                spec = detail.specification
                if spec.spec_json:
                    spec_lines = _parse_spec_json(spec.spec_json)
                    if spec_lines:
                        parts.append("Thong so ky thuat:\n" + "\n".join(spec_lines))
            except ProductSpecification.DoesNotExist:
                pass

        except ProductDetail.DoesNotExist:
            p_price = _format_price(product.price)
            if p_price:
                parts.append(f"Gia: {p_price}")

        contents = ProductContent.objects.filter(product=product).values_list("content_text", flat=True)[:2]
        for ct in contents:
            if ct:
                clean = _strip_html(ct[:300])
                if clean:
                    parts.append(f"Noi dung: {clean}")

        return "\n".join(parts)

    # ════════════════════════════════════════════════════════════
    # HANDLERS (không gọi Claude)
    # ════════════════════════════════════════════════════════════

    def _handle_greeting(self) -> dict[str, Any]:
        return {
            "message": "Chào anh/chị! Mình là trợ lý mua sắm của QHUN22. Mình có thể giúp gì cho anh/chị?",
            "suggestions": MENU_SUGGESTIONS,
        }

    def _handle_staff(self) -> dict[str, Any]:
        return {"message": STAFF_MSG, "suggestions": ["Tư vấn chọn máy", "So sánh sản phẩm"]}

    def _handle_installment(self) -> dict[str, Any]:
        return {"message": INSTALLMENT_MSG, "suggestions": ["Tư vấn chọn máy", "Gặp nhân viên"]}

    def _handle_warranty(self) -> dict[str, Any]:
        return {"message": WARRANTY_MSG, "suggestions": MENU_SUGGESTIONS}

    def _handle_list_products(self) -> dict[str, Any]:
        products = Product.objects.filter(is_active=True).order_by("name")
        if not products.exists():
            return {"message": "Hiện tại shop chưa có sản phẩm nào. Anh/chị quay lại sau nhé!", "suggestions": []}

        lines = ["QHUN22 hiện đang kinh doanh các sản phẩm sau:"]
        for p in products:
            min_p, max_p = _get_product_price_range(p)
            price_txt = f"từ {min_p}" if min_p else "Liên hệ"
            stock_txt = "Còn hàng" if p.stock > 0 else "Hết hàng"
            lines.append(f"  - {p.name} / {price_txt} ({stock_txt})")
        lines.append("\nAnh/chị muốn tìm hiểu sản phẩm nào, cứ hỏi mình nhé!")
        return {"message": "\n".join(lines), "suggestions": [p.name for p in products[:4]]}

    def _handle_price(self, product: Product) -> dict[str, Any]:
        min_p, max_p = _get_product_price_range(product)
        storage_prices = _get_storage_prices(product)

        if storage_prices:
            lines = [f"{product.name} hiện có giá như sau:"]
            for storage, price in storage_prices.items():
                lines.append(f"  - Bản {storage}: {_format_price(price)}")
            msg = "\n".join(lines)
        elif min_p and max_p and min_p != max_p:
            msg = f"{product.name} có giá từ {min_p} đến {max_p}, tùy theo dung lượng anh/chị chọn."
        elif min_p:
            msg = f"{product.name} hiện có giá {min_p}."
        else:
            msg = f"Mình chưa có thông tin giá của {product.name}, anh/chị liên hệ hotline để được hỗ trợ nhé!"

        return {"message": msg, "suggestions": [f"Thông số {product.name}", f"Còn hàng {product.name}", "So sánh sản phẩm"]}

    def _handle_stock(self, product: Product) -> dict[str, Any]:
        if product.stock > 0:
            colors = _get_product_colors(product)
            storages = _get_product_storages(product)
            lines = [f"{product.name} hiện đang còn hàng."]
            if colors:
                lines.append(f"Màu có sẵn: {', '.join(colors)}.")
            if storages:
                lines.append(f"Dung lượng: {', '.join(storages)}.")
            lines.append("Anh/chị muốn đặt mua luôn không?")
            msg = "\n".join(lines)
        else:
            msg = f"{product.name} hiện tạm hết hàng. Anh/chị để lại thông tin, mình sẽ thông báo khi có hàng trở lại nhé!"

        return {"message": msg, "suggestions": [f"Giá {product.name}", "Tư vấn mẫu khác", "Gặp nhân viên"]}

    def _handle_variant(self, product: Product) -> dict[str, Any]:
        colors = _get_product_colors(product)
        storages = _get_product_storages(product)
        storage_prices = _get_storage_prices(product)

        lines = [f"{product.name} hiện có:"]
        if colors:
            lines.append(f"Màu sắc: {', '.join(colors)}.")
        if storages and storage_prices:
            sp_lines = []
            for s in storages:
                p = storage_prices.get(s)
                sp_lines.append(f"  - {s}: {_format_price(p)}" if p and _format_price(p) else f"  - {s}")
            lines.append("Dung lượng và giá:\n" + "\n".join(sp_lines))
        elif storages:
            lines.append(f"Dung lượng: {', '.join(storages)}.")

        if not colors and not storages:
            lines = [f"Mình chưa có thông tin chi tiết phiên bản của {product.name}, anh/chị liên hệ hotline nhé!"]

        return {"message": "\n".join(lines), "suggestions": [f"Thông số {product.name}", f"Giá {product.name}", "So sánh sản phẩm"]}

    def _handle_order(self, message: str, user) -> dict[str, Any]:
        code_match = ORDER_CODE_PATTERN.search(message)
        if code_match:
            order_code = code_match.group(1).upper()
            try:
                order = Order.objects.get(order_code=order_code)
                status_map = dict(Order.STATUS_CHOICES)
                status_vn = status_map.get(order.status, order.status)
                msg = (
                    f"Đơn hàng {order.order_code}\n"
                    f"Trạng thái: {status_vn}\n"
                    f"Tổng tiền: {_format_price(order.total_amount) or '0₫'}\n"
                    f"Phương thức TT: {order.get_payment_method_display()}\n"
                    f"Ngày đặt: {order.created_at.strftime('%d/%m/%Y %H:%M')}"
                )
                return {"message": msg, "suggestions": ["Xem sản phẩm mới", "Tư vấn chọn máy"]}
            except Order.DoesNotExist:
                return {
                    "message": f"Mình không tìm thấy đơn hàng {order_code}. Anh/chị kiểm tra lại mã nhé!",
                    "suggestions": ["Kiểm tra đơn hàng khác", "Gặp nhân viên"],
                }

        if user and user.is_authenticated:
            recent = Order.objects.filter(user=user).order_by("-created_at")[:3]
            if recent.exists():
                status_map = dict(Order.STATUS_CHOICES)
                lines = ["Đơn hàng gần đây của anh/chị:"]
                for o in recent:
                    lines.append(f"  - {o.order_code} / {status_map.get(o.status, o.status)} / {_format_price(o.total_amount) or '0₫'}")
                return {"message": "\n".join(lines), "suggestions": ["Xem chi tiết đơn hàng"]}

        return {
            "message": "Anh/chị cho mình mã đơn hàng (VD: QH250101 hoặc QHUN38453) để mình tra cứu nhé!",
            "suggestions": ["Tư vấn chọn máy", "Gặp nhân viên"],
        }

    def _handle_consult(self, message: str) -> dict[str, Any]:
        price_match = re.search(r"(\d+)\s*(triệu|tr|m)", message.lower())
        if price_match:
            budget = int(price_match.group(1)) * 1_000_000
            margin = budget * 0.2
            featured = Product.objects.filter(
                is_active=True, stock__gt=0,
                price__gte=budget - margin, price__lte=budget + margin,
            ).order_by("price")[:5]

            if not featured.exists():
                all_products = Product.objects.filter(is_active=True, stock__gt=0).order_by("price")
                featured = all_products[:5]

            if featured.exists():
                lines = [f"Trong tầm giá {price_match.group(0)}, mình gợi ý:"]
                for p in featured:
                    min_p, _ = _get_product_price_range(p)
                    lines.append(f"  - {p.name} / từ {min_p or 'Liên hệ'}")
                lines.append("\nAnh/chị quan tâm mẫu nào, hỏi mình thêm nhé!")
                return {"message": "\n".join(lines), "suggestions": [p.name for p in featured[:3]]}

        featured = Product.objects.filter(is_active=True, is_featured=True).order_by("-updated_at")[:5]
        if not featured.exists():
            featured = Product.objects.filter(is_active=True, stock__gt=0).order_by("-updated_at")[:5]

        if featured.exists():
            lines = ["Mình gợi ý một số mẫu cho anh/chị:"]
            for p in featured:
                min_p, _ = _get_product_price_range(p)
                stock_txt = "Còn hàng" if p.stock > 0 else "Hết hàng"
                lines.append(f"  - {p.name} / từ {min_p or 'Liên hệ'} ({stock_txt})")
            lines.append("\nAnh/chị quan tâm mẫu nào, hỏi mình thêm nhé!")
            return {"message": "\n".join(lines), "suggestions": [p.name for p in featured[:3]]}

        return {"message": NOT_FOUND_MSG, "suggestions": MENU_SUGGESTIONS}

    def _handle_compare_with_ai(self, message: str, products: list[Product]) -> dict[str, Any]:
        contexts = [self._build_product_context(p) for p in products]
        combined = "\n\n---\n\n".join(contexts)

        compare_system = SYSTEM_PROMPT + COMPARE_SYSTEM_EXTRA
        user_prompt = COMPARE_USER_TEMPLATE.format(combined_context=combined, message=message)

        ai_reply = self.claude.call(compare_system, user_prompt, max_tokens=COMPARE_MAX_TOKENS)
        if ai_reply:
            return {"message": ai_reply, "suggestions": [p.name for p in products]}

        lines = ["So sánh nhanh:"]
        for p in products:
            min_p, _ = _get_product_price_range(p)
            lines.append(f"  - {p.name} / {min_p or 'Liên hệ'}")
        return {"message": "\n".join(lines), "suggestions": MENU_SUGGESTIONS}

    def _handle_spec_with_ai(self, message: str, product: Product) -> dict[str, Any]:
        context = self._build_product_context(product)
        user_prompt = NORMAL_USER_TEMPLATE.format(context=context, message=message)

        ai_reply = self.claude.call(SYSTEM_PROMPT, user_prompt, max_tokens=NORMAL_MAX_TOKENS)
        if ai_reply:
            return {"message": ai_reply, "suggestions": [f"Giá {product.name}", f"Còn hàng {product.name}", "So sánh sản phẩm"]}

        return self._fallback_product_response(product)

    def _handle_product_with_ai(self, message: str, product: Product) -> dict[str, Any]:
        context = self._build_product_context(product)
        user_prompt = NORMAL_USER_TEMPLATE.format(context=context, message=message)

        ai_reply = self.claude.call(SYSTEM_PROMPT, user_prompt, max_tokens=NORMAL_MAX_TOKENS)
        if ai_reply:
            suggestions = ["Xem thêm sản phẩm", "So sánh sản phẩm"]
            if product.stock <= 0:
                suggestions.insert(0, "Tư vấn mẫu khác")
            return {"message": ai_reply, "suggestions": suggestions}

        return self._fallback_product_response(product)

    def _fallback_product_response(self, product: Product) -> dict[str, Any]:
        stock_txt = "Còn hàng" if product.stock > 0 else "Hết hàng"
        min_p, _ = _get_product_price_range(product)
        msg = (
            f"{product.name}\n"
            f"Giá: {min_p or 'Liên hệ'}\n"
            f"{stock_txt}"
        )
        return {"message": msg, "suggestions": MENU_SUGGESTIONS}

    # ════════════════════════════════════════════════════════════
    # MAIN ENTRY POINT
    # ════════════════════════════════════════════════════════════

    def process_message(self, message: str, user=None, session=None) -> dict[str, Any]:
        message = message.strip()
        if not message:
            return {"message": MENU_MSG, "suggestions": MENU_SUGGESTIONS}

        # ── Multi-turn compare: if user previously picked base product, and now sends a product name ──
        pending_base = self._get_pending_compare_base(session)
        if pending_base:
            # Try resolve the second product from this message
            target_names = self.detect_product_names(message)
            if target_names:
                base_product = Product.objects.filter(is_active=True, name=pending_base).first()
                target_qs = (
                    Product.objects.filter(is_active=True, name__in=target_names)
                    .exclude(name=pending_base)
                )
                if base_product and target_qs.exists():
                    target_product = max(list(target_qs), key=lambda p: len(p.name))
                    self._clear_pending_compare(session)
                    return self._handle_compare_with_ai(
                        f"So sánh {base_product.name} và {target_product.name}",
                        [base_product, target_product],
                    )
            # If user changes topic (non-compare intent), clear pending compare to avoid sticky state
            intent_now = self.detect_intent(message)
            if intent_now not in ("compare", "unknown"):
                self._clear_pending_compare(session)

        intent = self.detect_intent(message)

        # ── Fixed responses (không gọi Claude) ──────────────────
        if intent == "order":
            return self._handle_order(message, user)

        if intent == "greeting":
            return self._handle_greeting()

        if intent == "staff":
            return self._handle_staff()

        if intent == "installment":
            return self._handle_installment()

        if intent == "warranty":
            return self._handle_warranty()

        if intent == "list_products":
            return self._handle_list_products()

        # Xử lý nhanh suggestion buttons
        if message.strip() == "Gặp nhân viên":
            return self._handle_staff()
        if message.strip() == "Tư vấn chọn máy":
            return self._handle_consult(message)
        if message.strip() == "So sánh sản phẩm":
            return {"message": "Anh/chị muốn so sánh 2 sản phẩm nào? VD: so sánh iPhone 17 vs iPhone Air", "suggestions": []}
        if message.strip() == "Kiểm tra đơn hàng":
            return self._handle_order(message, user)

        # ── Detect product names ────────────────────────────────
        product_names = self.detect_product_names(message)

        # ── Intents cần sản phẩm ────────────────────────────────
        if intent == "consult":
            if product_names:
                products = Product.objects.filter(name__in=product_names, is_active=True)
                if products.exists():
                    return self._handle_product_with_ai(message, max(products, key=lambda p: len(p.name)))
            return self._handle_consult(message)

        if intent == "compare":
            if product_names:
                products = Product.objects.filter(name__in=product_names, is_active=True)
                if products.count() >= 2:
                    return self._handle_compare_with_ai(message, list(products[:2]))
                elif products.count() == 1:
                    # Remember base product for the next user click/answer
                    self._set_pending_compare_base(session, products.first().name)
                    return {
                        "message": f"Anh/chị muốn so sánh {products.first().name} với sản phẩm nào?",
                        "suggestions": [p.name for p in Product.objects.filter(is_active=True).exclude(name=products.first().name)[:3]],
                    }
            return {"message": "Anh/chị muốn so sánh 2 sản phẩm nào? VD: so sánh iPhone 17 vs iPhone Air", "suggestions": []}

        if not product_names:
            if intent == "unknown":
                return {"message": MENU_MSG, "suggestions": MENU_SUGGESTIONS}
            return {"message": NOT_FOUND_MSG, "suggestions": MENU_SUGGESTIONS}

        products = Product.objects.filter(name__in=product_names, is_active=True)
        if not products.exists():
            return {"message": NOT_FOUND_MSG, "suggestions": MENU_SUGGESTIONS}

        product = max(products, key=lambda p: len(p.name))

        # ── Direct responses (không gọi Claude) ────────────────
        if intent == "price":
            return self._handle_price(product)

        if intent == "stock":
            return self._handle_stock(product)

        if intent == "variant":
            return self._handle_variant(product)

        # ── AI responses (gọi Claude) ──────────────────────────
        if intent == "spec":
            return self._handle_spec_with_ai(message, product)

        return self._handle_product_with_ai(message, product)
