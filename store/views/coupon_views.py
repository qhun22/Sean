"""
Coupon Views (list, add, edit, delete, apply) - QHUN22 Store
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


@login_required
def coupon_list(request):
    """Lấy danh sách mã giảm giá (admin) hoặc chi tiết 1 coupon"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Không có quyền'}, status=403)
    
    from store.models import Coupon
    
    coupon_id = request.GET.get('id')
    if coupon_id:
        try:
            c = Coupon.objects.get(id=coupon_id)
            return JsonResponse({'success': True, 'coupon': {
                'id': c.id,
                'name': c.name,
                'code': c.code,
                'discount_type': c.discount_type,
                'discount_value': str(c.discount_value),
                'target_type': c.target_type,
                'target_email': c.target_email,
                'max_products': c.max_products,
                'min_order_amount': str(c.min_order_amount),
                'usage_limit': c.usage_limit,
                'used_count': c.used_count,
                'expire_days': c.expire_days,
                'is_active': c.is_active,
            }})
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Không tìm thấy'}, status=404)
    
    coupons = Coupon.objects.all()
    result = []
    for c in coupons:
        result.append({
            'id': c.id,
            'name': c.name,
            'code': c.code,
            'discount_type': c.discount_type,
            'discount_value': str(c.discount_value),
            'target_type': c.target_type,
            'target_email': c.target_email,
            'max_products': c.max_products,
            'min_order_amount': str(c.min_order_amount),
            'usage_limit': c.usage_limit,
            'used_count': c.used_count,
            'is_active': c.is_active,
            'is_valid': c.is_valid(),
            'expire_at': c.expire_at.strftime('%d/%m/%Y'),
        })
    return JsonResponse({'success': True, 'coupons': result})



@login_required
@require_POST
def coupon_add(request):
    """Thêm mã giảm giá mới"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Không có quyền'}, status=403)
    
    from store.models import Coupon
    
    code = request.POST.get('code', '').strip().upper()
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'success': False, 'message': 'Tên chương trình không được để trống'})
    if not code:
        return JsonResponse({'success': False, 'message': 'Tên mã giảm không được để trống'})
    if ' ' in code:
        return JsonResponse({'success': False, 'message': 'Mã giảm không được chứa khoảng trắng'})
    if Coupon.objects.filter(code=code).exists():
        return JsonResponse({'success': False, 'message': 'Mã giảm giá đã tồn tại'})
    
    expire_days = int(request.POST.get('expire_days', '30'))
    if expire_days < 1:
        return JsonResponse({'success': False, 'message': 'Hạn sử dụng phải ít nhất 1 ngày'})
    
    expire_at = timezone.now() + datetime.timedelta(days=expire_days)
    
    try:
        Coupon.objects.create(
            name=name,
            code=code,
            discount_type=request.POST.get('discount_type', 'percentage'),
            discount_value=Decimal(request.POST.get('discount_value', '0')),
            target_type=request.POST.get('target_type', 'all'),
            target_email=request.POST.get('target_email', ''),
            max_products=int(request.POST.get('max_products', '0')),
            min_order_amount=Decimal(request.POST.get('min_order_amount', '0')),
            usage_limit=int(request.POST.get('usage_limit', '0')),
            expire_days=expire_days,
            is_active=request.POST.get('is_active') == '1',
            expire_at=expire_at,
        )
        return JsonResponse({'success': True, 'message': 'Đã thêm mã giảm giá'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Lỗi: {str(e)}'})



@login_required
@require_POST
def coupon_edit(request):
    """Sửa mã giảm giá"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Không có quyền'}, status=403)
    
    from store.models import Coupon
    
    coupon_id = request.POST.get('id')
    if not coupon_id:
        return JsonResponse({'success': False, 'message': 'Thiếu ID'})
    
    try:
        c = Coupon.objects.get(id=coupon_id)
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy'})
    
    try:
        c.name = request.POST.get('name', c.name)
        c.discount_type = request.POST.get('discount_type', 'percentage')
        c.discount_value = Decimal(request.POST.get('discount_value', '0'))
        c.target_type = request.POST.get('target_type', 'all')
        c.target_email = request.POST.get('target_email', '')
        c.max_products = int(request.POST.get('max_products', '0'))
        c.min_order_amount = Decimal(request.POST.get('min_order_amount', '0'))
        c.usage_limit = int(request.POST.get('usage_limit', '0'))
        new_expire_days = int(request.POST.get('expire_days', '0'))
        if new_expire_days > 0 and new_expire_days != c.expire_days:
            c.expire_days = new_expire_days
            c.expire_at = c.created_at + datetime.timedelta(days=new_expire_days)
        c.is_active = request.POST.get('is_active') == '1'
        c.save()
        return JsonResponse({'success': True, 'message': 'Đã cập nhật mã giảm giá'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Lỗi: {str(e)}'})



@login_required
@require_POST
def coupon_delete(request):
    """Xóa mã giảm giá"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Không có quyền'}, status=403)
    
    from store.models import Coupon
    
    coupon_id = request.POST.get('id')
    if not coupon_id:
        return JsonResponse({'success': False, 'message': 'Thiếu ID'})
    
    try:
        c = Coupon.objects.get(id=coupon_id)
        c.delete()
        return JsonResponse({'success': True, 'message': 'Đã xóa mã giảm giá'})
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy'})



@login_required
@require_POST
def coupon_apply(request):
    """
    Áp dụng mã giảm giá - 7-step validation:
    1. Có tồn tại không?
    2. Có active không?
    3. Có hết hạn chưa?
    4. Có đúng đối tượng không?
    5. Đơn có đạt tối thiểu không?
    6. Có vượt số lượng sản phẩm không?
    7. Đã vượt số lượt chưa?
    """
    from store.models import Coupon
    import json
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Dữ liệu không hợp lệ'})
    
    code = data.get('code', '').strip().upper()
    try:
        order_total = Decimal(str(data.get('order_total', 0)))
    except Exception:
        order_total = Decimal('0')
    try:
        item_count = int(data.get('item_count', 0))
    except Exception:
        item_count = 0
    
    if not code:
        return JsonResponse({'success': False, 'message': 'Vui lòng nhập mã giảm giá'})
    
    # 1. Có tồn tại không?
    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Mã giảm giá không tồn tại'})
    
    # 2. Có active không?
    if not coupon.is_active:
        return JsonResponse({'success': False, 'message': 'Mã giảm giá đã bị vô hiệu hóa'})
    
    # 3. Có hết hạn chưa?
    if coupon.is_expired():
        return JsonResponse({'success': False, 'message': 'Mã giảm giá đã hết hạn'})
    
    # 4. Có đúng đối tượng không?
    if coupon.target_type == 'single':
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Vui lòng đăng nhập để sử dụng mã này'})
        
        # Kiểm tra email đăng nhập HOẶC email edu đã xác thực
        user_email = request.user.email.lower() if request.user.email else ''
        target_email = coupon.target_email.lower() if coupon.target_email else ''
        
        # Lấy email edu đã xác thực (xử lý None)
        verified_student = (request.user.verified_student_email or '').lower()
        verified_teacher = (request.user.verified_teacher_email or '').lower()
        
        # So sánh trực tiếp hoặc qua email đã xác thực edu
        is_valid = (
            user_email == target_email or
            user_email == verified_student or
            user_email == verified_teacher or
            target_email == verified_student or
            target_email == verified_teacher
        )
        
        if not is_valid:
            return JsonResponse({'success': False, 'message': 'Mã giảm giá không áp dụng cho tài khoản của bạn'})
    
    # 5. Đơn có đạt tối thiểu không?
    if order_total < coupon.min_order_amount:
        min_fmt = f'{int(coupon.min_order_amount):,}'.replace(',', '.')
        return JsonResponse({'success': False, 'message': f'Đơn hàng chưa đạt giá trị tối thiểu {min_fmt}đ'})
    
    # 6. Có vượt số lượng sản phẩm không?
    if coupon.max_products > 0 and item_count > coupon.max_products:
        return JsonResponse({
            'success': False, 
            'message': f'Voucher chỉ áp dụng cho tối đa {coupon.max_products} sản phẩm. Vui lòng chọn lại sản phẩm để áp dụng voucher.',
            'max_products': coupon.max_products
        })
    
    # 7. Đã vượt số lượt chưa? (per-user)
    if coupon.usage_limit > 0:
        from store.models import CouponUsage
        user_usage = CouponUsage.objects.filter(coupon=coupon, user=request.user).count()
        if user_usage >= coupon.usage_limit:
            return JsonResponse({'success': False, 'message': f'Bạn đã dùng hết {coupon.usage_limit} lượt của mã này'})
    
    try:
        discount = coupon.calculate_discount(order_total)
    except Exception:
        return JsonResponse({'success': False, 'message': 'Lỗi tính toán giảm giá'})
    
    return JsonResponse({
        'success': True,
        'code': coupon.code,
        'discount': str(int(discount)),
        'discount_display': f'{int(discount):,}đ'.replace(',', '.'),
        'new_total': str(int(order_total - discount)),
        'new_total_display': f'{int(order_total - discount):,}đ'.replace(',', '.'),
        'name': coupon.name,
    })
