"""
Authentication Views (login, register, OTP, profile) - QHUN22 Store
Auto-generated from views.py
"""
import os
import json
import uuid
import random
import time
import traceback
import requests
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.db import models
from django.db.models import Q, Count, Sum, Max
from django.utils import timezone
from django.urls import reverse
import datetime



def verify_turnstile(token):
    """
    Xác minh Cloudflare Turnstile token
    """
    try:
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={
                'secret': settings.CLOUDFLARE_TURNSTILE_SECRET_KEY,
                'response': token,
            },
            timeout=10
        )
        result = response.json()
        return result.get('success', False)
    except Exception as e:
        print(f"Turnstile verification error: {e}")
        return False



def send_otp_view(request):
    """
    Gửi OTP qua email (AJAX)
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            return JsonResponse({'status': 'error', 'message': 'Thiếu email'})
        
        # Kiểm tra email đã tồn tại chưa
        from store.models import CustomUser
        if CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Email đã tồn tại trong hệ thống! Vui lòng sử dụng email khác.'})
        
        # Tạo OTP 5 chữ số
        otp = str(random.randint(10000, 99999))
        
        # Lưu vào session
        request.session['otp'] = otp
        request.session['otp_email'] = email
        request.session['otp_created_at'] = int(time.time())  # Thời điểm tạo OTP
        request.session['otp_expire'] = 300  # 5 phút (để tính toán sau)
        
        # Gửi email qua SendGrid
        api_key = os.getenv('SENDGRID_API_KEY', '')
        from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@qhun22.com')

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
            <div style="background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #333; text-align: center;">Xác minh tài khoản QHUN22</h2>
                <p style="color: #666;">Mã OTP của bạn là:</p>
                <div style="background: #f0f0f0; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #333;">{otp}</div>
                <p style="color: #999; font-size: 12px;">Mã có hiệu lực trong 5 phút. Vui lòng không chia sẻ mã này cho ai.</p>
            </div>
        </div>
        """

        data = {
            "personalizations": [{
                "to": [{"email": email}],
                "subject": "Xác minh OTP - QHUN22"
            }],
            "from": {"email": from_email},
            "content": [{
                "type": "text/html",
                "value": html_body
            }]
        }
        
        try:
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=data,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code in [200, 201, 202]:
                return JsonResponse({'status': 'success', 'message': 'OTP_SENT'})
            else:
                return JsonResponse({'status': 'error', 'message': f'Gửi email thất bại: {response.status_code}'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
            return JsonResponse({'status': 'error', 'message': 'Yêu cầu không hợp lệ'})



def login_view(request):
    """
    Đăng nhập người dùng với Turnstile verification
    """
    # Nếu đã đăng nhập thì chuyển về trang chủ
    if request.user.is_authenticated:
        return redirect('store:home')
    
    if request.method == 'POST':
        # Lấy email để đăng nhập
        email = request.POST.get('username')  # Vẫn dùng field username trong form nhưng là email
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        # Tìm user theo email - CustomUser dùng email làm USERNAME_FIELD
        from store.models import CustomUser
        try:
            user_obj = CustomUser.objects.get(email=email)
            username = user_obj.username  # Sẽ là None nhưng authenticate cần
        except CustomUser.DoesNotExist:
            username = email
        
        # turnstile_token = request.POST.get('cf-turnstile-response')
        
        # Cloudflare Turnstile - Enable when deploying to production
        # if not turnstile_token:
        #     messages.error(request, 'Vui lòng xác minh bạn không phải robot!')
        #     return render(request, 'store/login.html')
        
        # # Xác minh Turnstile trước khi authenticate
        # if not verify_turnstile(turnstile_token):
        #     messages.error(request, 'Xác minh thất bại. Vui lòng thử lại!')
        #     return render(request, 'store/login.html')
        
        # Authenticate với email
        user = authenticate(request, username=email, password=password)
        if user is not None:
            # Xử lý remember me
            if remember_me:
                request.session.set_expiry(60 * 60 * 24 * 7)  # 7 days
            else:
                request.session.set_expiry(0)  # Session hết khi đóng trình duyệt
            
            login(request, user)
            messages.success(request, 'Đăng nhập thành công!')
            return redirect('store:home')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng!')
    
    return render(request, 'store/login.html')



def profile(request):
    """
    Trang thông tin tài khoản người dùng
    """
    from store.models import Order
    from store.models import PasswordHistory
    from store.models import Address
    from django.db.models import Sum
    
    context = {}
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        # Chỉ đếm đơn đã giao thành công (không tính hủy, chờ xử lý, đang giao)
        total_orders = orders.filter(status='delivered').count()
        total_spent_raw = orders.filter(status='delivered').aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Đơn đã hoàn tiền (refund history)
        refunded_orders = orders.filter(status='cancelled', refund_status='completed')
        
        # Format total_spent for display
        total_spent = '{:,.0f}'.format(total_spent_raw).replace(',', '.')
        
        # Password change history
        password_history = PasswordHistory.objects.filter(user=request.user)
        
        # Address book
        addresses = Address.objects.filter(user=request.user)
        
        # Handle change password
        if request.method == 'POST' and request.POST.get('action') == 'change_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not request.user.check_password(current_password):
                messages.error(request, 'Mật khẩu hiện tại không đúng!')
            elif new_password != confirm_password:
                messages.error(request, 'Mật khẩu mới không khớp!')
            elif len(new_password) < 6:
                messages.error(request, 'Mật khẩu mới phải có ít nhất 6 ký tự!')
            else:
                request.user.set_password(new_password)
                request.user.save()
                # Save password change history
                ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
                if ip and ',' in ip:
                    ip = ip.split(',')[0].strip()
                PasswordHistory.objects.create(
                    user=request.user,
                    ip_address=ip or None,
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                )
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Đổi mật khẩu thành công!')
                return redirect('store:profile')
        
        # Voucher khả dụng cho user
        from store.models import Coupon, CouponUsage
        all_coupons = Coupon.objects.filter(is_active=True)
        available_coupons = []
        for cp in all_coupons:
            if cp.is_expired():
                continue
            # Kiểm tra giới hạn per-user
            if cp.usage_limit > 0:
                user_used = CouponUsage.objects.filter(coupon=cp, user=request.user).count()
                if user_used >= cp.usage_limit:
                    continue
            if cp.target_type == 'single':
                user_email = request.user.email.lower() if request.user.email else ''
                target_email = cp.target_email.lower() if cp.target_email else ''
                verified_student = (getattr(request.user, 'verified_student_email', None) or '').lower()
                verified_teacher = (getattr(request.user, 'verified_teacher_email', None) or '').lower()
                is_match = (
                    user_email == target_email or
                    user_email == verified_student or
                    user_email == verified_teacher or
                    target_email == verified_student or
                    target_email == verified_teacher
                )
                if not is_match:
                    continue
            available_coupons.append(cp)
        
        context.update({
            'orders': orders,
            'total_orders': total_orders,
            'total_spent': total_spent,
            'total_spent_raw': total_spent_raw,
            'password_history': password_history,
            'addresses': addresses,
            'refunded_orders': refunded_orders,
            'available_coupons': available_coupons,
        })
        
        # Lấy voucher Edu cho người dùng đã xác thực
        if request.user.is_student_verified or request.user.is_teacher_verified:
            edu_email = request.user.verified_student_email or request.user.verified_teacher_email
            edu_voucher = Coupon.objects.filter(
                target_type='single',
                target_email__iexact=edu_email,
                is_active=True
            ).first()
            
            if edu_voucher:
                if edu_voucher.is_expired():
                    edu_voucher_status = 'expired'
                else:
                    user_used_edu = CouponUsage.objects.filter(coupon=edu_voucher, user=request.user).count()
                    if edu_voucher.usage_limit > 0 and user_used_edu >= edu_voucher.usage_limit:
                        edu_voucher_status = 'used'
                    else:
                        edu_voucher_status = 'available'
            else:
                edu_voucher_status = None
                
            context.update({
                'edu_voucher': edu_voucher,
                'edu_voucher_status': edu_voucher_status,
            })
    
    return render(request, 'store/profile.html', context)



def register_view(request):
    """
    Đăng ký tài khoản mới với OTP verification
    """
    # Nếu đã đăng nhập thì chuyển về trang chủ
    if request.user.is_authenticated:
        return redirect('store:home')
    
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        otp_input = request.POST.get('otp')
        
        # Kiểm tra các trường không rỗng
        if not fullname or not email or not phone or not password or not confirm_password or not otp_input:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin!')
            return render(request, 'store/register.html')
        
        # Kiểm tra mật khẩu khớp
        if password != confirm_password:
            messages.error(request, 'Mật khẩu không khớp!')
            return render(request, 'store/register.html')
        
        # Kiểm tra OTP
        session_otp = request.session.get('otp')
        session_email = request.session.get('otp_email')
        session_created_at = request.session.get('otp_created_at', 0)
        session_expire = request.session.get('otp_expire', 300)
        
        # Kiểm tra OTP hết hạn
        if not session_otp or session_email != email or session_otp != otp_input or int(time.time()) > (session_created_at + session_expire):
            messages.error(request, 'OTP không hợp lệ hoặc đã hết hạn!')
            return render(request, 'store/register.html')
        
        # Kiểm tra email đã tồn tại chưa
        from store.models import CustomUser
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email đã được sử dụng!')
            return render(request, 'store/register.html')
        
        # Tạo user mới với email và phone
        user = CustomUser.objects.create_user(
            password=password,
            email=email,
            last_name=fullname.upper(),  # Lưu họ tên vào last_name (viết hoa)
            phone=phone
        )
        # Đảm bảo user thường không có OAuth flag
        user.is_oauth_user = False
        user.save()
        
        # Xóa OTP khỏi session
        request.session.pop('otp', None)
        request.session.pop('otp_email', None)
        request.session.pop('otp_expire', None)
        
        messages.success(request, 'Đăng ký thành công! Vui lòng đăng nhập.')
        return redirect('store:login')
    
    return render(request, 'store/register.html')



def forgot_password_view(request):
    """
    Trang quên mật khẩu
    """
    # Nếu đã đăng nhập thì chuyển về trang chủ
    if request.user.is_authenticated:
        return redirect('store:home')
    
    return render(request, 'store/forgot_password.html')



def send_otp_forgot_password_view(request):
    """
    Gửi OTP cho quên mật khẩu (AJAX)
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            return JsonResponse({'status': 'error', 'message': 'Thiếu email'})
        
        # Kiểm tra email có tồn tại trong hệ thống không
        from store.models import CustomUser
        if not CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Email không tồn tại trong hệ thống!'})
        
        # Tạo OTP 5 chữ số
        otp = str(random.randint(10000, 99999))
        
        # Lưu vào session với prefix để tránh xung đột với OTP đăng ký
        request.session['fp_otp'] = otp
        request.session['fp_otp_email'] = email
        request.session['fp_otp_created_at'] = int(time.time())
        request.session['fp_otp_expire'] = 300  # 5 phút
        
        # Gửi email qua SendGrid
        api_key = os.getenv('SENDGRID_API_KEY', '')
        from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@qhun22.com')

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
            <div style="background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #d9534f; text-align: center;">Đặt lại mật khẩu QHUN22</h2>
                <p style="color: #666;">Mã OTP của bạn để đặt lại mật khẩu là:</p>
                <div style="background: #f0f0f0; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #333;">{otp}</div>
                <p style="color: #999; font-size: 12px;">Mã có hiệu lực trong 5 phút. Nếu bạn không yêu cầu mã này, vui lòng bỏ qua.</p>
            </div>
        </div>
        """

        data = {
            "personalizations": [{
                "to": [{"email": email}],
                "subject": "OTP Quên Mật Khẩu - QHUN22"
            }],
            "from": {"email": from_email},
            "content": [{
                "type": "text/html",
                "value": html_body
            }]
        }
        
        try:
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=data,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code in [200, 201, 202]:
                return JsonResponse({'status': 'success', 'message': 'OTP_SENT'})
            else:
                return JsonResponse({'status': 'error', 'message': f'Gửi email thất bại: {response.status_code}'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
            return JsonResponse({'status': 'error', 'message': 'Yêu cầu không hợp lệ'})



def verify_otp_forgot_password_view(request):
    """
    Xác minh OTP cho quên mật khẩu (AJAX)
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        otp_input = request.POST.get('otp')
        
        if not email or not otp_input:
            return JsonResponse({'status': 'error', 'message': 'Thiếu tham số'})
        
        # Kiểm tra OTP
        session_otp = request.session.get('fp_otp')
        session_email = request.session.get('fp_otp_email')
        session_created_at = request.session.get('fp_otp_created_at', 0)
        session_expire = request.session.get('fp_otp_expire', 300)
        
        # Kiểm tra OTP hết hạn
        if not session_otp or session_email != email or session_otp != otp_input or int(time.time()) > (session_created_at + session_expire):
            return JsonResponse({'status': 'error', 'message': 'OTP không hợp lệ hoặc đã hết hạn!'})
        
        # OTP đúng, lưu trạng thái xác minh
        request.session['fp_verified'] = True
        
        return JsonResponse({'status': 'success', 'message': 'OTP verified'})



def reset_password_view(request):
    """
    Đặt lại mật khẩu (AJAX)
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        
        if not email or not new_password:
            return JsonResponse({'status': 'error', 'message': 'Thiếu tham số'})
        
        # Kiểm tra đã xác minh OTP chưa
        if not request.session.get('fp_verified') or request.session.get('fp_otp_email') != email:
            return JsonResponse({'status': 'error', 'message': 'Vui lòng xác minh OTP trước!'})
        
        # Cập nhật mật khẩu
        from store.models import CustomUser
        try:
            user = CustomUser.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            
            # Xóa session
            request.session.pop('fp_otp', None)
            request.session.pop('fp_otp_email', None)
            request.session.pop('fp_otp_created_at', None)
            request.session.pop('fp_otp_expire', None)
            request.session.pop('fp_verified', None)
            
            return JsonResponse({'status': 'success', 'message': 'Đặt lại mật khẩu thành công'})
        except CustomUser.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy người dùng'})
    
            return JsonResponse({'status': 'error', 'message': 'Yêu cầu không hợp lệ'})

@csrf_exempt
@require_POST
@login_required
def send_verification_code(request):
    """Gửi mã OTP 6 số tới email .edu.vn để xác thực Student/Teacher."""
    email = request.POST.get('email', '').strip().lower()

    if not email:
        return JsonResponse({'success': False, 'message': 'Vui lòng nhập email'})
    if not email.endswith('.edu.vn'):
        return JsonResponse({'success': False, 'message': 'Chỉ chấp nhận email .edu.vn'})

    # Kiểm tra email đã được xác thực bởi người khác chưa
    from django.contrib.auth import get_user_model
    User = get_user_model()
    existing_user = User.objects.filter(
        Q(verified_student_email__iexact=email) | Q(verified_teacher_email__iexact=email)
    ).exclude(id=request.user.id).first()
    
    if existing_user:
        return JsonResponse({'success': False, 'message': 'Email này đã được xác thực bởi tài khoản khác.'})

    # Tạo OTP 6 chữ số
    import random, time as _time
    otp = str(random.randint(100000, 999999))

    # Lưu vào session (hết hạn sau 5 phút)
    request.session['edu_otp'] = otp
    request.session['edu_otp_email'] = email
    request.session['edu_otp_created_at'] = int(_time.time())

    # Debug: in OTP ra console để test (nếu không có SendGrid)
    print(f"=== OTP for {email}: {otp} ===")

    # Gửi email qua SendGrid
    api_key = os.getenv('SENDGRID_API_KEY', '')
    from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@qhun22.com')

    # Debug: kiểm tra API key
    if not api_key:
        import logging
        logging.getLogger(__name__).warning('SENDGRID_API_KEY not configured')

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
        <div style="background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #5bc0de; text-align: center;">Xác thực Student/Teacher - QHUN22</h2>
            <p style="color: #666;">Mã xác thực của bạn là:</p>
            <div style="background: #e8f4fd; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #A9CCF0;">{otp}</div>
            <p style="color: #999; font-size: 12px;">Mã có hiệu lực trong 5 phút. Vui lòng không chia sẻ mã này cho ai.</p>
        </div>
    </div>
    """

    payload = {
        "personalizations": [{"to": [{"email": email}], "subject": "Mã xác thực Student/Teacher - QHUN22"}],
        "from": {"email": from_email},
        "content": [{"type": "text/html", "value": html_body}]
    }

    try:
        resp = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=10
        )
        if resp.status_code in [200, 201, 202]:
            return JsonResponse({'success': True, 'message': f'Đã gửi mã xác thực tới {email}. Vui lòng kiểm tra hộp thư.'})
        else:
            # Debug: trả về thông tin lỗi
            import logging
            logging.getLogger(__name__).error(f'SendGrid error: {resp.status_code} - {resp.text}')
            return JsonResponse({'success': False, 'message': f'Không thể gửi email. Mã lỗi: {resp.status_code}'})
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception(f'SendGrid connection error: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Lỗi kết nối: {str(e)}'})



@require_POST
@login_required
def verify_code(request):
    """Xác thực mã OTP và đánh dấu tài khoản là Student hoặc Teacher."""
    import time as _time

    email = request.POST.get('email', '').strip().lower()
    code = request.POST.get('code', '').strip()

    if not email or not code:
        return JsonResponse({'success': False, 'message': 'Thiếu thông tin xác thực'})

    session_otp = request.session.get('edu_otp')
    session_email = request.session.get('edu_otp_email', '')
    created_at = request.session.get('edu_otp_created_at', 0)

    # Kiểm tra hết hạn 5 phút
    if int(_time.time()) - created_at > 300:
        return JsonResponse({'success': False, 'message': 'Mã xác thực đã hết hạn. Vui lòng gửi lại.'})

    if session_email != email:
        return JsonResponse({'success': False, 'message': 'Email không khớp. Vui lòng gửi lại mã.'})

    if session_otp != code:
        return JsonResponse({'success': False, 'message': 'Mã xác thực không đúng.'})

    # Xác thực thành công — xác định student hay teacher
    # Convention: nếu email chứa "gv.", "giang.vien", "lecturer", "teacher" → teacher, còn lại → student
    teacher_keywords = ['gv.', 'gv@', 'giangvien', 'giang.vien', 'lecturer', 'teacher', 'faculty']
    is_teacher = any(kw in email for kw in teacher_keywords)

    user = request.user
    if is_teacher:
        user.is_teacher_verified = True
        user.verified_teacher_email = email
    else:
        user.is_student_verified = True
        user.verified_student_email = email
    user.save(update_fields=[
        'is_teacher_verified', 'verified_teacher_email',
        'is_student_verified', 'verified_student_email'
    ])

    # Tạo voucher giảm 50% cho người dùng Edu (chỉ tạo 1 lần)
    from store.models import Coupon
    from datetime import timedelta
    from django.utils import timezone
    
    # Kiểm tra xem đã có voucher edu chưa
    existing_edu_coupon = Coupon.objects.filter(
        target_type='single',
        target_email=email,
        is_active=True
    ).first()
    
    if not existing_edu_coupon:
        # Tạo mã voucher duy nhất: QHUN + 5 số
        import random
        voucher_code = 'QHUN' + ''.join(random.choices('0123456789', k=5))
        
        # Tạo coupon/voucher
        Coupon.objects.create(
            name='Ưu đãi Edu - Giảm 50%',
            code=voucher_code,
            discount_type='percentage',
            discount_value=50,
            target_type='single',
            target_email=email,
            max_products=1,
            min_order_amount=100000,
            usage_limit=1,
            used_count=0,
            expire_days=90,  # 90 ngày
            is_active=True,
            expire_at=timezone.now() + timedelta(days=90)
        )
        voucher_created = True
        voucher_code_display = voucher_code
    else:
        voucher_created = False
        voucher_code_display = existing_edu_coupon.code

    # Xóa OTP khỏi session
    for key in ['edu_otp', 'edu_otp_email', 'edu_otp_created_at']:
        request.session.pop(key, None)

    role = 'Teacher' if is_teacher else 'Student'
    if voucher_created:
        return JsonResponse({
            'success': True, 
            'message': f'Xác thực {role} thành công! Bạn đã nhận được voucher giảm 50% (Mã: {voucher_code_display}). Vui lòng kiểm tra trang tài khoản.'
        })
    else:
        return JsonResponse({'success': True, 'message': f'Xác thực {role} thành công! Tài khoản của bạn đã được xác thực.'})
