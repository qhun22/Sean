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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import models
from django.db.models import Q, Count, Sum
from django.utils import timezone
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
    Hiển thị danh sách sản phẩm với phân trang (tối đa 15 sản phẩm/trang)
    Sản phẩm có hàng hiển thị trước, hết hàng hiển thị sau
    """
    from store.models import Product, SiteVisit
    
    # Tracking lượt truy cập trang chủ
    # Lấy IP của người dùng
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    
    # Lưu lượt truy cập
    SiteVisit.objects.create(
        ip_address=ip_address,
        user=request.user if request.user.is_authenticated else None
    )
    
    # Lấy tất cả sản phẩm đang hoạt động
    # Sắp xếp: có hàng trước (stock > 0), hết hàng sau
    # Sử dụng annotation để sắp xếp theo stock
    from django.db.models import Case, When, IntegerField
    
    products_list = Product.objects.filter(is_active=True).annotate(
        stock_order=Case(
            When(stock__gt=0, then=0),
            default=1,
            output_field=IntegerField(),
        )
    ).order_by('stock_order', '-created_at')
    
    # Phân trang - 15 sản phẩm mỗi trang
    paginator = Paginator(products_list, 15)
    
    # Lấy số trang từ URL
    page = request.GET.get('page', 1)
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # Nếu page không phải số, lấy trang đầu tiên
        products = paginator.page(1)
    except EmptyPage:
        # Nếu trang vượt quá, lấy trang cuối cùng
        products = paginator.page(paginator.num_pages)
    
    context = {
        'products': products,
    }
    return render(request, 'store/home.html', context)


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
    from store.models import CustomUser, SiteVisit
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Search users
    user_search = request.GET.get('user_search', '')
    if user_search:
        users = users.filter(
            models.Q(email__icontains=user_search) | 
            models.Q(last_name__icontains=user_search) |
            models.Q(first_name__icontains=user_search)
        )
    
    # Phân trang người dùng (5 người dùng/trang)
    user_page = request.GET.get('user_page', 1)
    user_paginator = Paginator(users, 10)
    try:
        users_paginated = user_paginator.page(user_page)
    except PageNotAnInteger:
        users_paginated = user_paginator.page(1)
    except EmptyPage:
        users_paginated = user_paginator.page(user_paginator.num_pages)
    
    # Thống kê
    regular_users = users.filter(is_oauth_user=False, is_superuser=False).count()
    oauth_users = users.filter(is_oauth_user=True).count()
    
    # Tổng lượt truy cập trang chủ
    total_visits = SiteVisit.objects.count()
    
    # Sản phẩm sắp hết hàng (dưới 5 sản phẩm)
    from store.models import Product, Order, Brand
    low_stock_products_count = Product.objects.filter(stock__gt=0, stock__lt=5).count()
    
    # Danh sách hãng với số sản phẩm (cho stats)
    brands_for_stats = Brand.objects.filter(is_active=True).annotate(product_count=Count('products')).order_by('name')[:8]
    
    # Danh sách hãng cho bảng (có phân trang)
    all_brands = Brand.objects.filter(is_active=True).order_by('name')
    brand_search = request.GET.get('brand_search', '')
    if brand_search:
        all_brands = all_brands.filter(name__icontains=brand_search)
    
    brand_page = request.GET.get('brand_page', 1)
    brand_paginator = Paginator(all_brands, 10)
    try:
        brands_paginated = brand_paginator.page(brand_page)
    except PageNotAnInteger:
        brands_paginated = brand_paginator.page(1)
    except EmptyPage:
        brands_paginated = brand_paginator.page(brand_paginator.num_pages)
    
    # Doanh thu hôm nay
    today = timezone.now().date()
    revenue_today = Order.objects.filter(
        created_at__date=today,
        status__in=['processing', 'shipped', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Doanh thu tháng này
    from datetime import datetime
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    revenue_this_month = Order.objects.filter(
        created_at__gte=start_of_month,
        status__in=['processing', 'shipped', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Dữ liệu biểu đồ doanh thu năm 2026 (12 tháng)
    # Hiện tại: 23/02/2026 - Tất cả tháng có chiều cao bằng nhau khi chưa có dữ liệu
    month_data = [
        {'name': 'T1', 'value': 0, 'height': 10},
        {'name': 'T2', 'value': 0, 'height': 10},
        {'name': 'T3', 'value': 0, 'height': 10},
        {'name': 'T4', 'value': 0, 'height': 10},
        {'name': 'T5', 'value': 0, 'height': 10},
        {'name': 'T6', 'value': 0, 'height': 10},
        {'name': 'T7', 'value': 0, 'height': 10},
        {'name': 'T8', 'value': 0, 'height': 10},
        {'name': 'T9', 'value': 0, 'height': 10},
        {'name': 'T10', 'value': 0, 'height': 10},
        {'name': 'T11', 'value': 0, 'height': 10},
        {'name': 'T12', 'value': 0, 'height': 10},
    ]
    
    context = {
        'users_paginated': users_paginated,
        'total_users': users.count(),
        'regular_users': regular_users,
        'oauth_users': oauth_users,
        'total_visits': total_visits,
        'low_stock_products_count': low_stock_products_count,
        'revenue_today': revenue_today,
        'revenue_this_month': revenue_this_month,
        'months': month_data,
        'brands': brands_for_stats,
        'brands_paginated': brands_paginated,
    }
    return render(request, 'store/dashboard.html', context)


import re

def generate_slug(text):
    """Tạo slug từ text tiếng Việt"""
    # Remove accents
    import unicodedata
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Convert to lowercase and replace spaces with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.lower().strip('-')


@login_required
def brand_list(request):
    """Danh sách hãng sản phẩm"""
    if not request.user.is_superuser:
        messages.error(request, 'Bạn không có quyền truy cập!')
        return redirect('store:profile')
    
    from store.models import Brand
    brands = Brand.objects.all().order_by('name')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        brands = brands.filter(name__icontains=search)
    
    # Pagination
    brand_page = request.GET.get('brand_page', 1)
    brand_paginator = Paginator(brands, 10)
    try:
        brands_paginated = brand_paginator.page(brand_page)
    except PageNotAnInteger:
        brands_paginated = brand_paginator.page(1)
    except EmptyPage:
        brands_paginated = brand_paginator.page(brand_paginator.num_pages)
    
    context = {
        'brands_paginated': brands_paginated,
        'search': search,
    }
    return render(request, 'store/brand_list.html', context)


@login_required
@require_http_methods(["POST"])
def brand_add(request):
    """Thêm hãng mới"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Không có quyền!'}, status=403)
    
    from store.models import Brand
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    
    if not name:
        return JsonResponse({'success': False, 'message': 'Tên hãng không được để trống!'}, status=400)
    
    # Check exists
    if Brand.objects.filter(name__iexact=name).exists():
        return JsonResponse({'success': False, 'message': 'Hãng đã tồn tại!'}, status=400)
    
    slug = generate_slug(name)
    # Ensure unique slug
    base_slug = slug
    counter = 1
    while Brand.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    brand = Brand.objects.create(
        name=name,
        slug=slug,
        description=description,
        is_active=True
    )
    
    return JsonResponse({
        'success': True, 
        'message': f'Đã thêm hãng "{name}"!',
        'brand': {'id': brand.id, 'name': brand.name, 'slug': brand.slug}
    })


@login_required
@require_http_methods(["POST"])
def brand_edit(request):
    """Sửa hãng"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Không có quyền!'}, status=403)
    
    from store.models import Brand
    brand_id = request.POST.get('brand_id')
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    
    if not name or not brand_id:
        return JsonResponse({'success': False, 'message': 'Thiếu thông tin!'}, status=400)
    
    try:
        brand = Brand.objects.get(id=brand_id)
    except Brand.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Hãng không tồn tại!'}, status=404)
    
    # Check duplicate name (excluding current brand)
    if Brand.objects.filter(name__iexact=name).exclude(id=brand_id).exists():
        return JsonResponse({'success': False, 'message': 'Tên hãng đã tồn tại!'}, status=400)
    
    brand.name = name
    brand.description = description
    brand.slug = generate_slug(name)
    brand.save()
    
    return JsonResponse({'success': True, 'message': f'Đã cập nhật hãng "{name}"!'})


@login_required
@require_http_methods(["POST"])
def brand_delete(request):
    """Xóa hãng"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Không có quyền!'}, status=403)
    
    from store.models import Brand
    brand_id = request.POST.get('brand_id')
    
    if not brand_id:
        return JsonResponse({'success': False, 'message': 'Thiếu thông tin!'}, status=400)
    
    try:
        brand = Brand.objects.get(id=brand_id)
    except Brand.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Hãng không tồn tại!'}, status=404)
    
    # Check if brand has products
    if brand.products.exists():
        return JsonResponse({'success': False, 'message': 'Không thể xóa! Hãng đang có sản phẩm.'}, status=400)
    
    brand_name = brand.name
    brand.delete()
    
    return JsonResponse({'success': True, 'message': f'Đã xóa hãng "{brand_name}"!'})

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def user_edit(request):
    """Sửa thông tin người dùng"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Không có quyền!'}, status=403)
    
    from store.models import CustomUser
    user_id = request.POST.get('user_id')
    last_name = request.POST.get('last_name', '').strip()
    first_name = request.POST.get('first_name', '').strip()
    phone = request.POST.get('phone', '').strip()
    
    if not user_id:
        return JsonResponse({'success': False, 'message': 'Thiếu thông tin!'}, status=400)
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Người dùng không tồn tại!'}, status=404)
    
    user.last_name = last_name
    user.first_name = first_name
    user.phone = phone if phone else None
    user.save()
    
    return JsonResponse({'success': True, 'message': 'Cập nhật thông tin thành công!'})

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def user_delete(request):
    """Xóa người dùng"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Không có quyền!'}, status=403)
    
    from store.models import CustomUser
    user_id = request.POST.get('user_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': 'Thiếu thông tin!'}, status=400)
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Người dùng không tồn tại!'}, status=404)
    
    # Không cho xóa admin
    if user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Không thể xóa tài khoản admin!'}, status=400)
    
    user_email = user.email
    user.delete()
    
    return JsonResponse({'success': True, 'message': f'Đã xóa người dùng "{user_email}"!'})
