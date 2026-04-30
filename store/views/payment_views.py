"""
Payment Views (VietQR, VNPay, QR) - QHUN22 Store
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
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.db import models, transaction, IntegrityError
from django.db.models import Q, Count, Sum, Max
from django.utils import timezone
from django.urls import reverse
import datetime

logger = logging.getLogger(__name__)


@csrf_exempt
@login_required
@require_POST
def qr_payment_create(request):
    """
    Khách tạo QR trên checkout → lưu PendingQRPayment.
    POST: amount, transfer_code
    """
    from store.models import PendingQRPayment
    import json

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Dữ liệu không hợp lệ'}, status=400)

    amount = data.get('amount')
    transfer_code = data.get('transfer_code')

    if not amount or not transfer_code:
        return JsonResponse({'success': False, 'message': 'Thiếu thông tin'}, status=400)

    # Kiểm tra trùng mã CK
    if PendingQRPayment.objects.filter(transfer_code=transfer_code).exists():
        return JsonResponse({'success': False, 'message': 'Mã chuyển khoản đã tồn tại'}, status=400)

    qr = PendingQRPayment.objects.create(
        user=request.user,
        amount=amount,
        transfer_code=transfer_code,
    )
    return JsonResponse({'success': True, 'id': qr.id, 'message': 'Đã tạo QR thành công'})


@csrf_exempt
@login_required
@require_POST
def vietqr_create_order(request):
    """
    Tạo đơn hàng VietQR:
    - Sinh payment_code, ghi vào Order.payment_code
    - Set Order.expires_at = now + 15 phút
    - Tạo PendingQRPayment liên kết qua transfer_code
    - Trả về redirect_url dạng /vietqr-payment/<order_id>/
    """
    from store.models import Cart, Order, OrderItem, ProductDetail, FolderColorImage, PendingQRPayment
    from datetime import timedelta
    import json
    import random as _rand

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Dữ liệu không hợp lệ'}, status=400)

    items_param = data.get('items_param', '')

    if not items_param:
        return JsonResponse({'success': False, 'message': 'Không có sản phẩm'}, status=400)

    try:
        item_ids = [int(x) for x in items_param.split(',') if x.strip()]
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'Danh sách sản phẩm không hợp lệ'}, status=400)

    cart = Cart.get_or_create_for_user(request.user)
    if not cart:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy giỏ hàng'}, status=400)

    cart_items = list(cart.items.filter(id__in=item_ids).select_related('product', 'product__brand'))
    if not cart_items:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy sản phẩm trong giỏ'}, status=400)

    total_amount = sum(item.price_at_add * item.quantity for item in cart_items)

    def _unique_order_code(max_attempts=20):
        for _ in range(max_attempts):
            code = 'QHUN' + str(_rand.randint(10000, 99999))
            if not Order.objects.filter(order_code=code).exists():
                return code
        return None

    def _unique_payment_code(max_attempts=20):
        """payment_code = QHUN + 5 chữ số random, dùng cho cả order.payment_code và PendingQRPayment.transfer_code"""
        for _ in range(max_attempts):
            code = 'QHUN' + ''.join(str(_rand.randint(0, 9)) for _ in range(5))
            already_in_order = Order.objects.filter(payment_code=code).exists()
            already_in_qr = PendingQRPayment.objects.filter(transfer_code=code).exists()
            if not already_in_order and not already_in_qr:
                return code
        return None

    order_code = _unique_order_code()
    payment_code = _unique_payment_code()

    if not order_code or not payment_code:
        return JsonResponse({
            'success': False,
            'message': 'Hệ thống đang bận tạo mã thanh toán. Vui lòng thử lại sau vài giây.'
        }, status=503)

    expires_at = timezone.now() + timedelta(minutes=15)

    try:
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                order_code=order_code,
                total_amount=total_amount,
                payment_method='vietqr',
                status='awaiting_payment',
                payment_code=payment_code,
                expires_at=expires_at,
            )

            for ci in cart_items:
                thumb_url = ''
                try:
                    if ci.product and ci.product.brand_id:
                        detail = ProductDetail.objects.get(product=ci.product)
                        variant = detail.variants.filter(
                            is_active=True, color_name=ci.color_name
                        ).first()
                        if variant and variant.sku:
                            img = FolderColorImage.objects.filter(
                                brand_id=ci.product.brand_id,
                                sku=variant.sku
                            ).order_by('order').first()
                            if img:
                                thumb_url = img.image.url
                    if not thumb_url and ci.product and ci.product.image:
                        thumb_url = ci.product.image.url
                except Exception:
                    pass

                OrderItem.objects.create(
                    order=order,
                    product=ci.product,
                    product_name=ci.product.name if ci.product else 'Sản phẩm',
                    color_name=ci.color_name,
                    storage=ci.storage,
                    quantity=ci.quantity,
                    price=ci.price_at_add,
                    thumbnail=thumb_url,
                )

            # PendingQRPayment dùng cùng payment_code làm transfer_code
            PendingQRPayment.objects.create(
                user=request.user,
                amount=total_amount,
                transfer_code=payment_code,
            )

            cart.items.filter(id__in=item_ids).delete()

    except IntegrityError:
        logger.warning('VietQR create order integrity error for user=%s', request.user.id, exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Mã giao dịch vừa trùng, vui lòng bấm đặt hàng lại.'
        }, status=409)
    except Exception:
        logger.exception('VietQR create order unexpected error for user=%s', request.user.id)
        return JsonResponse({
            'success': False,
            'message': 'Lỗi hệ thống khi tạo đơn VietQR. Vui lòng thử lại.'
        }, status=500)

    from store.telegram_utils import notify_payment_created
    notify_payment_created('vietqr', order_code, request.user.username, total_amount)

    # URL dạng /vietqr-payment/<order_id>/ — không lộ code hoặc amount qua query string
    return JsonResponse({
        'success': True,
        'redirect_url': reverse('store:vietqr_payment_page', kwargs={'order_id': order.id}),
    })


@login_required
def vietqr_payment_page(request, order_id):
    """
    Trang thanh toán VietQR — URL: /vietqr-payment/<order_id>/
    Toàn bộ dữ liệu nhạy cảm lấy từ DB, không đọc query string.
    """
    from store.models import Order

    # Ownership check: chỉ đúng chủ đơn mới xem được
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, 'Đơn hàng không tồn tại hoặc không thuộc về bạn.')
        return redirect('store:order_tracking')

    # Đơn không phải VietQR → redirect trang theo dõi
    if order.payment_method != 'vietqr':
        messages.info(request, 'Đơn hàng này không sử dụng phương thức VietQR.')
        return redirect('store:order_success', order_code=order.order_code)

    # Đơn đã hoàn tất → redirect trang thành công
    if order.status in ('processing', 'pending', 'shipped', 'delivered'):
        messages.info(request, 'Đơn hàng đã được thanh toán trước đó.')
        return redirect('store:order_success', order_code=order.order_code)

    # Đơn đã hết hạn thanh toán hoặc đã bị hủy thanh toán (VietQR)
    if order.status == 'payment_expired':
        if order.payment_status == 'cancelled':
            messages.warning(request, 'Đơn hàng đã hủy thanh toán VietQR.')
        else:
            messages.warning(request, 'Đơn hàng đã hết hạn thanh toán.')
        return redirect('store:order_tracking')

    # Đơn đã bị hủy thủ công → thông báo + redirect
    if order.status == 'cancelled':
        messages.warning(request, 'Đơn hàng đã bị hủy.')
        return redirect('store:order_tracking')

    # Tính thời gian còn lại từ expires_at trên DB
    timeout_seconds = 0
    if order.expires_at:
        remaining = (order.expires_at - timezone.now()).total_seconds()
        timeout_seconds = max(0, int(remaining))

    # Hết hạn → ghi cả order.status và payment_status
    if timeout_seconds <= 0 and order.status == 'awaiting_payment':
        order.status = 'payment_expired'
        order.payment_status = 'expired'
        order.save(update_fields=['status', 'payment_status', 'updated_at'])

    context = {
        'order': order,
        'order_status': order.status,
        'payment_status': order.payment_status,
        'timeout_seconds': timeout_seconds,
        'bank_id': settings.BANK_ID,
        'bank_account_no': settings.BANK_ACCOUNT_NO,
        'bank_account_name': settings.BANK_ACCOUNT_NAME,
    }
    return render(request, 'store/payment/vietqr_payment.html', context)


@login_required
def vietqr_page_status(request):
    """
    Polling API: GET ?order_id=<id>
    So sánh dữ liệu từ DB, không tin bất kỳ input nào ngoài order_id.
    """
    from store.models import PendingQRPayment, Order

    try:
        order_id = int(request.GET.get('order_id', ''))
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'status': 'error'}, status=400)

    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'status': 'error'}, status=404)

    if order.status == 'payment_expired':
        return JsonResponse({'success': True, 'status': 'expired'})

    if order.status == 'cancelled':
        return JsonResponse({'success': True, 'status': 'cancelled'})

    if order.status in ('processing', 'pending', 'shipped', 'delivered'):
        return JsonResponse({'success': True, 'status': 'approved'})

    # Đơn vẫn awaiting_payment — kiểm tra PendingQRPayment
    if not order.payment_code:
        return JsonResponse({'success': True, 'status': 'error'})

    # Kiểm tra hết hạn theo DB
    if order.is_payment_expired:
        if order.status == 'awaiting_payment':
            order.status = 'payment_expired'
            order.payment_status = 'expired'
            order.save(update_fields=['status', 'payment_status', 'updated_at'])
        return JsonResponse({'success': True, 'status': 'expired'})

    try:
        qr = PendingQRPayment.objects.get(transfer_code=order.payment_code, user=request.user)
    except PendingQRPayment.DoesNotExist:
        return JsonResponse({'success': True, 'status': 'expired'})

    if qr.status == 'approved':
        if order.status == 'awaiting_payment':
            order.status = 'processing'
            order.payment_status = 'paid'
            order.save(update_fields=['status', 'payment_status', 'updated_at'])

            from store.telegram_utils import notify_order_success
            from store.email_utils import send_order_invoice_email
            items = list(order.items.values('product_name', 'quantity', 'storage', 'color_name'))
            notify_order_success(order.order_code, 'vietqr', items)
            send_order_invoice_email(order, base_url=request.build_absolute_uri('/'))

        return JsonResponse({'success': True, 'status': 'approved'})

    if qr.status == 'cancelled':
        return JsonResponse({'success': True, 'status': 'cancelled'})

    return JsonResponse({'success': True, 'status': 'pending'})


@csrf_exempt
@login_required
@require_POST
def vietqr_expire(request):
    """
    Client báo hết giờ → huỷ đơn theo order_id từ POST body.
    POST body: { "order_id": <int> }
    """
    from store.models import Order, PendingQRPayment
    import json

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False})

    try:
        order_id = int(data.get('order_id', ''))
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'order_id không hợp lệ'}, status=400)

    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy đơn hàng'}, status=404)

    if order.status == 'awaiting_payment':
        # Phân biệt hết hạn timer (expired) vs khách chủ động hủy (cancelled)
        # Cả hai đều set order.status = 'payment_expired' — KHÔNG dùng 'cancelled'
        reason = data.get('reason', 'cancelled')
        order.status = 'payment_expired'
        order.payment_status = 'expired' if reason == 'expired' else 'cancelled'
        order.save(update_fields=['status', 'payment_status', 'updated_at'])

    # Xoá PendingQRPayment pending nếu còn
    if order.payment_code:
        PendingQRPayment.objects.filter(
            transfer_code=order.payment_code,
            user=request.user,
            status='pending',
        ).delete()

    return JsonResponse({'success': True})


@csrf_exempt
@login_required
@require_POST
def vietqr_mark_paid(request):
    """
    Người dùng tự báo đã chuyển khoản.
    POST body: { "order_id": <int> }
    → Chuyển order.status sang 'processing' để admin xem xét.
    """
    from store.models import Order
    import json

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Dữ liệu không hợp lệ'}, status=400)

    try:
        order_id = int(data.get('order_id', ''))
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'order_id không hợp lệ'}, status=400)

    try:
        order = Order.objects.get(id=order_id, user=request.user, payment_method='vietqr')
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy đơn hàng'}, status=404)

    if order.status == 'awaiting_payment':
        order.status = 'processing'
        order.payment_status = 'paid'
        order.save(update_fields=['status', 'payment_status', 'updated_at'])
        logger.info('User %s self-reported payment for order %s', request.user.id, order.order_code)
        return JsonResponse({'success': True, 'message': 'Đã ghi nhận. Chúng tôi sẽ xác nhận trong vài phút.'})

    if order.status == 'processing':
        return JsonResponse({'success': True, 'message': 'Đơn hàng đang được xử lý.'})

    return JsonResponse({'success': False, 'message': f'Trạng thái đơn hàng không hợp lệ: {order.status}'}, status=422)


@csrf_exempt
def vietqr_callback(request):
    """
    Fake callback endpoint mô phỏng ngân hàng gọi về sau khi thanh toán.
    /vietqr/callback/?order_id=<id>&status=success&token=<secret>

    Trong thực tế đây sẽ là HMAC-SHA256 verify.
    Demo: dùng VIETQR_CALLBACK_TOKEN trong settings (mặc định 'dev-secret').
    """
    from store.models import Order, PendingQRPayment

    expected_token = getattr(settings, 'VIETQR_CALLBACK_TOKEN', 'dev-secret')
    received_token = request.GET.get('token', '') or request.POST.get('token', '')

    # Luôn trả về 200 để tránh lộ thông tin (timing attack / enumeration)
    if received_token != expected_token:
        logger.warning('VietQR callback: invalid token from %s', request.META.get('REMOTE_ADDR'))
        return JsonResponse({'success': False, 'message': 'Unauthorised'}, status=401)

    try:
        order_id = int(request.GET.get('order_id', '') or request.POST.get('order_id', ''))
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'order_id không hợp lệ'}, status=400)

    status_param = (request.GET.get('status', '') or request.POST.get('status', '')).lower()
    if status_param not in ('success', 'failed'):
        return JsonResponse({'success': False, 'message': 'status phải là success hoặc failed'}, status=400)

    try:
        order = Order.objects.get(id=order_id, payment_method='vietqr')
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy đơn hàng'}, status=404)

    if status_param == 'success':
        if order.status == 'awaiting_payment':
            with transaction.atomic():
                order.status = 'processing'
                order.payment_status = 'paid'
                order.save(update_fields=['status', 'payment_status', 'updated_at'])

                if order.payment_code:
                    PendingQRPayment.objects.filter(
                        transfer_code=order.payment_code
                    ).update(status='approved')

            from store.telegram_utils import notify_order_success
            from store.email_utils import send_order_invoice_email
            items = list(order.items.values('product_name', 'quantity', 'storage', 'color_name'))
            notify_order_success(order.order_code, 'vietqr', items)
            send_order_invoice_email(order, base_url=f'{request.scheme}://{request.get_host()}/')
            logger.info('VietQR callback: order %s marked as processing', order.order_code)

        return JsonResponse({'success': True, 'order_code': order.order_code, 'status': order.status})

    # status_param == 'failed'
    # C1 FIX: KHÔNG set order.status = 'cancelled' cho VietQR payment failure
    # Dùng payment_expired + payment_status = 'cancelled' thay thế
    if order.status == 'awaiting_payment':
        order.status = 'payment_expired'
        order.payment_status = 'cancelled'
        order.save(update_fields=['status', 'payment_status', 'updated_at'])
    return JsonResponse({'success': True, 'order_code': order.order_code, 'status': order.status})


    from store.models import Cart, Order, OrderItem, ProductDetail, FolderColorImage, PendingQRPayment
    import json
    import random as _rand
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Dữ liệu không hợp lệ'}, status=400)
    
    items_param = data.get('items_param', '')
    
    if not items_param:
        return JsonResponse({'success': False, 'message': 'Không có sản phẩm'}, status=400)
    
    try:
        item_ids = [int(x) for x in items_param.split(',') if x.strip()]
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'Danh sách sản phẩm không hợp lệ'}, status=400)
    
    cart = Cart.get_or_create_for_user(request.user)
    if not cart:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy giỏ hàng'}, status=400)
    
    cart_items = list(cart.items.filter(id__in=item_ids).select_related('product', 'product__brand'))
    if not cart_items:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy sản phẩm trong giỏ'}, status=400)
    
    total_amount = sum(item.price_at_add * item.quantity for item in cart_items)

    def generate_unique_order_code(max_attempts=20):
        for _ in range(max_attempts):
            code = 'QHUN' + str(_rand.randint(10000, 99999))
            if not Order.objects.filter(order_code=code).exists():
                return code
        return None

    def generate_unique_transfer_code(max_attempts=20):
        for _ in range(max_attempts):
            code = 'QHUN' + ''.join(str(_rand.randint(0, 9)) for _ in range(5))
            if not PendingQRPayment.objects.filter(transfer_code=code).exists():
                return code
        return None

    tracking_code = generate_unique_order_code()
    transfer_code = generate_unique_transfer_code()

    if not tracking_code or not transfer_code:
        return JsonResponse({
            'success': False,
            'message': 'Hệ thống đang bận tạo mã thanh toán. Vui lòng thử lại sau vài giây.'
        }, status=503)

    try:
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                order_code=tracking_code,
                total_amount=total_amount,
                payment_method='vietqr',
                status='awaiting_payment'
            )

            for ci in cart_items:
                thumb_url = ''
                try:
                    if ci.product and ci.product.brand_id:
                        detail = ProductDetail.objects.get(product=ci.product)
                        variant = detail.variants.filter(
                            is_active=True, color_name=ci.color_name
                        ).first()
                        if variant and variant.sku:
                            img = FolderColorImage.objects.filter(
                                brand_id=ci.product.brand_id,
                                sku=variant.sku
                            ).order_by('order').first()
                            if img:
                                thumb_url = img.image.url
                    if not thumb_url and ci.product and ci.product.image:
                        thumb_url = ci.product.image.url
                except Exception:
                    pass

                OrderItem.objects.create(
                    order=order,
                    product=ci.product,
                    product_name=ci.product.name if ci.product else 'Sản phẩm',
                    color_name=ci.color_name,
                    storage=ci.storage,
                    quantity=ci.quantity,
                    price=ci.price_at_add,
                    thumbnail=thumb_url,
                )

            PendingQRPayment.objects.create(
                user=request.user,
                amount=total_amount,
                transfer_code=transfer_code,
            )

            cart.items.filter(id__in=item_ids).delete()

    except IntegrityError:
        logger.warning('VietQR create order integrity error for user=%s', request.user.id, exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Mã giao dịch vừa trùng, vui lòng bấm đặt hàng lại.'
        }, status=409)
    except Exception:
        logger.exception('VietQR create order unexpected error for user=%s', request.user.id)
        return JsonResponse({
            'success': False,
            'message': 'Lỗi hệ thống khi tạo đơn VietQR. Vui lòng thử lại.'
        }, status=500)

    from store.telegram_utils import notify_payment_created
    notify_payment_created('vietqr', tracking_code, request.user.username, total_amount)

    return JsonResponse({
        'success': True,
        'redirect_url': '/vietqr-payment/?order=' + tracking_code + '&code=' + transfer_code,
    })



@login_required
def qr_payment_list(request):
    """
    Admin: lấy danh sách QR.
    ?filter=pending (default): chờ duyệt, tự cleanup expired.
    ?filter=history: approved + cancelled.
    """
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Không có quyền'}, status=403)

    from store.models import PendingQRPayment
    filter_type = request.GET.get('filter', 'pending')

    if filter_type == 'history':
        qrs = PendingQRPayment.objects.filter(status__in=['approved', 'cancelled']).order_by('-created_at')
    else:
        # Xoá hết QR pending quá 15 phút
        PendingQRPayment.cleanup_expired()
        qrs = PendingQRPayment.objects.filter(status='pending').order_by('-created_at')

    items = []
    for idx, qr in enumerate(qrs, 1):
        items.append({
            'id': qr.id,
            'stt': idx,
            'amount': int(qr.amount),
            'transfer_code': qr.transfer_code,
            'created_at': timezone.localtime(qr.created_at).strftime('%d/%m/%Y %H:%M:%S'),
            'user_email': qr.user.email,
            'qr_url': qr.qr_url(),
            'status': qr.status,
        })
    return JsonResponse({'success': True, 'items': items})



@login_required
def qr_payment_detail(request):
    """
    Admin: lấy chi tiết 1 QR (ảnh, số tiền, nội dung CK).
    GET: id
    """
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Không có quyền'}, status=403)

    from store.models import PendingQRPayment
    qr_id = request.GET.get('id')
    try:
        qr = PendingQRPayment.objects.get(id=qr_id)
    except PendingQRPayment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy QR'}, status=404)

    return JsonResponse({
        'success': True,
        'data': {
            'id': qr.id,
            'amount': int(qr.amount),
            'transfer_code': qr.transfer_code,
            'created_at': timezone.localtime(qr.created_at).strftime('%d/%m/%Y %H:%M:%S'),
            'user_email': qr.user.email,
            'user_name': qr.user.get_full_name(),
            'qr_url': qr.qr_url(),
            'status': qr.status,
        }
    })



@csrf_exempt
@login_required
@require_POST
def qr_payment_approve(request):
    """Admin duyệt QR → status = approved."""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Không có quyền'}, status=403)

    from store.models import PendingQRPayment
    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Dữ liệu không hợp lệ'}, status=400)

    qr_id = data.get('id')
    try:
        qr = PendingQRPayment.objects.get(id=qr_id, status='pending')
    except PendingQRPayment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy QR hoặc đã xử lý'}, status=404)

    qr.status = 'approved'
    qr.save()
    return JsonResponse({'success': True, 'message': f'Đã duyệt QR {qr.transfer_code}'})



@csrf_exempt
@login_required
@require_POST
def qr_payment_cancel(request):
    """Admin hủy QR → status = cancelled."""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Không có quyền'}, status=403)

    from store.models import PendingQRPayment
    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Dữ liệu không hợp lệ'}, status=400)

    qr_id = data.get('id')
    try:
        qr = PendingQRPayment.objects.get(id=qr_id, status='pending')
    except PendingQRPayment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Không tìm thấy QR hoặc đã xử lý'}, status=404)

    qr.status = 'cancelled'
    qr.save()
    return JsonResponse({'success': True, 'message': f'Đã hủy QR {qr.transfer_code}'})



@login_required
def qr_payment_status(request):
    """
    Checkout polling: kiểm tra trạng thái QR theo transfer_code.
    GET: transfer_code
    Trả về: status = 'pending' | 'approved' | 'cancelled' | 'expired'
    """
    from store.models import PendingQRPayment
    code = request.GET.get('code', '')
    if not code:
        return JsonResponse({'success': False, 'status': 'error'})

    try:
        qr = PendingQRPayment.objects.get(transfer_code=code, user=request.user)
    except PendingQRPayment.DoesNotExist:
        # Có thể đã bị cleanup (hết 15 phút) → coi như expired
        return JsonResponse({'success': True, 'status': 'expired'})

    if qr.is_expired:
        qr.delete()
        return JsonResponse({'success': True, 'status': 'expired'})

    return JsonResponse({'success': True, 'status': qr.status})

@login_required
@require_POST
@csrf_exempt
def vnpay_create(request):
    """
    Tạo yêu cầu thanh toán VNPay
    POST: amount, order_description, items_param
    """
    from store.models import VNPayPayment
    from store.vnpay_utils import VNPayUtil
    
    try:
        amount = float(request.POST.get('amount', 0))
        order_description = request.POST.get('order_description', 'Thanh toán mua hàng QHUN22')
        items_param = request.POST.get('items_param', '')
        
        if amount <= 0:
            return JsonResponse({'success': False, 'message': 'Số tiền không hợp lệ'}, status=400)
        
        # Tạo order code
        order_code = VNPayUtil.generate_order_code()
        
        # Lấy IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        # Tạo bản ghi VNPay Payment
        vnpay_payment = VNPayPayment.objects.create(
            user=request.user,
            amount=Decimal(amount),
            order_code=order_code,
            status='pending'
        )
        
        # Lưu items_param vào session (để lấy lại khi VNPay redirect về)
        request.session['vnpay_items_param'] = items_param
        request.session['vnpay_order_code'] = order_code
        
        # Xây dựng URL thanh toán (return URL sạch, không chứa query params)
        return_url = request.build_absolute_uri('/vnpay/return/')
        
        # Order description chỉ dùng ASCII (tránh lỗi encoding)
        safe_description = f'Thanh toan QHUN22 - {int(amount)} VND'
        
        payment_url = VNPayUtil.build_payment_url(
            amount=amount,
            order_code=order_code,
            order_description=safe_description,
            ip_address=ip_address,
            return_url=return_url
        )
        
        from store.telegram_utils import notify_payment_created
        notify_payment_created('vnpay', order_code, request.user.username, amount)
        
        return JsonResponse({
            'success': True,
            'payment_url': payment_url,
            'order_code': order_code
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)



@login_required
def vnpay_return(request):
    """
    Xử lý return từ VNPay sau khi thanh toán
    VNPay sẽ redirect về URL này với các tham số response
    """
    from store.models import VNPayPayment, Order, OrderItem, Cart, FolderColorImage, ProductDetail
    from store.vnpay_utils import VNPayUtil
    
    try:
        # Lấy tất cả tham số từ request (VNPay append vào return URL)
        response_data = request.GET.dict()
        order_code = response_data.get('vnp_TxnRef', '')
        
        # Lấy items_param từ session
        items_param = request.session.pop('vnpay_items_param', '')
        session_order_code = request.session.pop('vnpay_order_code', '')
        
        if not order_code:
            messages.error(request, 'Không tìm thấy mã giao dịch VNPay')
            return redirect('store:checkout')
        
        # Lấy bản ghi VNPay Payment
        try:
            vnpay_payment = VNPayPayment.objects.get(order_code=order_code)
        except VNPayPayment.DoesNotExist:
            messages.error(request, 'Không tìm thấy đơn hàng VNPay')
            return redirect('store:checkout')
        
        # Chỉ verify các tham số vnp_ (loại bỏ params không phải của VNPay)
        vnp_data = {k: v for k, v in response_data.items() if k.startswith('vnp_')}
        
        # Xác minh response từ VNPay
        is_valid, message = VNPayUtil.verify_payment_response(vnp_data)
        
        response_code = vnp_data.get('vnp_ResponseCode', '')
        transaction_no = vnp_data.get('vnp_TransactionNo', '')
        
        # Cập nhật thông tin thanh toán
        vnpay_payment.response_code = response_code
        vnpay_payment.response_message = message
        vnpay_payment.transaction_no = transaction_no
        
        if is_valid and response_code == '00':
            vnpay_payment.status = 'paid'
            vnpay_payment.paid_at = timezone.now()
            vnpay_payment.save()
            
            # Tạo mã đơn hàng QHUN + 5 số random
            import random as _rand
            tracking_code = 'QHUN' + str(_rand.randint(10000, 99999))
            
            # Tạo Order
            order = Order.objects.create(
                user=request.user,
                order_code=tracking_code,
                total_amount=vnpay_payment.amount,
                payment_method='vnpay',
                vnpay_order_code=order_code,
                status='processing'
            )
            
            # Lưu sản phẩm vào OrderItem trước khi xóa cart
            if items_param:
                try:
                    item_ids = [int(x) for x in items_param.split(',') if x.strip()]
                    cart = Cart.get_or_create_for_user(request.user)
                    if cart:
                        cart_items = cart.items.filter(id__in=item_ids).select_related('product', 'product__brand')
                        for ci in cart_items:
                            # Tìm thumbnail
                            thumb_url = ''
                            try:
                                if ci.product and ci.product.brand_id:
                                    detail = ProductDetail.objects.get(product=ci.product)
                                    variant = detail.variants.filter(
                                        is_active=True, color_name=ci.color_name
                                    ).first()
                                    if variant and variant.sku:
                                        img = FolderColorImage.objects.filter(
                                            brand_id=ci.product.brand_id,
                                            sku=variant.sku
                                        ).order_by('order').first()
                                        if img:
                                            thumb_url = img.image.url
                                if not thumb_url and ci.product and ci.product.image:
                                    thumb_url = ci.product.image.url
                            except Exception:
                                pass
                            
                            OrderItem.objects.create(
                                order=order,
                                product=ci.product,
                                product_name=ci.product.name if ci.product else 'Sản phẩm',
                                color_name=ci.color_name,
                                storage=ci.storage,
                                quantity=ci.quantity,
                                price=ci.price_at_add,
                                thumbnail=thumb_url,
                            )
                        # Xóa cart items sau khi đã lưu
                        cart_items.delete()
                except (ValueError, TypeError):
                    pass
            
            from store.telegram_utils import notify_order_success
            from store.email_utils import send_order_invoice_email
            vnpay_items = list(order.items.values('product_name', 'quantity', 'storage', 'color_name'))
            notify_order_success(tracking_code, 'vnpay', vnpay_items)
            send_order_invoice_email(order, base_url=request.build_absolute_uri('/'))
            
            return redirect('store:order_success', order_code=tracking_code)
        else:
            vnpay_payment.status = 'failed'
            vnpay_payment.save()
            messages.error(request, f'Thanh toán VNPay thất bại: {message}')
            
            if items_param:
                return redirect(f'{reverse("store:checkout")}?items={items_param}')
            return redirect('store:checkout')
            
    except Exception as e:
        messages.error(request, f'Lỗi xử lý thanh toán: {str(e)}')
        return redirect('store:checkout')



@csrf_exempt
@require_http_methods(["POST"])
def vnpay_ipn(request):
    """
    Xử lý IPN (Instant Payment Notification) từ VNPay
    VNPay sẽ gửi POST request đến URL này để xác nhận thanh toán
    """
    from store.models import VNPayPayment, Order, Cart
    from store.vnpay_utils import VNPayUtil
    import json
    
    try:
        # Lấy tất cả tham số từ request
        response_data = request.POST.dict()
        order_code = response_data.get('vnp_TxnRef', '')
        
        if not order_code:
            return JsonResponse({'RspCode': '01', 'Message': 'Invalid order code'})
        
        # Lấy bản ghi VNPay Payment
        try:
            vnpay_payment = VNPayPayment.objects.get(order_code=order_code)
        except VNPayPayment.DoesNotExist:
            return JsonResponse({'RspCode': '01', 'Message': 'Order not found'})
        
        # Xác minh response từ VNPay
        is_valid, message = VNPayUtil.verify_payment_response(response_data)
        
        response_code = response_data.get('vnp_ResponseCode', '')
        transaction_no = response_data.get('vnp_TransactionNo', '')
        
        if not is_valid:
            return JsonResponse({'RspCode': '02', 'Message': message})
        
        # Cập nhật thông tin thanh toán
        vnpay_payment.transaction_no = transaction_no
        vnpay_payment.response_code = response_code
        vnpay_payment.response_message = message
        
        if response_code == '00':
            vnpay_payment.status = 'paid'
            vnpay_payment.paid_at = timezone.now()
            vnpay_payment.save()
            
            # Ghi log hoặc xử lý thêm tại đây
            # Ví dụ: Tạo Order, gửi email, v.v.
            
            return JsonResponse({'RspCode': '00', 'Message': 'Confirmed'})
        else:
            vnpay_payment.status = 'failed'
            vnpay_payment.save()
            return JsonResponse({'RspCode': '02', 'Message': f'Payment failed: {message}'})

    except Exception as e:
        return JsonResponse({'RspCode': '99', 'Message': str(e)})


# ==================== MoMo Payment ====================

@login_required
def momo_create(request):
    from django.http import JsonResponse
    from django.utils import timezone

    try:
        amount = float(request.POST.get('amount', 0))
        items_param = request.POST.get('items_param', '')

        if amount <= 0:
            return JsonResponse({'success': False, 'message': 'Số tiền không hợp lệ'}, status=400)

        # Tạo order code (sẽ dùng để tạo Order sau khi thanh toán thành công)
        order_code = f"MO{timezone.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"

        order_id = f"QHUN22_{order_code}"
        # Dung ASCII cho order_info (moi voi signature)
        order_info = f"Pay QHUN22 order {order_code}"

        from store.momo_utils import MoMoUtil
        momo = MoMoUtil()
        result = momo.create_payment(int(amount), order_id, order_info)

        if result.get('error'):
            return JsonResponse({'success': False, 'message': result.get('message', 'Lỗi kết nối MoMo')})

        pay_url = result.get('payUrl')
        print(f"[MoMo] payUrl: {pay_url}")  # Debug
        if pay_url:
            # Lưu vào session để lấy lại khi MoMo redirect về
            request.session['momo_order_code'] = order_code
            request.session['momo_amount'] = int(amount)
            request.session['momo_items_param'] = items_param

            # Gửi Telegram thông báo có đơn MoMo mới
            from store.telegram_utils import notify_payment_created
            notify_payment_created('momo', order_code, request.user.username, int(amount))

            return JsonResponse({'success': True, 'payment_url': pay_url})
        else:
            # Log full response for debugging
            print(f"[MoMo] Full response: {result}")
            return JsonResponse({'success': False, 'message': 'Không thể tạo link thanh toán MoMo', 'debug': result})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def momo_return(request):
    from django.shortcuts import render, redirect
    from django.contrib import messages
    from django.views.decorators.csrf import csrf_exempt
    from store.models import Cart, Order, OrderItem, ProductDetail, FolderColorImage

    try:
        result_code = request.GET.get('resultCode') or (request.POST.get('resultCode') if request.method == 'POST' else None)
        order_id = request.GET.get('orderId') or (request.POST.get('orderId') if request.method == 'POST' else None)
        message = request.GET.get('message') or (request.POST.get('message') if request.method == 'POST' else None)
        amount = request.GET.get('amount') or (request.POST.get('amount') if request.method == 'POST' else None)

        # Lấy thông tin từ session
        order_code = request.session.get('momo_order_code')
        session_amount = request.session.get('momo_amount', 0)
        items_param = request.session.get('momo_items_param', '')

        if not order_code:
            if order_id:
                order_code = order_id.replace('QHUN22_', '') if order_id.startswith('QHUN22_') else order_id
            else:
                return render(request, 'store/payment/payment_error.html', {
                    'message': 'Không nhận được thông tin đơn hàng'
                })

        if result_code == '0':
            # Mã giao dịch MoMo để kiểm tra trùng
            momo_order_code = order_code

            # Đã xử lý đơn này rồi (user refresh hoặc MoMo redirect 2 lần) -> chỉ hiển thị success
            existing = Order.objects.filter(momo_order_code=momo_order_code, user=request.user).first()
            if existing:
                request.session.pop('momo_order_code', None)
                request.session.pop('momo_amount', None)
                request.session.pop('momo_items_param', None)
                return render(request, 'store/payment/payment_success.html', {
                    'order': existing,
                    'payment_method': 'MoMo'
                })

            # Tạo mã đơn hàng QHUN + 5 số ngẫu nhiên
            tracking_code = 'QHUN' + str(random.randint(10000, 99999))

            # Xóa session sau khi đã lấy xong
            request.session.pop('momo_order_code', None)
            request.session.pop('momo_amount', None)
            request.session.pop('momo_items_param', None)

            # Tạo Order mới
            order = Order.objects.create(
                user=request.user,
                order_code=tracking_code,
                momo_order_code=momo_order_code,
                total_amount=Decimal(session_amount) if session_amount else Decimal(0),
                payment_method='momo',
                status='processing'
            )

            # Lưu sản phẩm vào OrderItem trước khi xóa cart (giống VNPay)
            if items_param:
                try:
                    item_ids = [int(x) for x in items_param.split(',') if x.strip()]
                    cart = Cart.get_or_create_for_user(request.user)
                    if cart:
                        cart_items = cart.items.filter(id__in=item_ids).select_related('product', 'product__brand')
                        for ci in cart_items:
                            # Tìm thumbnail
                            thumb_url = ''
                            try:
                                if ci.product and ci.product.brand_id:
                                    detail = ProductDetail.objects.get(product=ci.product)
                                    variant = detail.variants.filter(
                                        is_active=True, color_name=ci.color_name
                                    ).first()
                                    if variant and variant.sku:
                                        img = FolderColorImage.objects.filter(
                                            brand_id=ci.product.brand_id,
                                            sku=variant.sku
                                        ).order_by('order').first()
                                        if img:
                                            thumb_url = img.image.url
                                if not thumb_url and ci.product and ci.product.image:
                                    thumb_url = ci.product.image.url
                            except Exception:
                                pass

                            OrderItem.objects.create(
                                order=order,
                                product=ci.product,
                                product_name=ci.product.name if ci.product else 'Sản phẩm',
                                color_name=ci.color_name,
                                storage=ci.storage,
                                quantity=ci.quantity,
                                price=ci.price_at_add,
                                thumbnail=thumb_url,
                            )
                        # Xóa cart items sau khi đã lưu
                        cart_items.delete()
                except (ValueError, TypeError):
                    pass

            from store.telegram_utils import notify_order_success
            from store.email_utils import send_order_invoice_email
            momo_items = list(order.items.values('product_name', 'quantity', 'storage', 'color_name'))
            notify_order_success(tracking_code, 'momo', momo_items)
            send_order_invoice_email(order, base_url=request.build_absolute_uri('/'))

            return render(request, 'store/payment/payment_success.html', {
                'order': order,
                'payment_method': 'MoMo'
            })
        else:
            return render(request, 'store/payment/payment_error.html', {
                'message': message or 'Thanh toán MoMo thất bại'
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return render(request, 'store/payment/payment_error.html', {
            'message': str(e)
        })


@csrf_exempt
def momo_ipn(request):
    from django.http import JsonResponse
    from django.views.decorators.csrf import csrf_exempt
    from store.models import Order

    try:
        result_code = request.POST.get('resultCode')
        order_id = request.POST.get('orderId')
        message = request.POST.get('message')

        if not order_id:
            return JsonResponse({'RspCode': '01', 'Message': 'Missing orderId'})

        try:
            order = Order.objects.get(momo_order_code=order_id)
        except Order.DoesNotExist:
            return JsonResponse({'RspCode': '01', 'Message': 'Order not found'})

        if result_code == '0':
            order.status = 'processing'
            order.save()
            return JsonResponse({'RspCode': '0', 'Message': 'Success'})
        else:
            order.status = 'cancelled'
            order.save()
            return JsonResponse({'RspCode': result_code, 'Message': message or 'Payment failed'})

    except Exception as e:
        return JsonResponse({'RspCode': '99', 'Message': str(e)})
