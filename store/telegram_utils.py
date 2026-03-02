"""
Telegram notification utilities for QHUN22.
"""
import threading
import requests
import logging

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = 'gan bot token vao day'
TELEGRAM_CHAT_ID = 'gan id chat vao day'
TELEGRAM_API = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'


def _send_message(text, parse_mode='HTML'):
    """Send a Telegram message. Returns message_id or None."""
    try:
        resp = requests.post(
            f'{TELEGRAM_API}/sendMessage',
            json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': text,
                'parse_mode': parse_mode,
            },
            timeout=10,
        )
        data = resp.json()
        if data.get('ok'):
            return data['result']['message_id']
    except Exception as e:
        logger.warning(f'[Telegram] Send failed: {e}')
    return None


def _delete_message(message_id):
    """Delete a Telegram message by message_id."""
    try:
        requests.post(
            f'{TELEGRAM_API}/deleteMessage',
            json={
                'chat_id': TELEGRAM_CHAT_ID,
                'message_id': message_id,
            },
            timeout=10,
        )
    except Exception as e:
        logger.warning(f'[Telegram] Delete failed: {e}')


def _send_and_delete_later(text, delay_seconds=900):
    """Send message, then auto-delete after delay_seconds (default 15 min)."""
    def _worker():
        msg_id = _send_message(text)
        if msg_id:
            timer = threading.Timer(delay_seconds, _delete_message, args=[msg_id])
            timer.daemon = True
            timer.start()
    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def _format_price(amount):
    try:
        return '{:,.0f}'.format(int(amount)).replace(',', '.') + 'đ'
    except (ValueError, TypeError):
        return str(amount)


# ==================== PUBLIC API ====================

def notify_payment_created(payment_method, order_code, username, total_amount):
    """
    VietQR/VNPay vừa được tạo -> gửi Telegram, tự xóa sau 15 phút.
    COD không gọi hàm này.
    """
    method_label = 'VietQR' if payment_method == 'vietqr' else 'VNPay'
    text = (
        f'🔔 <b>Thanh toán mới - {method_label}</b>\n'
        f'━━━━━━━━━━━━━━━━━\n'
        f'👤 Khách: <b>{username}</b>\n'
        f'💰 Số tiền: <b>{_format_price(total_amount)}</b>\n'
        f'📋 Mã đơn: <code>{order_code}</code>\n'
        f'━━━━━━━━━━━━━━━━━\n'
        f'⏳ Đang chờ thanh toán {method_label}...\n'
        f'<i>(Tin nhắn này sẽ tự xóa sau 15 phút)</i>'
    )
    _send_and_delete_later(text, delay_seconds=900)


def notify_order_success(order_code, payment_method, items):
    """
    Đơn hàng thành công (COD/VietQR/VNPay) -> gửi Telegram, KHÔNG tự xóa.
    items: list of dict { product_name, quantity, storage, color_name }
    """
    method_map = {'cod': 'COD', 'vietqr': 'VietQR', 'vnpay': 'VNPay'}
    method_label = method_map.get(payment_method, payment_method)

    product_lines = ''
    for item in items:
        name = item.get('product_name', 'Sản phẩm')
        qty = item.get('quantity', 1)
        storage = item.get('storage', '')
        color = item.get('color_name', '')

        detail_parts = []
        if qty and int(qty) > 1:
            detail_parts.append(f'x{qty}')
        if storage:
            detail_parts.append(storage)
        if color:
            detail_parts.append(color)

        detail_str = ' | '.join(detail_parts)
        product_lines += f'  • {name}'
        if detail_str:
            product_lines += f' ({detail_str})'
        product_lines += '\n'

    text = (
        f'✅ <b>ĐƠN HÀNG THÀNH CÔNG</b>\n'
        f'━━━━━━━━━━━━━━━━━\n'
        f'📋 Mã đơn: <code>{order_code}</code>\n'
        f'💳 Thanh toán: <b>{method_label}</b>\n'
        f'━━━━━━━━━━━━━━━━━\n'
        f'📦 Sản phẩm:\n'
        f'{product_lines}'
    )

    def _worker():
        _send_message(text)
    t = threading.Thread(target=_worker, daemon=True)
    t.start()
