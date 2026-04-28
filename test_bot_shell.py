"""
Script test chatbot QHUN22 - Chạy qua Django shell.
Sử dụng: python -c "exec(open('test_bot_shell.py').read())"
Output: Ghi log vào logtestbot.md

Bao gồm TẤT CẢ 22 sản phẩm trong hệ thống:
  iPhone 13, iPhone 14, iPhone 14 Pro Max, iPhone 15,
  iPhone 16 Plus, iPhone 16 Pro Max, iPhone 17, iPhone 17 Pro Max, iPhone Air,
  Samsung Galaxy S25 Ultra, Samsung Galaxy S26, Samsung Galaxy S26 Ultra,
  Xiaomi 14T Pro, Xiaomi 15T Pro,
  OPPO Reno15,
  Vivo Y19S,
  Honor 400 Pro,
  Tecno Camon 40 Pro,
  RedMagic 10S Pro, RedMagic 11 Pro,
  Realme 13+,
  Benco S1 Pro
"""

import os
import sys
import json
import logging
from datetime import datetime

# Disable logging noise
logging.basicConfig(level=logging.ERROR)

# ============================================================
# DANH SÁCH TẤT CẢ SẢN PHẨM TRONG HỆ THỐNG
# ============================================================

ALL_PRODUCTS = [
    # iPhone series
    "iphone 13", "iphone 14", "iphone 14 pro max",
    "iphone 15", "iphone 16 plus", "iphone 16 pro max",
    "iphone 17", "iphone 17 pro max", "iphone air",
    # Samsung
    "samsung galaxy s25 ultra", "samsung galaxy s26", "samsung galaxy s26 ultra",
    # Xiaomi
    "xiaomi 14t pro", "xiaomi 15t pro",
    # OPPO
    "oppo reno15",
    # Vivo
    "vivo y19s",
    # Honor
    "honor 400 pro",
    # Tecno
    "tecno camon 40 pro",
    # RedMagic
    "redmagic 10s pro", "redmagic 11 pro",
    # Realme
    "realme 13+",
    # Benco
    "benco s1 pro",
]

# Aliases/variations cho mỗi sản phẩm
PRODUCT_ALIASES = {
    "iphone 13": ["ip13", "ip 13", "iPhone 13"],
    "iphone 14": ["ip14", "ip 14", "iPhone 14"],
    "iphone 14 pro max": ["ip14pm", "ip 14 pro max", "iPhone 14 Pro Max", "14 promax"],
    "iphone 15": ["ip15", "ip 15", "iPhone 15"],
    "iphone 16 plus": ["ip16plus", "ip 16 plus", "iPhone 16 Plus", "16 plus"],
    "iphone 16 pro max": ["ip16pm", "ip 16 pro max", "iPhone 16 Pro Max", "16 promax"],
    "iphone 17": ["ip17", "ip 17", "iPhone 17"],
    "iphone 17 pro max": ["ip17pm", "ip 17 pro max", "iPhone 17 Pro Max", "17 promax"],
    "iphone air": ["ip air", "iphone air", "iPhone Air"],
    "samsung galaxy s25 ultra": ["ss25u", "s25 ultra", "galaxy s25 ultra", "samsung s25u"],
    "samsung galaxy s26": ["ss26", "s26", "galaxy s26", "samsung s26"],
    "samsung galaxy s26 ultra": ["ss26u", "s26 ultra", "galaxy s26 ultra", "samsung s26u"],
    "xiaomi 14t pro": ["xm14tp", "xiaomi 14t", "14t pro"],
    "xiaomi 15t pro": ["xm15tp", "xiaomi 15t", "15t pro"],
    "oppo reno15": ["op15", "reno15", "oppo reno 15"],
    "vivo y19s": ["vivo19s", "vivo y 19s", "y19s"],
    "honor 400 pro": ["honor400", "honor 400", "400 pro"],
    "tecno camon 40 pro": ["tecno40", "tecno camon", "camon 40"],
    "redmagic 10s pro": ["rm10s", "redmagic 10s", "10s pro"],
    "redmagic 11 pro": ["rm11", "redmagic 11", "11 pro"],
    "realme 13+": ["realme13", "realme 13", "13+"],
    "benco s1 pro": ["benco s1", "benco s1pro", "s1 pro"],
}

# ============================================================
# BỘ CÂU HỎI TEST - PHÂN THEO INTENTS
# ============================================================

TEST_CASES = {
    # === 1. CHÀO HỎI (15 câu) ===
    "1. Chào hỏi": [
        "xin chào",
        "chào bạn",
        "chào shop",
        "hello",
        "hi there",
        "ê shop",
        "có ai không",
        "ui shop",
        "zô shop",
        "good morning",
        "yo",
        "chk",
        "chào buổi sáng",
        "shop ơi",
        "ad ơi",
    ],

    # === 2. TƯ VẤN THEO NHU CẦU - MỖI HÃNG/LOẠI MỘT CÂU ===
    "2a. Tư vấn iPhone": [
        "tư vấn iphone",
        "máy iphone nào tốt",
        "nên mua iphone nào",
        "mình thích iphone",
        "iphone cho sinh viên",
    ],
    "2b. Tư vấn Samsung": [
        "tư vấn samsung",
        "điện thoại samsung nào tốt",
        "nên mua samsung nào",
        "samsung cho game thủ",
        "galaxy nào đáng mua",
    ],
    "2c. Tư vấn Xiaomi": [
        "tư vấn xiaomi",
        "xiaomi nào ngon",
        "nên mua xiaomi không",
        "mình thích xiaomi",
        "xiaomi cho sinh viên",
    ],
    "2d. Tư vấn OPPO": [
        "tư vấn oppo",
        "oppo reno nào tốt",
        "nên mua oppo không",
        "oppo cho chụp ảnh",
    ],
    "2e. Tư vấn Vivo": [
        "tư vấn vivo",
        "vivo nào đáng mua",
        "nên mua vivo không",
    ],
    "2f. Tư vấn Honor": [
        "tư vấn honor",
        "honor 400 pro như nào",
        "nên mua honor không",
    ],
    "2g. Tư vấn Tecno": [
        "tư vấn tecno",
        "tecno camon nào tốt",
        "nên mua tecno không",
    ],
    "2h. Tư vấn RedMagic (chơi game)": [
        "tư vấn redmagic",
        "điện thoại chơi game ngon",
        "máy chơi game giá rẻ",
        "nên mua redmagic không",
        "máy gaming nào tốt",
    ],
    "2i. Tư vấn Realme": [
        "tư vấn realme",
        "realme nào ngon",
        "nên mua realme không",
    ],
    "2j. Tư vấn Benco": [
        "tư vấn benco",
        "benco s1 pro như nào",
        "nên mua benco không",
    ],

    # === 3. HỎI GIÁ - MỖI SẢN PHẨM MỘT CÂU ===
    "3a. Hỏi giá iPhone": [
        "giá iphone 13",
        "iphone 14 pro max giá bao nhiêu",
        "giá iphone 16 pro max",
        "iphone 17 giá mấy",
        "iphone air bao nhiêu tiền",
    ],
    "3b. Hỏi giá Samsung": [
        "giá samsung galaxy s25 ultra",
        "samsung s26 giá bao nhiêu",
        "galaxy s26 ultra mấy tiền",
    ],
    "3c. Hỏi giá Xiaomi": [
        "giá xiaomi 14t pro",
        "xiaomi 15t pro bao nhiêu",
    ],
    "3d. Hỏi giá OPPO/Vivo/Honor/Tecno/RedMagic/Realme/Benco": [
        "giá oppo reno15",
        "vivo y19s giá bao nhiêu",
        "honor 400 pro giá mấy",
        "tecno camon 40 pro bao nhiêu",
        "redmagic 10s pro giá bao nhiêu",
        "redmagic 11 pro mấy tiền",
        "realme 13+ giá bao nhiêu",
        "benco s1 pro giá mấy",
    ],

    # === 4. HỎI TỒN KHO - NHIỀU HÃNG ===
    "4a. Hỏi tồn kho iPhone": [
        "còn iphone 13 không",
        "iphone 14 pro max còn hàng không",
        "ip16 plus còn bán không",
        "iphone 17 pro max còn hàng chưa",
    ],
    "4b. Hỏi tồn kho Samsung": [
        "samsung galaxy s25 ultra còn không",
        "galaxy s26 còn hàng chưa",
        "s26 ultra còn bán không",
    ],
    "4c. Hỏi tồn kho Android khác": [
        "xiaomi 14t pro còn không",
        "oppo reno15 còn hàng không",
        "redmagic 10s pro còn bán không",
        "realme 13+ còn không",
        "benco s1 pro còn hàng chưa",
    ],

    # === 5. SO SÁNH - CROSS-BRAND ===
    "5a. So sánh iPhone vs iPhone": [
        "so sánh iphone 14 và iphone 15",
        "iphone 16 plus vs iphone 16 pro max",
        "nên mua iphone 15 hay iphone 17",
        "ip13 hay ip14 tốt hơn",
        "iphone 17 pro max vs iphone air",
    ],
    "5b. So sánh iPhone vs Samsung": [
        "iphone hay samsung",
        "nên mua iphone hay samsung",
        "samsung s25 ultra vs iphone 16 pro max",
        "ip vs ss cái nào tốt hơn",
        "android hay ios nên dùng",
    ],
    "5c. So sánh Samsung vs Android khác": [
        "samsung hay xiaomi",
        "galaxy s25 ultra hay xiaomi 14t pro",
        "nên mua samsung hay oppo",
        "redmagic hay rog phone",
    ],
    "5d. So sánh gaming phones": [
        "redmagic 10s pro vs redmagic 11 pro",
        "nên mua redmagic 11 pro không",
        "điện thoại gaming nào ngon nhất",
    ],

    # === 6. THÔNG SỐ KỸ THUẬT - NHIỀU SẢN PHẨM ===
    "6a. Thông số iPhone": [
        "thông số iphone 16 pro max",
        "iphone 17 pin bao nhiêu mah",
        "iphone 15 chip gì",
        "camera iphone 14 pro max bao nhiêu mp",
    ],
    "6b. Thông số Samsung": [
        "thông số samsung galaxy s25 ultra",
        "s26 ultra màn hình bao nhiêu inch",
        "galaxy s25 ultra pin mấy mah",
    ],
    "6c. Thông số Android khác": [
        "thông số xiaomi 14t pro",
        "redmagic 11 pro chip gì",
        "oppo reno15 camera bao nhiêu mp",
        "honor 400 pro pin bao nhiêu",
    ],

    # === 7. BIẾN THỂ/MÀU/DUNG LƯỢNG ===
    "7. Hỏi biến thể": [
        "iphone 16 pro max có mấy màu",
        "samsung s25 ultra có mấy màu",
        "xiaomi 14t pro có bản nào",
        "iphone 14 pro max dung lượng nào",
        "redmagic 10s pro có bản 512gb không",
        "màu nào đẹp cho iphone 17",
    ],

    # === 8. TRẢ GÓP ===
    "8. Trả góp": [
        "trả góp iphone 16 pro max",
        "mua samsung s25 ultra trả góp được không",
        "góp điện thoại mỗi tháng bao nhiêu",
        "trả góp 0% có không",
        "hỗ trợ trả góp không",
    ],

    # === 9. BẢO HÀNH/ĐỔI TRẢ ===
    "9. Bảo hành": [
        "bảo hành bao lâu",
        "đổi trả được không",
        "7 ngày đổi trả có không",
        "bảo hành chính hãng không",
        "lỗi thì sao",
    ],

    # === 10. ĐƠN HÀNG ===
    "10. Đơn hàng": [
        "kiểm tra đơn hàng",
        "QH250101",
        "đơn của tôi tới đâu rồi",
        "bao giờ giao",
        "tra cứu đơn hàng",
    ],

    # === 11. GẶP NHÂN VIÊN ===
    "11. Gặp nhân viên": [
        "gặp nhân viên",
        "chuyển người thật",
        "cần nhân viên hỗ trợ",
        "shop ơi có ai không",
    ],

    # === 12. DANH SÁCH SẢN PHẨM ===
    "12. Liệt kê sản phẩm": [
        "có những máy nào",
        "danh sách sản phẩm",
        "shop có bán gì",
        "các dòng iphone hiện có",
        "samsung có máy nào",
        "hàng mới về",
    ],

    # === 13. HÃNG SẢN XUẤT ===
    "13. Hỏi theo hãng": [
        "có iphone không",
        "samsung có không",
        "xiaomi có bán gì",
        "apple có máy nào",
        "oppo có những dòng nào",
        "điện thoại hãng nào tốt",
    ],

    # === 14. SẢN PHẨM CỤ THỂ - TỪNG HÃNG ===
    "14a. Nhắc iPhone cụ thể": [
        "iphone 13",
        "ip 14",
        "iphone 16 pro max",
        "iPhone 17",
        "iphone air",
    ],
    "14b. Nhắc Samsung cụ thể": [
        "samsung galaxy s25 ultra",
        "galaxy s26",
        "samsung s26 ultra",
    ],
    "14c. Nhắc Xiaomi/OPPO/Vivo cụ thể": [
        "xiaomi 14t pro",
        "xiaomi 15t pro",
        "oppo reno15",
        "vivo y19s",
        "honor 400 pro",
    ],
    "14d. Nhắc Tecno/RedMagic/Realme/Benco cụ thể": [
        "tecno camon 40 pro",
        "redmagic 10s pro",
        "redmagic 11 pro",
        "realme 13+",
        "benco s1 pro",
    ],

    # === 15. MODEL TYPES - CÁC DÒNG ===
    "15. Hỏi các loại dòng": [
        "iphone 16 có những loại nào",
        "dòng iphone 17 có gì",
        "samsung s series có mấy loại",
        "xiaomi t series có máy nào",
    ],

    # === 16. XÁC NHẬN MUA / CONFIRM ===
    "16. Xác nhận mua": [
        "vậy lấy iphone 14",
        "ok mua samsung s25 ultra",
        "đồng ý mua iphone 17 pro max",
        "vậy thì lấy redmagic 11 pro",
        "ngon, mình lấy oppo reno15",
        "nếu vậy mua honor 400 pro",
        "chốt được rồi, lấy iphone 16 plus",
    ],

    # === 17. NGÂN SÁCH / BUDGET ===
    "17. Tư vấn theo ngân sách": [
        "dưới 10 triệu nên mua máy nào",
        "ngân sách 15 triệu",
        "tầm 20 triệu mua gì",
        "máy dưới 8 triệu nào ngon",
        "có máy nào dưới 5 triệu không",
        "25 triệu nên mua gì",
    ],

    # === 18. CHỨC NĂNG ĐẶC BIỆT ===
    "18. Chức năng đặc biệt": [
        "máy pin trâu nhất",
        "điện thoại chụp ảnh đẹp nhất",
        "máy chơi game mạnh nhất",
        "màn hình đẹp nhất",
        "máy selfie đẹp nhất",
        "điện thoại nào mỏng nhẹ",
    ],

    # === 19. IDENTITY / UNKNOWN ===
    "19. Identity/khác": [
        "cậu là ai",
        "giới thiệu về bạn",
        "câu hỏi thường gặp",
        "hỏi đáp",
    ],
}


# ============================================================
# HÀM TEST
# ============================================================

def count_tests():
    return sum(len(v) for v in TEST_CASES.values())


def run_tests():
    """Chạy tất cả tests và trả về kết quả."""
    from store.chatbot_orchestrator import HybridChatbotOrchestrator

    orchestrator = HybridChatbotOrchestrator()

    results = {
        "summary": {"total": 0, "success": 0, "failed": 0, "by_category": {}},
        "details": [],
    }

    for category, cases in TEST_CASES.items():
        cat_results = []
        for msg in cases:
            try:
                result = orchestrator.process_message(msg)
                cat_results.append({
                    "message": msg,
                    "response": result.get("message", ""),
                    "intent": result.get("intent", "unknown"),
                    "engine": result.get("engine", "unknown"),
                    "source": result.get("source", "unknown"),
                    "has_products": bool(result.get("products") or result.get("product_cards")),
                    "has_suggestions": bool(result.get("suggestions")),
                    "success": True,
                    "error": None,
                })
                results["summary"]["success"] += 1
            except Exception as e:
                cat_results.append({
                    "message": msg,
                    "response": "",
                    "intent": "ERROR",
                    "engine": "ERROR",
                    "source": "ERROR",
                    "has_products": False,
                    "has_suggestions": False,
                    "success": False,
                    "error": str(e),
                })
                results["summary"]["failed"] += 1
            results["summary"]["total"] += 1

        results["summary"]["by_category"][category] = {
            "total": len(cases),
            "success": sum(1 for r in cat_results if r["success"]),
            "failed": sum(1 for r in cat_results if not r["success"]),
        }
        results["details"].append({"category": category, "results": cat_results})

    return results


def generate_report(results):
    """Tạo báo cáo Markdown."""
    summary = results["summary"]
    total = summary["total"]
    success = summary["success"]
    failed = summary["failed"]
    rate = (success / total * 100) if total > 0 else 0

    lines = [
        "# Bao Cao Test Chatbot QHUN22",
        "",
        f"**Ngay test:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "",
        "## Danh Sach San Pham Trong He Thong",
        "",
        "| STT | San pham | Aliases |",
        "|-----|---------|---------|",
    ]

    aliases_flat = {a: k for k, v in PRODUCT_ALIASES.items() for a in v}
    for i, (prod, aliases) in enumerate(sorted(PRODUCT_ALIASES.items()), 1):
        lines.append(f"| {i} | `{prod}` | `{'`, `'.join(aliases)}` |")

    lines.append("")
    lines.append("## Tong Quan")
    lines.append("")
    lines.append(f"| Chi so | Gia tri |")
    lines.append(f"|--------|---------|")
    lines.append(f"| Tong test cases | {total} |")
    lines.append(f"| Thanh cong | {success} |")
    lines.append(f"| That bai | {failed} |")
    lines.append(f"| Ty le thanh cong | {rate:.1f}% |")
    lines.append("")
    lines.append("## Chi Tiet Theo Danh Muc")
    lines.append("")
    lines.append(f"| Danh muc | Tong | Thanh cong | That bai | Ty le |")
    lines.append(f"|----------|------|-----------|----------|-------|")

    for cat, stats in summary["by_category"].items():
        r = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
        lines.append(f"| {cat} | {stats['total']} | {stats['success']} | {stats['failed']} | {r:.0f}% |")

    lines.append("")
    lines.append("## Chi Tiet Tung Cau Hoi")
    lines.append("")

    for detail in results["details"]:
        cat = detail["category"]
        stats = summary["by_category"][cat]

        lines.append(f"### {cat}")
        lines.append("")
        lines.append(f"- Tong: {stats['total']} | Thanh cong: {stats['success']} | That bai: {stats['failed']}")
        lines.append("")

        for i, r in enumerate(detail["results"], 1):
            status = "[OK]" if r["success"] else "[FAIL]"

            lines.append(f"#### {status} {i}. `{r['message']}`")
            lines.append("")

            if r["success"]:
                lines.append(f"- **Intent:** `{r['intent']}`")
                lines.append(f"- **Engine:** `{r['engine']}`")
                lines.append(f"- **Source:** `{r['source']}`")
                lines.append(f"- **Co san pham:** {'Co' if r['has_products'] else 'Khong'}")
                lines.append(f"- **Co goi y:** {'Co' if r['has_suggestions'] else 'Khong'}")
                lines.append("")
                lines.append("**Phan hoi:**")
                lines.append('```')
                resp = r["response"][:500] if r["response"] else "(trong)"
                lines.append(resp)
                lines.append('```')
            else:
                lines.append(f"- **Loi:** `{r['error']}`")

            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Ghi Chu")
    lines.append("")
    lines.append("- Engine `django_local` = Xu ly bang local (ChatbotService)")
    lines.append("- Engine `ai_pipeline` = Xu ly bang AI (RAG pipeline)")
    lines.append("- Engine `django_local_fallback` = Fallback tu AI ve local")
    lines.append("- Source `rule` = Xu ly bang luat (khong goi Claude API)")
    lines.append("- Source `claude` = Xu ly bang Claude API")
    lines.append("")
    lines.append(f"*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import os as _os
    import django
    _os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    print("=" * 60)
    print("TEST BOT QHUN22 - Chatbot Test Suite (Day Du)")
    print("=" * 60)
    print()

    total = count_tests()
    print(f"Tong so test cases: {total}")
    print()
    print("Dang chay tests...")

    results = run_tests()

    # Generate report
    report = generate_report(results)

    # Write to file
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logtestbot.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print()
    print("=" * 60)
    print("KET QUA TEST")
    print("=" * 60)

    summary = results["summary"]
    rate = (summary["success"] / summary["total"] * 100) if summary["total"] > 0 else 0

    print(f"[OK] Thanh cong: {summary['success']}/{summary['total']} ({rate:.1f}%)")
    print(f"[FAIL] That bai: {summary['failed']}/{summary['total']}")

    print()
    print("Theo danh muc:")
    for cat, stats in summary["by_category"].items():
        r = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  - {cat}: {stats['success']}/{stats['total']} ({r:.0f}%)")

    print()
    print(f"Report da ghi vao: {output_path}")

    if summary["failed"] > 0:
        print()
        print("=" * 60)
        print("CAC CAU HOI THAT BAI:")
        print("=" * 60)
        for detail in results["details"]:
            for r in detail["results"]:
                if not r["success"]:
                    print(f"  - '{r['message']}'")
                    print(f"    Loi: {r['error']}")
