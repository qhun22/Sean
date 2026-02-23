"""
Views cho ứng dụng store - QHUN22
"""
import os
import random
import time
import requests
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


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
            return JsonResponse({'status': 'error', 'message': 'Email missing'})
        
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
        
        data = {
            "personalizations": [{
                "to": [{"email": email}],
                "subject": "OTP Verification - QHUN22"
            }],
            "from": {"email": from_email},
            "content": [{
                "type": "text/html",
                "value": f"<h1>Mã OTP của bạn: {otp}</h1><p>Mã có hiệu lực trong 5 phút.</p>"
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
                return JsonResponse({'status': 'error', 'message': f'Failed to send email: {response.status_code}'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def home(request):
    """
    Trang chủ của cửa hàng QHUN22
    """
    return render(request, 'store/home.html')


def product_search(request):
    """
    Tìm kiếm sản phẩm
    """
    query = request.GET.get('q', '')
    context = {
        'query': query,
    }
    return render(request, 'store/search.html', context)


def cart_detail(request):
    """
    Chi tiết giỏ hàng
    """
    return render(request, 'store/cart.html')


def order_tracking(request):
    """
    Tra cứu đơn hàng
    """
    return render(request, 'store/order_tracking.html')


def wishlist(request):
    """
    Danh sách sản phẩm yêu thích
    """
    return render(request, 'store/wishlist.html')


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
    return render(request, 'store/profile.html')


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
            return JsonResponse({'status': 'error', 'message': 'Email missing'})
        
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
        
        data = {
            "personalizations": [{
                "to": [{"email": email}],
                "subject": "OTP Quên Mật Khẩu - QHUN22"
            }],
            "from": {"email": from_email},
            "content": [{
                "type": "text/html",
                "value": f"<h1>Mã OTP quên mật khẩu của bạn: {otp}</h1><p>Mã có hiệu lực trong 5 phút.</p><p>Nếu bạn không yêu cầu mã này, vui lòng bỏ qua.</p>"
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
                return JsonResponse({'status': 'error', 'message': f'Failed to send email: {response.status_code}'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def verify_otp_forgot_password_view(request):
    """
    Xác minh OTP cho quên mật khẩu (AJAX)
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        otp_input = request.POST.get('otp')
        
        if not email or not otp_input:
            return JsonResponse({'status': 'error', 'message': 'Missing parameters'})
        
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
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def reset_password_view(request):
    """
    Đặt lại mật khẩu (AJAX)
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        
        if not email or not new_password:
            return JsonResponse({'status': 'error', 'message': 'Missing parameters'})
        
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
            
            return JsonResponse({'status': 'success', 'message': 'Password reset successful'})
        except CustomUser.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@login_required
def dashboard_view(request):
    """
    Trang dashboard quản trị - hiển thị danh sách người dùng
    Chỉ admin (superuser) mới có thể truy cập
    """
    # Kiểm tra quyền admin
    if not request.user.is_superuser:
        messages.error(request, 'Bạn không có quyền truy cập trang này!')
        return redirect('store:profile')
    
    # Lấy danh sách tất cả người dùng
    from store.models import CustomUser
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Thống kê
    regular_users = users.filter(is_oauth_user=False, is_superuser=False).count()
    oauth_users = users.filter(is_oauth_user=True).count()
    
    context = {
        'users': users,
        'regular_users': regular_users,
        'oauth_users': oauth_users,
    }
    return render(request, 'store/dashboard.html', context)
