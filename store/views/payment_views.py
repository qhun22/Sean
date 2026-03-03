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
    Tạo đơn hàng VietQR (awaiting_payment) + PendingQRPayment,
    trả về URL trang thanh toán VietQR riêng.
    """
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
    
    tracking_code = 'QHUN' + str(_rand.randint(10000, 99999))
    
    digits = '0123456789'
    transfer_code = 'QHUN'
    for _ in range(5):
        transfer_code += digits[_rand.randint(0, 9)]
    
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
    
    cart.items.filter(id__in=item_ids).delete()
    
    PendingQRPayment.objects.create(
        user=request.user,
        amount=total_amount,
        transfer_code=transfer_code,
    )
    
    from store.telegram_utils import notify_payment_created
    notify_payment_created('vietqr', tracking_code, request.user.username, total_amount)
    
    return JsonResponse({
        'success': True,
        'redirect_url': '/vietqr-payment/?order=' + tracking_code + '&code=' + transfer_code,
    })



@login_required
def vietqr_payment_page(request):
    """
    Trang thanh toán VietQR riêng - hiển thị QR, timer, polling admin duyệt.
    """
    from store.models import Order, PendingQRPayment
    
    order_code = request.GET.get('order', '')
    transfer_code = request.GET.get('code', '')
    
    if not order_code or not transfer_code:
        messages.error(request, 'Thiếu thông tin thanh toán')
        return redirect('store:cart_detail')
    
    try:
        order = Order.objects.get(order_code=order_code, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, 'Không tìm thấy đơn hàng')
        return redirect('store:cart_detail')
    
    if order.status not in ('awaiting_payment', 'processing'):
        return redirect('store:order_success', order_code=order_code)
    
    qr = PendingQRPayment.objects.filter(
        transfer_code=transfer_code, user=request.user
    ).first()
    
    timeout_seconds = 15 * 60
    if qr and qr.created_at:
        elapsed = (timezone.now() - qr.created_at).total_seconds()
        timeout_seconds = max(0, int(15 * 60 - elapsed))
    
    if timeout_seconds <= 0 and order.status == 'awaiting_payment':
        order.status = 'cancelled'
        order.save()
        # Không xóa PendingQRPayment — giữ lại lịch sử
    
    context = {
        'order': order,
        'transfer_code': transfer_code,
        'timeout_seconds': timeout_seconds,
        'bank_id': settings.BANK_ID,
        'bank_account_no': settings.BANK_ACCOUNT_NO,
        'bank_account_name': settings.BANK_ACCOUNT_NAME,
    }
    return render(request, 'store/vietqr_payment.html', context)



@login_required
def vietqr_page_status(request):
    """
    Polling API cho trang VietQR riêng.
    GET: code, order_code
    """
    from store.models import PendingQRPayment, Order
    
    code = request.GET.get('code', '')
    order_code = request.GET.get('order_code', '')
    
    if not code:
        return JsonResponse({'success': False, 'status': 'error'})
    
    try:
        qr = PendingQRPayment.objects.get(transfer_code=code, user=request.user)
    except PendingQRPayment.DoesNotExist:
        try:
            order = Order.objects.get(order_code=order_code, user=request.user)
            if order.status in ('processing', 'pending', 'delivered'):
                return JsonResponse({'success': True, 'status': 'approved'})
        except Order.DoesNotExist:
            pass
        return JsonResponse({'success': True, 'status': 'expired'})
    
    if qr.is_expired:
        # Không xóa trực tiếp, để cleanup_expired() xử lý theo lịt
        return JsonResponse({'success': True, 'status': 'expired'})
        try:
            order = Order.objects.get(order_code=order_code, user=request.user)
            if order.status == 'awaiting_payment':
                order.status = 'processing'
                order.save()
                
                from store.telegram_utils import notify_order_success
                vqr_items = list(order.items.values('product_name', 'quantity', 'storage', 'color_name'))
                notify_order_success(order_code, 'vietqr', vqr_items)
        except Order.DoesNotExist:
            pass
        # Giữ lại record để lưu lịch sử duyệt QR
        return JsonResponse({'success': True, 'status': 'approved'})
    
    if qr.status == 'cancelled':
        return JsonResponse({'success': True, 'status': 'cancelled'})
    
    return JsonResponse({'success': True, 'status': 'pending'})



@csrf_exempt
@login_required
@require_POST
def vietqr_expire(request):
    """
    Client báo hết thời gian → huỷ đơn + xoá QR pending.
    """
    from store.models import Order, PendingQRPayment
    import json
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False})
    
    order_code = data.get('order_code', '')
    transfer_code = data.get('transfer_code', '')
    
    if order_code:
        try:
            order = Order.objects.get(order_code=order_code, user=request.user)
            if order.status == 'awaiting_payment':
                order.status = 'cancelled'
                order.save()
        except Order.DoesNotExist:
            pass
    
    if transfer_code:
        # Chỉ xóa nếu vẫn còn pending — không xóa approved/cancelled để giữ lịch sử
        PendingQRPayment.objects.filter(
            transfer_code=transfer_code, user=request.user, status='pending'
        ).delete()
    
    return JsonResponse({'success': True})



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
            'created_at': qr.created_at.strftime('%d/%m/%Y %H:%M:%S'),
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
            'created_at': qr.created_at.strftime('%d/%m/%Y %H:%M:%S'),
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
            vnpay_items = list(order.items.values('product_name', 'quantity', 'storage', 'color_name'))
            notify_order_success(tracking_code, 'vnpay', vnpay_items)
            
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
