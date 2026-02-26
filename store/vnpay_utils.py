"""
VNPay Payment Gateway Utilities
"""
import hashlib
import hmac
import urllib.parse
import requests
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
import uuid


class VNPayUtil:
    """VNPay utility class for payment processing"""
    
    @staticmethod
    def get_config():
        """Get VNPay configuration from settings"""
        return settings.VNPAY_CONFIG
    
    @staticmethod
    def generate_order_code():
        """Generate unique order code for VNPay"""
        # Format: QHun-YYYYMMDDHHMISS-RANDOM (max 50 chars)
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"QHun-{timestamp}-{random_suffix}"
    
    @staticmethod
    def calculate_checksum(data, secret_key):
        """
        Calculate VNPay checksum signature
        
        Args:
            data: Dictionary of parameters
            secret_key: VNPay secret key
            
        Returns:
            HMAC SHA512 hex string
        """
        # Sort parameters by key
        sorted_keys = sorted(data.keys())
        
        # Build hash data string (VNPay standard: quote_plus per value)
        hash_data = '&'.join(
            f"{k}={urllib.parse.quote_plus(str(data[k]))}"
            for k in sorted_keys
        )
        
        # Calculate HMAC SHA512
        signature = hmac.new(
            secret_key.encode(),
            hash_data.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return signature
    
    @staticmethod
    def build_payment_url(amount, order_code, order_description, ip_address, return_url=None):
        """
        Build VNPay payment URL
        
        Args:
            amount: Payment amount (in VND)
            order_code: Unique order code
            order_description: Order description
            ip_address: Payer IP address
            return_url: Return URL after payment
            
        Returns:
            Full VNPay payment URL
        """
        config = VNPayUtil.get_config()
        
        if return_url is None:
            return_url = config['vnp_ReturnUrl']
        
        # Build request data (CHỈ các tham số chuẩn VNPay v2.1.0)
        vnp_params = {
            'vnp_Version': config['vnp_Version'],
            'vnp_Command': config['vnp_Command'],
            'vnp_TmnCode': config['vnp_TmnCode'],
            'vnp_Amount': int(amount * 100),  # VNPay requires amount in xu (cents)
            'vnp_CreateDate': timezone.now().strftime('%Y%m%d%H%M%S'),
            'vnp_CurrCode': 'VND',
            'vnp_IpAddr': ip_address,
            'vnp_Locale': 'vn',
            'vnp_OrderInfo': order_description,
            'vnp_OrderType': config['vnp_OrderType'],
            'vnp_ReturnUrl': return_url,
            'vnp_TxnRef': order_code,
        }
        
        # Calculate checksum (KHÔNG bao gồm vnp_SecureHash)
        vnp_secure_hash = VNPayUtil.calculate_checksum(
            vnp_params,
            config['vnp_HashSecret']
        )
        
        # Build final URL: params + hash riêng
        query_parts = []
        for k in sorted(vnp_params.keys()):
            query_parts.append(f"{k}={urllib.parse.quote_plus(str(vnp_params[k]))}")
        query_string = '&'.join(query_parts)
        payment_url = f"{config['vnp_Url']}?{query_string}&vnp_SecureHash={vnp_secure_hash}"
        
        return payment_url
    
    @staticmethod
    def verify_payment_response(response_data, secret_key=None):
        """
        Verify payment response from VNPay
        
        Args:
            response_data: Dictionary of response parameters from VNPay
            secret_key: VNPay secret key (use config if None)
            
        Returns:
            Tuple (is_valid, message)
        """
        if secret_key is None:
            config = VNPayUtil.get_config()
            secret_key = config['vnp_HashSecret']
        
        # Get provided checksum
        vnp_secure_hash = response_data.get('vnp_SecureHash', '')
        if not vnp_secure_hash:
            return False, "Checksum không được cung cấp"
        
        # Create copy of response data without the checksum
        verify_data = {k: v for k, v in response_data.items() 
                      if k not in ['vnp_SecureHash', 'vnp_SecureHashType']}
        
        # Calculate expected checksum
        expected_hash = VNPayUtil.calculate_checksum(verify_data, secret_key)
        
        # Verify checksum
        if vnp_secure_hash != expected_hash:
            return False, "Checksum không hợp lệ"
        
        # Verify response code
        response_code = response_data.get('vnp_ResponseCode', '')
        if response_code != '00':
            message = VNPayUtil.get_response_message(response_code)
            return False, message
        
        return True, "OK"
    
    @staticmethod
    def get_response_message(response_code):
        """
        Get human-readable message for VNPay response code
        
        Args:
            response_code: VNPay response code
            
        Returns:
            Response message in Vietnamese
        """
        response_messages = {
            '00': 'Giao dịch thành công',
            '01': 'Giao dịch bị từ chối do các lý do liên quan đến thẻ hoặc tài khoản',
            '02': 'Giao dịch bị từ chối do liên lạc đến máy chủ của ngân hàng phát hành thẻ không thành công',
            '03': 'Merchant không hợp lệ',
            '04': 'Đơn vị tiền tệ không được hỗ trợ',
            '05': 'Giao dịch được chấp nhận, nhưng không có thông tin thanh toán do nhà cung cấp',
            '06': 'Có lỗi trong quá trình xử lý giao dịch',
            '07': 'Merchant không được phép thực hiện loại giao dịch này',
            '08': 'Interchange không được hỗ trợ',
            '09': 'Đặc tính giao dịch không được hỗ trợ',
            '10': 'Giao dịch bị từ chối do ngân hàng phát hành thẻ không hỗ trợ giao dịch này',
            '11': 'Thẻ hết hạn hoặc bị khóa',
            '12': 'Thẻ chưa được đăng ký hoặc không hỗ trợ giao dịch này trên mạng',
            '13': 'Phương thức thanh toán không hợp lệ',
            '14': 'Không có tài khoản ngân hàng hỗ trợ hoặc tài khoản bị khóa',
            '15': 'Ngân hàng từ chối giao dịch này',
            '20': 'Giao dịch từ chối do người phát hành thẻ từ chối được tham gia',
            '99': 'Người dùng hủy giao dịch',
        }
        return response_messages.get(response_code, f'Mã lỗi: {response_code}')
    
    @staticmethod
    def format_amount_for_display(amount):
        """Format amount for display (convert from xu to VND)"""
        return int(amount) // 100 if isinstance(amount, (int, str)) else amount
