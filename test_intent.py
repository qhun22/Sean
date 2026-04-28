"""
Test Chatbot QHUN22 - Intent Detection Patterns
Chạy: python test_intent.py

Script này copy PATTERNS từ chatbot_service.py (lines 100-500)
và test chúng để verify intent detection hoạt động đúng.
"""

import re
import unicodedata
import sys

# ============================================================
# COPY PATTERNS FROM chatbot_service.py (lines 100-500)
# ============================================================

GREETING_PATTERNS = re.compile(
    r"(xin chào|chào bạn|chào shop|chào\b|hello\b|^hi\b|^hey\b|alo\b|"
    r"ê shop|shop ơi|ad ơi|admin ơi|"
    r"có ai không|có ai trực không|tư vấn giúp|giúp mình với|"
    r"^help\b|^support\b|mình cần hỗ trợ|cho mình hỏi|hỏi chút|"
    r"ơi shop|ơi ơi|shop ơi ơi|ui shop|uii|uy|uyy|uyyy|"
    r"chào buổi sáng|chào buổi trưa|chào buổi tối|"
    r"zô shop|zô|zạ|zk|zp|chk|chek|chik|chkò|yo|yo yo|"
    r"khỏe không|khỏe không|good morning|good afternoon|"
    r"hi there|greetings)",
    re.IGNORECASE,
)

GREETING_PATTERNS_NORM = re.compile(
    r"(xin chao|chao ban|chao shop|chao\b|hello\b|^hi\b|^hey\b|alo\b|"
    r"e shop|shop oi|ad oi|admin oi|"
    r"co ai khong|co ai truc khong|tu van giup|giup minh voi|"
    r"^help\b|^support\b|minh can ho tro|cho minh hoi|hoi chut|"
    r"oi shop|oi oi|shop oi oi|ui shop|uii|uy|uyy|uyyy|"
    r"chao buoi sang|chao buoi trua|chao buoi toi|"
    r"zo shop|zo|za|zk|zp|chk|chek|chik|chkò|yo|yo yo|"
    r"khoe khong|khoe khong|good morning|good afternoon|"
    r"hi there|greetings)",
    re.IGNORECASE,
)

LIST_PRODUCT_PATTERNS = re.compile(
    r"(mẫu nào|những mẫu|có những gì|bán gì|sản phẩm nào|có gì|"
    r"xem sản phẩm mới|mẫu mới|hàng mới về|sản phẩm mới|"
    r"danh sách máy|danh sách sản phẩm|các máy đang bán|các mẫu iphone|các dòng iphone|các dòng samsung|"
    r"shop có bán|hiện có những|hiện đang bán|còn những máy nào|"
    r"có những dòng nào|đang kinh doanh gì|bán những gì|"
    r"có bán|đang bán gì|shop có gì|có máy nào|liệt kê|"
    r"có những máy nào|danh sách|danh sach|"
    r"xem sản phẩm|xem san pham|show me phones|list products)",
    re.IGNORECASE,
)

LIST_PRODUCT_PATTERNS_NORM = re.compile(
    r"(mau nao|nhung mau|co nhung gi|ban gi|san pham nao|co gi|"
    r"xem san pham moi|mau moi|hang moi ve|san pham moi|"
    r"danh sach may|danh sach san pham|cac may dang ban|cac mau iphone|cac dong iphone|cac dong samsung|"
    r"shop co ban|hien co nhung|hien dang ban|con nhung may nao|"
    r"co nhung dong nao|dang kinh doanh gi|ban nhung gi|"
    r"co ban|dang ban gi|shop co gi|co may nao|liet ke|"
    r"co nhung may nao|danh sach|danh sach|"
    r"xem san pham|xem san pham|show me phones|list products)",
    re.IGNORECASE,
)

PRICE_PATTERNS = re.compile(
    r"(\bgiá\b|bao nhiêu tiền|bao nhiêu\b|giá bn|bn tiền|bao tiền|"
    r"giá sao|giá nhiêu|giá hiện tại|giá bây giờ|"
    r"bao nhiu|giá cả|mức giá|giá khoảng|"
    r"giá rẻ nhất|giá thấp nhất|giá cao nhất|"
    r"nhiêu tiền|bao nhiêu v|bao nhiêu ạ|"
    r"tiền\b|đắt không|co gia|giá co|có giá|"
    r"check giá|check gia|coi giá|xem giá giùm|"
    r"rẻ nhất|cao nhất|mắc nhất)",
    re.IGNORECASE,
)

PRICE_PATTERNS_NORM = re.compile(
    r"(gia|bao nhieu tien|bao nhieu|gia bn|bn tien|bao tien|"
    r"gia sao|gia nhieu|gia hien tai|gia bay gio|"
    r"bao nhiu|muc gia|gia khoang|nhiu tien|xin gia|"
    r"bao nhieu a|bao nhieu vay|"
    r"tien\b|dat khong|co gia|giá có|có giá|"
    r"check gia|coi gia|xem gia gium|"
    r"re nhat|cao nhat|mac nhat)",
    re.IGNORECASE,
)

STOCK_PATTERNS = re.compile(
    r"(còn hàng không|còn hàng|còn không|còn máy không|hết hàng chưa|hết hàng|"
    r"có hàng không|có sẵn không|còn sẵn không|"
    r"tình trạng|stock|hàng còn không|còn k|"
    r"còn bán không|hết chưa|còn hay hết|"
    r"mua được không|đặt được không|order được không|"
    r"lấy được không|bán không|bán chưa|"
    r"ship được không|ship chưa|"
    r"còn hem|hết rồi|hết hem|bán rồi|"
    r"bán được không|chưa bán|đang bán)",
    re.IGNORECASE,
)

STOCK_PATTERNS_NORM = re.compile(
    r"(con hang khong|con hang|con khong|con may khong|het hang chua|het hang|"
    r"co hang khong|co san khong|con san khong|"
    r"tinh trang|stock|hang con khong|con k|"
    r"con ko|het chua|con hay het|"
    r"mua duoc khong|dat duoc khong|order duoc khong|"
    r"lay duoc khong|ban khong|ban chua|"
    r"ship duoc khong|ship chua|"
    r"con hem|het roi|het hem|ban roi|"
    r"ban duoc khong|chua ban|dang ban)",
    re.IGNORECASE,
)

VARIANT_PATTERNS = re.compile(
    r"(màu gì|có màu gì|mấy màu|màu nào đẹp|màu nào|có mấy màu|"
    r"phiên bản nào|bản nào|dung lượng nào|có bản nào|"
    r"bao nhiêu gb|bao nhiêu tb|ram bao nhiêu|rom bao nhiêu|"
    r"có bao nhiêu phiên bản|mấy bản|mấy gb|bản gì|"
    r"màu đẹp nhất|nên chọn màu|màu nào bền|"
    r"màu nào đẹp nhất|đẹp nhất|màu nào hot|"
    r"bản \d+gb|bản \d+gb|phiên bản \d+|"
    r"storage nào|dung lượng nào|128gb|256gb|512gb|1tb|"
    r"\d+gb|\d+tb|\d+gb\b|\d+ tb\b|"
    r"\d+\s*gb\b|\d+\s*tb\b|"
    r"128 hay 256|256 hay 512|bản nào|bản gì|"
    r"mấy phiên bản|phiên bản nào)",
    re.IGNORECASE,
)

VARIANT_PATTERNS_NORM = re.compile(
    r"(mau gi|co mau gi|may mau|mau nao dep|mau nao|co may mau|"
    r"phien ban nao|ban nao|dung luong nao|co ban nao|"
    r"bao nhieu gb|bao nhieu tb|ram bao nhieu|rom bao nhieu|"
    r"co bao nhieu phien ban|may ban|may gb|ban gi)",
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

SPEC_PATTERNS_NORM = re.compile(
    r"(pin|mah|camera|mp|chip|man hinh|"
    r"cau hinh|thong so|spec|ram|rom|bo nho|dung luong trong|"
    r"sac nhanh|sac khong day|khang nuoc|chong nuoc|ip68|ip67|"
    r"nang bao nhieu|kich thuoc|trong luong|tan so quet|hz|do sang|nit|"
    r"hieu nang|manh khong|choi game|chup anh|quay phim|selfie)",
    re.IGNORECASE,
)

COMPARE_PATTERNS = re.compile(
    r"(so sánh|vs|versus|hay hơn|khác gì|"
    r"khác nhau|nên mua cái nào|chọn cái nào|"
    r"so với|đặt cạnh|so giùm|so giúp|"
    r"hơn gì|thua gì|ưu điểm hơn|nhược điểm|"
    r"\bhay\b.*\b(mua|chọn|nên)|"
    r"\b(mua|chọn|nên).*\bhay\b|"
    r"con nào|con nào ngon|con nào tốt|con nào rẻ|"
    r"cái nào ngon|cái nào tốt|cái nào rẻ|"
    r"cái nào đáng mua hơn|ngon hơn|tốt hơn|rẻ hơn|"
    r"iphone hay samsung|samsung hay iphone|ip hay ss|ss hay apple|"
    r"android hay ios|ios hay android|ios vs android|"
    r"nên mua max hay pro|nên mua pro hay max|"
    r"max hay pro hay|pro hay max hay|"
    r"16 pro hay 16 pro max|16 pro max hay|ultra hay pro max|"
    r"hay\b.*\bmáy\b|máy\b.*\bhay\b|"
    r"nên lấy|nên chọn)",
    re.IGNORECASE,
)

COMPARE_PATTERNS_NORM = re.compile(
    r"(so sanh|vs|versus|hay hon|khac gi|"
    r"khac nhau|nen mua cai nao|chon cai nao|"
    r"so voi|dat canh|so giup|hơn gi|thua gi|uu diem hon|nhuoc diem)",
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
    r"dùng lâu|bền|đáng tiền|"
    r"mình cần|mình muốn|mình thích|mình tìm|"
    r"cho mình gợi ý|gợi ý cho|recommend cho|"
    r"ngân sách|budget là|tiền là|tiền|mình có \d+|"
    r"sinh viên|hs|sVs|dân văn phòng|dân công sở|"
    r"chụp ảnh|game|pin|btq|mỏng nhẹ|"
    r"tv dum|tv giup|giúp tôi|giúp mình|"
    r"chỉ cho|tư vấn cho|check|recommend|đi tour|"
    r"nghiên cứu|phân vân|lăn tăn|băn khoăn|mắc nghi|"
    r"cân nhắc|so sánh giá|so sánh máy|"
    r"có nên mua|nên mua không|có đáng mua không|"
    r"phù hợp không|hợp lý không|tốt không|có tốt không|"
    r"mua được không|xứng đáng không|đáng không|"
    r"review|đánh giá|nhận xét|kinh nghiệm|"
    r"mua hàng|order|mua online|mua ở đâu|"
    r"dùng thế nào|sử dụng thế nào|cách dùng|"
    r"cấu hình|thông số kỹ thuật|đặc điểm)",
    re.IGNORECASE,
)

CONSULT_PATTERNS_NORM = re.compile(
    r"(tu van|goi y|recommend|suggest|"
    r"nen mua may nao|chon may nao|"
    r"may nao tot|may nao dang mua|"
    r"trong tam gia|budget|duoi \d+|tren \d+|"
    r"\d+\s*(trieu|tr|m)|"
    r"may nao phu hop|phu hop voi|"
    r"may nao choi game|may chup anh dep|may pin trau|"
    r"dung lau|ben|dang tien|tv dum|tv giup|"
    r"minh can|minh muon|minh thich|minh tim|"
    r"cho minh goi y|goi y cho|recommend cho|"
    r"ngan sach|budget la|tien la|minh co \d+|"
    r"sinh vien|hs|svs|dan van phong|dan cong so|"
    r"chup anh|game|pin|btq|mong nhe|"
    r"giup toi|giup minh|chi cho|tu van cho|check|di tour|"
    r"nghien cuuu|phan van|lan tan|bankhoan|mac nghi|"
    r"can nhac|so sanh gia|so sanh may|"
    r"co nen mua|nen mua khong|co dang mua khong|"
    r"phu hop khong|hop ly khong|tot khong|co tot khong|"
    r"mua duoc khong|xung dang khong|dang khong|"
    r"review|danh gia|nhan xet|kinh nghiem|"
    r"mua hang|order|mua online|mua o dau|"
    r"dung the nao|su dung the nao|cach dung|"
    r"cau hinh|thong so ky thuat|dac diem)",
    re.IGNORECASE,
)

ORDER_PATTERNS = re.compile(
    r"(đơn hàng|mã đơn|order|kiểm tra đơn|"
    r"tra cứu đơn|tracking|đơn của tôi|"
    r"đơn của mình|giao tới đâu rồi|"
    r"đơn tới đâu|bao giờ giao|khi nào nhận|"
    r"vận đơn|mã vận đơn|check đơn|xem đơn|"
    r"đơn đâu|đơn đâu rồi|ship tới đâu|"
    r"tình trạng đơn|tinhtrangs don|don cua toi|"
    r"đơn có giao chưa|don giao chua|đơn chưa|"
    r"đơn có được duyệt chưa|don duoc duyet|"
    r"QH\d{6,}|QHUN\d+|đơn \d+|don \d+|"
    r"xem đơn|kiểm tra đơn|tra cuu don|"
    r"đơn nào|đơn của|đơn mới|đơn cũ)",
    re.IGNORECASE,
)

ORDER_PATTERNS_NORM = re.compile(
    r"(don hang|ma don|order|kiem tra don|"
    r"tra cuu don|check don|tracking|don cua toi|"
    r"don cua minh|don cua t|giao toi dau roi|"
    r"don toi dau|ship toi dau|bao gio giao|khi nao nhan|"
    r"ma van don|van don|xem don|don dau|"
    r"don dau roi|ship toi dau|"
    r"tinh trang don|tinhtrangs don|"
    r"don co giao chua|don giao chua|don chua|"
    r"don co duoc duyet chua|don duoc duyet|"
    r"QH\d{6,}|QHUN\d+|don \d+)",
    re.IGNORECASE,
)

ORDER_CODE_PATTERN = re.compile(r"\b(QH\d{6,}|QHUN\d+)\b", re.IGNORECASE)

ORDER_CAPABILITY_PATTERNS = re.compile(
    r"((bạn|em|bot).*(có thể|giúp).*(tra cứu|kiểm tra).*(đơn hàng|mã đơn).*(không|hay không|được không))|"
    r"((hỗ trợ|giúp).*(tra cứu|kiểm tra|tra đơn|tra đơn hàng).*(không|hay không|được không))|"
    r"((tra cứu|kiểm tra|tra đơn).*(đơn hàng|mã đơn).*(được không|hay không|không))",
    re.IGNORECASE,
)

ORDER_CAPABILITY_PATTERNS_NORM = re.compile(
    r"((ban|em|bot).*(co the|giup|ho tro).*(tra cuu|kiem tra|check).*(don|ma don|don hang).*(duoc khong|hay khong|khong)?)|"
    r"((ho tro|giup).*(tra cuu|kiem tra|check|tra don|tra don hang).*(duoc khong|hay khong|khong))|"
    r"((tra cuu|kiem tra|check|tra don).*(don|ma don|don hang).*(duoc khong|hay khong|khong))|"
    r"(giup.*(tra cuu|kiem tra).*(don|ma don).*(duoc khong|khong|hay khong))",
    re.IGNORECASE,
)

INSTALLMENT_PATTERNS = re.compile(
    r"(trả góp|trả góp 0%|trả góp không lãi|"
    r"mua trả góp|trả trước bao nhiêu|"
    r"góp mỗi tháng bao nhiêu|"
    r"hỗ trợ trả góp|có trả góp|góp được không|"
    r"mua góp|chia kỳ|thanh toán góp|"
    r"installment|tra gop|tra truoc|gop thang|"
    r"góp \d+ tháng|gop \d+ thang|"
    r"góp bao lâu|gop bao lau|"
    r"trả góp đi|mua góp đi)",
    re.IGNORECASE,
)

INSTALLMENT_PATTERNS_NORM = re.compile(
    r"(tra gop|tra gop 0|tra gop khong lai|"
    r"mua tra gop|tra truoc bao nhieu|"
    r"gop moi thang bao nhieu|"
    r"ho tro tra gop|co tra gop|gop duoc khong|"
    r"mua gop|chia ky|thanh toan gop)",
    re.IGNORECASE,
)

WARRANTY_PATTERNS = re.compile(
    r"(bảo hành bao lâu|bảo hành mấy tháng|"
    r"bảo hành chính hãng không|bảo hành ở đâu|"
    r"đổi trả|chính sách bảo hành|"
    r"bảo hành|warranty|đổi máy|trả máy|"
    r"lỗi thì sao|hư thì sao|bể màn|"
    r"bh bao lâu|bh mấy tháng|bh ở đâu|"
    r"bao hanh|bh\b|đổi trả|tra hang)",
    re.IGNORECASE,
)

WARRANTY_PATTERNS_NORM = re.compile(
    r"(bao hanh bao lau|bao hanh may thang|"
    r"bao hanh chinh hang khong|bao hanh o dau|"
    r"doi tra|chinh sach bao hanh|"
    r"bao hanh|warranty|doi may|tra may|"
    r"loi thi sao|hu thi sao|be man)",
    re.IGNORECASE,
)

STAFF_PATTERNS = re.compile(
    r"(gặp nhân viên|người thật|"
    r"nói chuyện với người|gặp tư vấn viên|"
    r"kết nối nhân viên|chuyển nhân viên|"
    r"gọi nhân viên|cần người hỗ trợ|"
    r"admin đâu|ad đâu|shop ơi có ai không|"
    r"nhân viên đâu|cần nhân viên|nv đâu|nv ơi|"
    r"shop có ai không|ad ơi|admin ơi)",
    re.IGNORECASE,
)

STAFF_PATTERNS_NORM = re.compile(
    r"(gap nhan vien|nguoi that|"
    r"noi chuyen voi nguoi|gap tu van vien|"
    r"ket noi nhan vien|chuyen nhan vien|"
    r"goi nhan vien|can nguoi ho tro|"
    r"noi chuyen admin|gap ad)",
    re.IGNORECASE,
)

IDENTITY_PATTERNS = re.compile(
    r"(bạn là ai|em là ai|bot là ai|ai vậy|"
    r"cậu là ai|cậu là gì|bạn là gì|"
    r"giới thiệu về bạn|giới thiệu về em|"
    r"tên bạn là gì|tên em là gì|"
    r"bạn là bot gì|em là bot gì|"
    r"bạn làm được gì|em làm được gì|"
    r"bạn có thể làm|em có thể làm|có thể làm gì|làm được những gì|"
    r"hỗ trợ được gì|chức năng của bạn|bạn giúp được gì|em giúp được gì)",
    re.IGNORECASE,
)

IDENTITY_PATTERNS_NORM = re.compile(
    r"(ban la ai|em la ai|bot la ai|ai vay|"
    r"gioi thieu ve ban|gioi thieu ve em|"
    r"ten ban la gi|ten em la gi|"
    r"ban la bot gi|em la bot gi|"
    r"ban lam duoc gi|em lam duoc gi|"
    r"ban co the lam|em co the lam|co the lam gi|lam duoc nhung gi|"
    r"ho tro duoc gi|chuc nang cua ban|ban giup duoc gi|em giup duoc gi)",
    re.IGNORECASE,
)

BRAND_QUERY_PATTERNS = re.compile(
    r"(thương hiệu|brand|liên quan tới hãng|liên quan đến hãng|"
    r"sản phẩm hãng|máy hãng|điện thoại hãng|dòng của hãng|"
    r"của hãng nào|theo hãng|"
    r"hãng\s+(apple|iphone|samsung|xiaomi|oppo|vivo|realme|huawei|nokia|pixel|google)|"
    r"apple có không|apple có ko|apple có gì|apple bán gì|"
    r"samsung có không|samsung có ko|samsung có gì|"
    r"xiaomi có gì|xiaomi có không|"
    r"ip có không|ip có ko|ss có không|ss có ko|"
    r"điện thoại samsung|điện thoại apple|điện thoại iphone|"
    r"sam có gì|samsung bán gì|"
    r"google có không|pixel có không|"
    r"ô tô có bán|huawei có không|oppo có gì)",
    re.IGNORECASE,
)

BRAND_QUERY_PATTERNS_NORM = re.compile(
    r"(thuong hieu|brand|lien quan toi hang|lien quan den hang|"
    r"san pham hang|may hang|dien thoai hang|dong cua hang|"
    r"cua hang nao|theo hang|"
    r"hang\s+(apple|iphone|samsung|xiaomi|oppo|vivo|realme|huawei|nokia|pixel|google))",
    re.IGNORECASE,
)

PRODUCT_NAME_PATTERNS = re.compile(
    r"(iphone|\bip\b|\bip\s*\d{1,2}\b|\bip\d{1,2}\b|samsung|xiaomi|oppo|vivo|realme|huawei|nokia|pixel|"
    r"galaxy|redmi|note|pro|ultra|plus|max|lite|se|mini|air|fold|flip)",
    re.IGNORECASE,
)

PRODUCT_NAME_PATTERNS_NORM = re.compile(
    r"(iphone|\bip\b|\bip\s*\d{1,2}\b|\bip\d{1,2}\b|samsung|xiaomi|oppo|vivo|realme|huawei|nokia|pixel|"
    r"galaxy|redmi|note|pro|max|plus|ultra|lite|se|mini|air|fold|flip)",
    re.IGNORECASE,
)

MODEL_TYPES_PATTERNS = re.compile(
    r"(các loại|những loại|các dòng|những dòng|"
    r"có loại nào|có dòng nào|gồm những loại nào|"
    r"iphone\s*\d{1,2}\s*(có)?\s*(những|các)?\s*(loại|dòng).*(nào|gì)|"
    r"loại iphone\s*\d{1,2})",
    re.IGNORECASE,
)

MODEL_TYPES_PATTERNS_NORM = re.compile(
    r"(cac loai|nhung loai|cac dong|nhung dong|"
    r"co loai nao|co dong nao|gom nhung loai nao|"
    r"iphone\s*\d{1,2}\s*(co)?\s*(nhung|cac)?\s*(loai|dong).*(nao|gi)|"
    r"loai iphone\s*\d{1,2})",
    re.IGNORECASE,
)


def _normalize_text(value: str) -> str:
    """Normalize Vietnamese + common shorthand/typos."""
    text = (value or "").lower().strip()

    replacements = {
        "preomax": "pro max",
        "promax": "pro max",
        "promaxx": "pro max",
        "prm": "pro max",
        "ip16": "iphone 16",
        "ip15": "iphone 15",
        "ip14": "iphone 14",
        "ip13": "iphone 13",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)

    text = re.sub(r"\b(k|ko|kh|hk|hok|hong)\b", "khong", text)
    text = re.sub(r"\b(dc|đc|dk|đk)\b", "duoc", text)
    text = re.sub(r"\b(ko?z)\b", "khong", text)
    text = re.sub(r"\b(sp)\b", "san pham", text)
    text = re.sub(r"\b(dt|đt)\b", "dien thoai", text)
    text = re.sub(r"\b(bn)\b", "bao nhieu", text)
    text = re.sub(r"\b(tui|toi|t)\b", "toi", text)

    text = re.sub(r"\bip\s*(\d{1,2})\b", r"iphone \1", text)
    text = re.sub(r"\bip(\d{1,2})\b", r"iphone \1", text)
    text = re.sub(r"\biphone\s*(\d{1,2})\s*pm\b", r"iphone \1 pro max", text)
    text = re.sub(r"\biphone\s*(\d{1,2})\s*promax\b", r"iphone \1 pro max", text)

    text = re.sub(r"([a-z])(\d)", r"\1 \2", text)
    text = re.sub(r"(\d)([a-z])", r"\1 \2", text)
    text = re.sub(r"\bpro\s*max\b", "pro max", text)

    text = re.sub(r"\bip\b", "iphone", text)

    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_intent(message: str) -> str:
    """Detect intent - EXACT COPY từ chatbot_service.py (detect_intent method)."""
    msg = message.strip()
    msg_norm = _normalize_text(msg)

    def matched(raw_pat, norm_pat) -> bool:
        return bool(raw_pat.search(msg) or norm_pat.search(msg_norm))

    # === ƯU TIÊN CAO NHẤT: So sánh ===
    if matched(COMPARE_PATTERNS, COMPARE_PATTERNS_NORM):
        return "compare"

    # === Tiếp theo: Thông số kỹ thuật (check TRƯỚC consult) ===
    # Nhưng ưu tiên consult nếu có context keywords hoặc consult patterns
    has_consult_context = bool(
        re.search(r"(nên|máy|sinh viên|mình|tui|cho (mình|tôi|tui)|"
                 r"người|dùng|cần|muốn|tìm)", msg_norm)
    )
    has_consult_pattern = matched(CONSULT_PATTERNS, CONSULT_PATTERNS_NORM)
    if matched(SPEC_PATTERNS, SPEC_PATTERNS_NORM) and not (has_consult_context or has_consult_pattern):
        return "spec"

    # === Tiếp theo: Tư vấn/Recommend ===
    # Ưu tiên stock/installment nếu câu hỏi ngắn chỉ hỏi về khả năng
    has_simple_stock_question = bool(
        re.search(r"^(mua|đặt|lấy|order|ship)\s*(được|được không|ko|không)\s*(\?||$)", msg) or
        re.search(r"^(mua|dat|lay|order|ship)\s*(duoc|duoc khong|ko|khong)\s*(\?||$)", msg_norm)
    )
    if has_simple_stock_question:
        return "stock"

    if matched(CONSULT_PATTERNS, CONSULT_PATTERNS_NORM):
        return "consult"

    if matched(ORDER_CAPABILITY_PATTERNS, ORDER_CAPABILITY_PATTERNS_NORM):
        return "order_capability"

    if matched(ORDER_PATTERNS, ORDER_PATTERNS_NORM) or ORDER_CODE_PATTERN.search(msg):
        return "order"

    if matched(LIST_PRODUCT_PATTERNS, LIST_PRODUCT_PATTERNS_NORM):
        return "list_products"

    if matched(MODEL_TYPES_PATTERNS, MODEL_TYPES_PATTERNS_NORM):
        return "model_types"

    if matched(PRICE_PATTERNS, PRICE_PATTERNS_NORM):
        return "price"

    if matched(STOCK_PATTERNS, STOCK_PATTERNS_NORM):
        return "stock"

    if matched(VARIANT_PATTERNS, VARIANT_PATTERNS_NORM):
        return "variant"

    if matched(BRAND_QUERY_PATTERNS, BRAND_QUERY_PATTERNS_NORM):
        return "brand_query"

    if matched(INSTALLMENT_PATTERNS, INSTALLMENT_PATTERNS_NORM):
        return "installment"

    if matched(WARRANTY_PATTERNS, WARRANTY_PATTERNS_NORM):
        return "warranty"

    if matched(STAFF_PATTERNS, STAFF_PATTERNS_NORM):
        return "staff"

    if matched(IDENTITY_PATTERNS, IDENTITY_PATTERNS_NORM):
        return "identity"

    if matched(GREETING_PATTERNS, GREETING_PATTERNS_NORM):
        return "greeting"

    if PRODUCT_NAME_PATTERNS.search(msg) or PRODUCT_NAME_PATTERNS_NORM.search(msg_norm):
        return "product_mention"

    return "unknown"


# ============================================================
# BỘ CÂU HỎI TEST
# ============================================================

TEST_CASES = {
    "Chào hỏi": [
        "xin chào", "chào bạn", "chào shop", "hello", "hi", "hi there",
        "alo shop", "ê shop", "shop ơi", "ad ơi", "có ai không",
        "ui shop", "uii", "zô shop", "chào buổi sáng", "chào buổi tối",
        "khỏe không", "yo", "chk", "good morning",
    ],
    "Tư vấn chọn máy": [
        "tư vấn máy", "tư vấn điện thoại", "gợi ý máy", "máy nào tốt",
        "máy nào đáng mua", "nên mua máy nào", "chọn máy nào",
        "máy nào phù hợp", "recommend phone", "tư vấn giúp mình",
        "tv dum", "tv giup", "giúp tôi chọn máy", "mình cần máy mới",
        "mình muốn đổi máy", "mình thích máy nào đó", "mình tìm máy pin trâu",
        "cho mình gợi ý đi", "ngân sách 15 triệu", "budget 20 triệu",
        "dưới 10 triệu có máy nào", "máy cho sinh viên",
        "máy cho dân văn phòng", "máy chơi game ngon", "máy chụp ảnh đẹp",
        "máy pin trâu", "mình có 8 triệu", "tầm 12 triệu nên mua gì",
        "cần máy pin 5000mah",
        # Thêm các câu mới
        "sinh viên có nên mua máy này không", "có nên mua không",
        "nên mua không", "có đáng mua không", "phù hợp không",
        "hợp lý không", "tốt không", "có tốt không", "mua được không",
        "xứng đáng không", "đáng không", "review máy này",
        "đánh giá máy này", "mua hàng ở đâu", "mua online",
        "dùng thế nào", "sử dụng thế nào", "cách dùng",
        "cấu hình thế nào", "thông số kỹ thuật", "đặc điểm",
        "sinh viên nên mua điện thoại nào", "sv mua máy nào",
        "sv có nên mua sản phẩm này không",
    ],
    "Hỏi giá": [
        "giá bao nhiêu", "giá iphone 16", "giá samsung s25",
        "bao nhiêu tiền", "bao nhiêu v", "giá sao", "giá hiện tại",
        "mức giá là bao nhiêu", "máy này giá bn", "price iphone 15",
        "giá cả thế nào", "iphone 16 giá mấy", "máy này bao nhiêu",
        "bn tiền", "bao nhiu", "có bao nhiêu v", "tính giá đi",
        "xem giá", "check giá", "coi giá", "giá ổn không",
        "máy này giá ổn chưa", "có đắt không", "rẻ nhất bao nhiêu",
        "cao nhất bao nhiêu",
    ],
    "Hỏi tồn kho": [
        "còn hàng không", "còn máy không", "hết hàng chưa", "có hàng không",
        "còn sẵn không", "tình trạng còn không", "mua được không",
        "đặt được không", "còn k", "hết chưa", "in stock",
        "còn ko", "còn hem", "hết rồi hả", "còn không shop",
        "ship được không", "order được không", "lấy được không",
        "bán không", "còn bán không",
    ],
    "Hỏi biến thể": [
        "có màu gì", "mấy màu", "màu nào đẹp", "dung lượng nào",
        "có bản nào", "bao nhiêu gb", "ram bao nhiêu", "bản 128gb",
        "bản 256gb", "phiên bản nào tốt", "ip16 có mấy màu",
        "có mấy phiên bản", "mấy bản", "nên lấy bản nào",
        "bản nào ngon", "màu nào bền", "màu nào đẹp nhất",
        "storage nào", "128 hay 256", "chọn màu gì",
    ],
    "So sánh sản phẩm": [
        "so sánh iphone 16 vs iphone 15", "iphone hay samsung",
        "samsung hay iphone", "nên mua cái nào", "chọn cái nào",
        "khác gì", "so sánh", "so sánh chi tiết", "vs", "versus",
        "ưu nhược điểm", "ip16 với ip15", "ss vs ip",
        "nên lấy cái nào", "con nào ngon hơn", "con nào tốt hơn",
        "cái nào đáng mua hơn", "ip hay ss", "ss hay apple",
        "android hay ios", "android vs ios", "16 pro hay 16 pro max",
        "ultra vs pro max", "nên mua max hay pro", "max hay pro",
    ],
    "Hỏi thông số": [
        "thông số iphone 16", "pin bao nhiêu mah", "camera bao nhiêu mp",
        "chip gì", "màn hình kích thước", "ram bao nhiêu",
        "cấu hình thế nào", "spec", "sạc nhanh không",
        "có sạc không dây không", "pin mấy mah", "camera mấy mp",
        "chip gì vậy", "màn hình bao nhiêu inch", "sạc nhanh mấy w",
        "chơi game mượt không", "fps bao nhiêu", "hiệu năng thế nào",
        "có chơi game được không", "mạnh không",
    ],
    "Tra cứu đơn hàng": [
        "kiểm tra đơn hàng", "tra cứu đơn", "đơn hàng của tôi",
        "mã đơn QH250101", "order QHUN38453", "tracking", "đơn tới đâu rồi",
        "bao giờ giao", "khi nào nhận được", "vận đơn", "check đơn",
        "xem đơn", "đơn đâu rồi", "ship tới đâu rồi", "mã vận đơn",
        "đơn 38453", "QH123456", "tình trạng đơn", "đơn có giao chưa",
        "đơn có được duyệt chưa",
    ],
    "Bảo hành/Đổi trả": [
        "bảo hành bao lâu", "bảo hành ở đâu", "đổi trả như thế nào",
        "chính sách bảo hành", "bảo hành chính hãng không",
        "đổi máy được không", "lỗi thì sao", "hư thì sao",
        "bể màn thì sao", "bảo hành mấy tháng", "bh bao lâu",
        "đổi trả được không", "7 ngày đổi trả", "bảo hành free không",
        "có bảo hành không",
    ],
    "Trả góp": [
        "trả góp 0%", "mua trả góp", "trả trước bao nhiêu",
        "góp mỗi tháng bao nhiêu", "hỗ trợ trả góp không",
        "có trả góp không", "installment", "trả góp không lãi",
        "góp được không", "trả góp đi", "mua góp", "trả góp 0% lãi",
        "thanh toán góp", "góp 12 tháng", "góp 6 tháng",
    ],
    "Gặp nhân viên": [
        "gặp nhân viên", "người thật", "chuyển nhân viên",
        "gọi nhân viên", "cần người hỗ trợ", "nói chuyện với shop",
        "gặp ad", "admin đâu", "shop ơi có ai không", "cần nhân viên",
    ],
    "Liệt kê sản phẩm": [
        "có những máy nào", "danh sách sản phẩm", "shop có bán gì",
        "còn những máy nào", "các dòng iphone", "các dòng samsung",
        "sản phẩm mới", "hàng mới về", "show me phones", "list products",
        "có gì bán", "bán những gì", "đang kinh doanh gì",
        "xem sản phẩm", "liệt kê đi",
    ],
    "Hỏi theo hãng": [
        "có apple không", "samsung có không", "xiaomi có gì",
        "sản phẩm hãng apple", "điện thoại samsung", "thương hiệu apple",
        "của hãng nào", "theo hãng apple", "ip có ko", "ss có ko",
        "apple bán gì", "sam sản có gì", "ô tô có bán ko",
        "hãng google có ko", "pixel có không",
    ],
    "Nhắc sản phẩm cụ thể": [
        "iphone 16 pro max", "iphone 15", "ip16", "ip 16", "ip15",
        "iphone 14 pro", "ip 17", "iPhone 16", "IP16 Pro Max",
        "ip16 promax", "samsung s25 ultra", "s25", "galaxy s24",
        "samsung z fold", "z flip", "galaxy", "xiaomi 14",
        "redmi note 13", "oppo find x8", "vivo x100", "realme c67",
        "huawei mate 60", "nokia", "google pixel 8", "pixel 9",
    ],
    "Unknown/khác": [
        "cậu là ai", "bạn là gì", "em là bot gì", "giới thiệu về bạn",
        "faq", "câu hỏi thường gặp", "hỏi đáp", "giải đáp giúp",
        "thắc mắc", "cần hỏi gì",
    ],
}

EXPECTED_INTENTS = {
    # Chào hỏi
    "xin chào": "greeting", "chào bạn": "greeting", "chào shop": "greeting",
    "hello": "greeting", "hi": "greeting", "hi there": "greeting",
    "alo shop": "greeting", "ê shop": "greeting", "shop ơi": "greeting",
    "ad ơi": "greeting", "có ai không": "greeting",
    "ui shop": "greeting", "uii": "greeting", "zô shop": "greeting",
    "chào buổi sáng": "greeting", "chào buổi tối": "greeting",
    "khỏe không": "greeting", "yo": "greeting", "chk": "greeting",
    "good morning": "greeting",
    # Tư vấn
    "tư vấn máy": "consult", "tư vấn điện thoại": "consult",
    "gợi ý máy": "consult", "máy nào tốt": "consult",
    "máy nào đáng mua": "consult", "nên mua máy nào": "consult",
    "chọn máy nào": "consult", "máy nào phù hợp": "consult",
    "recommend phone": "consult", "tư vấn giúp mình": "consult",
    "tv dum": "consult", "tv giup": "consult", "giúp tôi chọn máy": "consult",
    "mình cần máy mới": "consult", "mình muốn đổi máy": "consult",
    "mình thích máy nào đó": "consult", "mình tìm máy pin trâu": "consult",
    "cho mình gợi ý đi": "consult", "ngân sách 15 triệu": "consult",
    "budget 20 triệu": "consult", "dưới 10 triệu có máy nào": "consult",
    "máy cho sinh viên": "consult", "máy cho dân văn phòng": "consult",
    "máy chơi game ngon": "consult", "máy chụp ảnh đẹp": "consult",
    "máy pin trâu": "consult", "mình có 8 triệu": "consult",
    "tầm 12 triệu nên mua gì": "consult", "cần máy pin 5000mah": "consult",
    # Thêm các câu mới
    "sinh viên có nên mua máy này không": "consult",
    "có nên mua không": "consult",
    "nên mua không": "consult",
    "có đáng mua không": "consult",
    "phù hợp không": "consult",
    "hợp lý không": "consult",
    "tốt không": "consult",
    "có tốt không": "consult",
    "mua được không": "consult",
    "xứng đáng không": "consult",
    "đáng không": "consult",
    "review máy này": "consult",
    "đánh giá máy này": "consult",
    "mua hàng ở đâu": "consult",
    "mua online": "consult",
    "dùng thế nào": "consult",
    "sử dụng thế nào": "consult",
    "cách dùng": "consult",
    "cấu hình thế nào": "consult",
    "thông số kỹ thuật": "consult",
    "đặc điểm": "consult",
    "sinh viên nên mua điện thoại nào": "consult",
    "sv mua máy nào": "consult",
    "sv có nên mua sản phẩm này không": "consult",
    # Giá
    "giá bao nhiêu": "price", "giá iphone 16": "price",
    "giá samsung s25": "price", "bao nhiêu tiền": "price",
    "bao nhiêu v": "price", "giá sao": "price", "giá hiện tại": "price",
    "mức giá là bao nhiêu": "price", "máy này giá bn": "price",
    "price iphone 15": "price", "giá cả thế nào": "price",
    "iphone 16 giá mấy": "price", "máy này bao nhiêu": "price",
    "bn tiền": "price", "bao nhiu": "price", "có bao nhiêu v": "price",
    "tính giá đi": "price", "xem giá": "price", "check giá": "price",
    "coi giá": "price", "giá ổn không": "price",
    "máy này giá ổn chưa": "price", "có đắt không": "price",
    "rẻ nhất bao nhiêu": "price", "cao nhất bao nhiêu": "price",
    # Tồn kho
    "còn hàng không": "stock", "còn máy không": "stock",
    "hết hàng chưa": "stock", "có hàng không": "stock",
    "còn sẵn không": "stock", "tình trạng còn không": "stock",
    "mua được không": "stock", "đặt được không": "stock",
    "còn k": "stock", "hết chưa": "stock", "in stock": "stock",
    "còn ko": "stock", "còn hem": "stock", "hết rồi hả": "stock",
    "còn không shop": "stock", "ship được không": "stock",
    "order được không": "stock", "lấy được không": "stock",
    "bán không": "stock", "còn bán không": "stock",
    # Biến thể
    "có màu gì": "variant", "mấy màu": "variant", "màu nào đẹp": "variant",
    "dung lượng nào": "variant", "có bản nào": "variant",
    "bao nhiêu gb": "variant", "ram bao nhiêu": "variant",
    "bản 128gb": "variant", "bản 256gb": "variant",
    "phiên bản nào tốt": "variant", "ip16 có mấy màu": "variant",
    "có mấy phiên bản": "variant", "mấy bản": "variant",
    "nên lấy bản nào": "variant", "bản nào ngon": "variant",
    "màu nào bền": "variant", "màu nào đẹp nhất": "variant",
    "storage nào": "variant", "128 hay 256": "variant",
    "chọn màu gì": "variant",
    # So sánh
    "so sánh iphone 16 vs iphone 15": "compare",
    "iphone hay samsung": "compare", "samsung hay iphone": "compare",
    "nên mua cái nào": "compare", "chọn cái nào": "compare",
    "khác gì": "compare", "so sánh": "compare",
    "so sánh chi tiết": "compare", "vs": "compare", "versus": "compare",
    "ưu nhược điểm": "compare", "ip16 với ip15": "compare",
    "ss vs ip": "compare", "nên lấy cái nào": "compare",
    "con nào ngon hơn": "compare", "con nào tốt hơn": "compare",
    "cái nào đáng mua hơn": "compare", "ip hay ss": "compare",
    "ss hay apple": "compare", "android hay ios": "compare",
    "android vs ios": "compare", "16 pro hay 16 pro max": "compare",
    "ultra vs pro max": "compare", "nên mua max hay pro": "compare",
    "max hay pro": "compare",
    # Thông số
    "thông số iphone 16": "spec", "pin bao nhiêu mah": "spec",
    "camera bao nhiêu mp": "spec", "chip gì": "spec",
    "màn hình kích thước": "spec", "ram bao nhiêu": "spec",
    "cấu hình thế nào": "spec", "spec": "spec",
    "sạc nhanh không": "spec", "có sạc không dây không": "spec",
    "pin mấy mah": "spec", "camera mấy mp": "spec",
    "chip gì vậy": "spec", "màn hình bao nhiêu inch": "spec",
    "sạc nhanh mấy w": "spec", "chơi game mượt không": "spec",
    "fps bao nhiêu": "spec", "hiệu năng thế nào": "spec",
    "có chơi game được không": "spec", "mạnh không": "spec",
    # Đơn hàng
    "kiểm tra đơn hàng": "order", "tra cứu đơn": "order",
    "đơn hàng của tôi": "order", "mã đơn QH250101": "order",
    "order QHUN38453": "order", "tracking": "order",
    "đơn tới đâu rồi": "order", "bao giờ giao": "order",
    "khi nào nhận được": "order", "vận đơn": "order",
    "check đơn": "order", "xem đơn": "order",
    "đơn đâu rồi": "order", "ship tới đâu rồi": "order",
    "mã vận đơn": "order", "đơn 38453": "order",
    "QH123456": "order", "tình trạng đơn": "order",
    "đơn có giao chưa": "order", "đơn có được duyệt chưa": "order",
    # Bảo hành
    "bảo hành bao lâu": "warranty", "bảo hành ở đâu": "warranty",
    "đổi trả như thế nào": "warranty", "chính sách bảo hành": "warranty",
    "bảo hành chính hãng không": "warranty", "đổi máy được không": "warranty",
    "lỗi thì sao": "warranty", "hư thì sao": "warranty",
    "bể màn thì sao": "warranty", "bảo hành mấy tháng": "warranty",
    "bh bao lâu": "warranty", "đổi trả được không": "warranty",
    "7 ngày đổi trả": "warranty", "bảo hành free không": "warranty",
    "có bảo hành không": "warranty",
    # Trả góp
    "trả góp 0%": "installment", "mua trả góp": "installment",
    "trả trước bao nhiêu": "installment",
    "góp mỗi tháng bao nhiêu": "installment",
    "hỗ trợ trả góp không": "installment", "có trả góp không": "installment",
    "installment": "installment", "trả góp không lãi": "installment",
    "góp được không": "installment", "trả góp đi": "installment",
    "mua góp": "installment", "trả góp 0% lãi": "installment",
    "thanh toán góp": "installment", "góp 12 tháng": "installment",
    "góp 6 tháng": "installment",
    # Nhân viên
    "gặp nhân viên": "staff", "người thật": "staff",
    "chuyển nhân viên": "staff", "gọi nhân viên": "staff",
    "cần người hỗ trợ": "staff", "nói chuyện với shop": "staff",
    "gặp ad": "staff", "admin đâu": "staff",
    "shop ơi có ai không": "staff", "cần nhân viên": "staff",
    # Liệt kê
    "có những máy nào": "list_products", "danh sách sản phẩm": "list_products",
    "shop có bán gì": "list_products", "còn những máy nào": "list_products",
    "các dòng iphone": "list_products", "các dòng samsung": "list_products",
    "sản phẩm mới": "list_products", "hàng mới về": "list_products",
    "show me phones": "list_products", "list products": "list_products",
    "có gì bán": "list_products", "bán những gì": "list_products",
    "đang kinh doanh gì": "list_products", "xem sản phẩm": "list_products",
    "liệt kê đi": "list_products",
    # Hãng
    "có apple không": "brand_query", "samsung có không": "brand_query",
    "xiaomi có gì": "brand_query", "sản phẩm hãng apple": "brand_query",
    "điện thoại samsung": "brand_query", "thương hiệu apple": "brand_query",
    "của hãng nào": "brand_query", "theo hãng apple": "brand_query",
    "ip có ko": "brand_query", "ss có ko": "brand_query",
    "apple bán gì": "brand_query", "sam sản có gì": "brand_query",
    "ô tô có bán ko": "brand_query", "hãng google có ko": "brand_query",
    "pixel có không": "brand_query",
    # Sản phẩm cụ thể
    "iphone 16 pro max": "product_mention", "iphone 15": "product_mention",
    "ip16": "product_mention", "ip 16": "product_mention",
    "ip15": "product_mention", "iphone 14 pro": "product_mention",
    "ip 17": "product_mention", "iPhone 16": "product_mention",
    "IP16 Pro Max": "product_mention", "ip16 promax": "product_mention",
    "samsung s25 ultra": "product_mention", "s25": "product_mention",
    "galaxy s24": "product_mention", "samsung z fold": "product_mention",
    "z flip": "product_mention", "galaxy": "product_mention",
    "xiaomi 14": "product_mention", "redmi note 13": "product_mention",
    "oppo find x8": "product_mention", "vivo x100": "product_mention",
    "realme c67": "product_mention", "huawei mate 60": "product_mention",
    "nokia": "product_mention", "google pixel 8": "product_mention",
    "pixel 9": "product_mention",
    # Unknown
    "cậu là ai": "identity", "bạn là gì": "identity",
    "em là bot gì": "identity", "giới thiệu về bạn": "identity",
    "faq": "unknown", "câu hỏi thường gặp": "unknown",
    "hỏi đáp": "unknown", "giải đáp giúp": "unknown",
    "thắc mắc": "unknown", "cần hỏi gì": "unknown",
}


def run_tests():
    results = {"summary": {"total": 0, "correct": 0, "wrong": 0, "by_category": {}}, "details": []}

    for category, cases in TEST_CASES.items():
        cat_correct = 0
        cat_wrong = 0
        cat_details = []

        for msg in cases:
            detected = detect_intent(msg)
            expected = EXPECTED_INTENTS.get(msg, "unknown")
            is_correct = detected == expected

            if is_correct:
                cat_correct += 1
            else:
                cat_wrong += 1

            cat_details.append({
                "message": msg,
                "expected": expected,
                "detected": detected,
                "correct": is_correct,
            })

            results["summary"]["total"] += 1
            if is_correct:
                results["summary"]["correct"] += 1
            else:
                results["summary"]["wrong"] += 1

        results["summary"]["by_category"][category] = {
            "total": len(cases),
            "correct": cat_correct,
            "wrong": cat_wrong,
        }
        results["details"].append({"category": category, "results": cat_details})

    return results


def generate_report(results):
    from datetime import datetime
    summary = results["summary"]
    total = summary["total"]
    correct = summary["correct"]
    wrong = summary["wrong"]
    rate = (correct / total * 100) if total > 0 else 0

    lines = [
        "# Bao Cao Test Intent Detection - Chatbot QHUN22",
        "",
        f"**Ngay test:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "",
        "## Tong Quan",
        "",
        f"| Chi so | Gia tri |",
        f"|--------|---------|",
        f"| Tong test cases | {total} |",
        f"| Dung | {correct} |",
        f"| Sai | {wrong} |",
        f"| Ty le chinh xac | {rate:.1f}% |",
        "",
        "## Chi Tiet Theo Danh Muc",
        "",
        f"| Danh muc | Tong | Dung | Sai | Ty le |",
        f"|----------|------|------|-----|-------|",
    ]

    for cat, stats in summary["by_category"].items():
        r = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        lines.append(f"| {cat} | {stats['total']} | {stats['correct']} | {stats['wrong']} | {r:.0f}% |")

    lines.append("")
    lines.append("## Chi Tiet Tung Cau Hoi")
    lines.append("")

    for detail in results["details"]:
        cat = detail["category"]
        stats = summary["by_category"][cat]

        lines.append(f"### {cat}")
        lines.append("")
        lines.append(f"- Tong: {stats['total']} | Dung: {stats['correct']} | Sai: {stats['wrong']}")
        lines.append("")

        for i, r in enumerate(detail["results"], 1):
            status = "[OK]" if r["correct"] else "[FAIL]"

            lines.append(f"#### {status} {i}. `{r['message']}`")
            lines.append("")
            lines.append(f"- **Mong doi:** `{r['expected']}`")
            lines.append(f"- **Phat hien:** `{r['detected']}`")
            if not r["correct"]:
                lines.append(f"- **Loi:** Intent khong khop!")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Ghi Chu")
    lines.append("")
    lines.append("- Test chi kiem tra pattern matching (intent detection)")
    lines.append("- Khong goi Database hay AI API")
    lines.append("- Chi danh gia do chinh xac cua regex patterns")
    lines.append("")
    lines.append(f"*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return "\n".join(lines)


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    print("=" * 60)
    print("TEST INTENT DETECTION - Chatbot QHUN22")
    print("=" * 60)
    print()

    results = run_tests()

    report = generate_report(results)

    output_path = "logtestbot.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print()
    print("=" * 60)
    print("KET QUA TEST")
    print("=" * 60)

    summary = results["summary"]
    rate = (summary["correct"] / summary["total"] * 100) if summary["total"] > 0 else 0

    print(f"[OK] Dung: {summary['correct']}/{summary['total']} ({rate:.1f}%)")
    print(f"[FAIL] Sai: {summary['wrong']}/{summary['total']}")

    print()
    print("Theo danh muc:")
    for cat, stats in summary["by_category"].items():
        r = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        status = "[OK]" if stats["wrong"] == 0 else "[FAIL]"
        print(f"  {status} {cat}: {stats['correct']}/{stats['total']} ({r:.0f}%)")

    print()
    print(f"Report da ghi vao: {output_path}")

    if summary["wrong"] > 0:
        print()
        print("=" * 60)
        print("CAC CAU HOI SAI:")
        print("=" * 60)
        for detail in results["details"]:
            for r in detail["results"]:
                if not r["correct"]:
                    print(f"  - '{r['message']}'")
                    print(f"    Mong doi: {r['expected']} | Phat hien: {r['detected']}")

    return results


if __name__ == "__main__":
    main()
