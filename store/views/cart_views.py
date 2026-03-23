"""
Cart Views (add, remove, update) - QHUN22 Store
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



def cart_detail(request):
    """
    Chi tiết giỏ hàng
    Hiển thị các sản phẩm trong giỏ hàng
    """
    from store.models import Cart, FolderColorImage, ProductDetail, ProductVariant

    cart = Cart.get_or_create_for_user(request.user)

    if cart:
        # Lấy các item trong giỏ hàng
        cart_items = list(cart.items.select_related('product', 'product__brand').order_by('-created_at'))

        # Lấy color options cho từng item (ảnh thumbnail + tên màu)
        for item in cart_items:
            product = item.product
            item.color_options = []
            item.original_price = None
            item.color_thumbnail = ''

            # Chuẩn hóa để so khớp (strip)
            item_color_name = (item.color_name or '').strip()
            item_storage = (item.storage or '').strip()

            # Hiển thị: template cần display_color, display_storage, display_price
            item.display_color = item_color_name or 'Mặc định'
            item.display_storage = item_storage or 'Mặc định'
            try:
                item.display_price = Decimal(str(item.price_at_add or 0)) if (item.price_at_add is not None and item.price_at_add != '') else Decimal('0')
            except Exception:
                item.display_price = Decimal('0')
            if item.display_price <= 0:
                try:
                    detail_p = ProductDetail.objects.get(product=product)
                    if detail_p.discounted_price:
                        item.display_price = Decimal(str(detail_p.discounted_price))
                    elif detail_p.summary_original_price:
                        item.display_price = Decimal(str(detail_p.summary_original_price))
                except ProductDetail.DoesNotExist:
                    pass
                if item.display_price <= 0 and product.price:
                    item.display_price = Decimal(str(product.price))
                if item.display_price <= 0 and product.original_price:
                    item.display_price = Decimal(str(product.original_price))

            # Lấy variants để biết các màu có sẵn
            try:
                detail = ProductDetail.objects.get(product=product)
                variants = detail.variants.filter(is_active=True)

                # Tìm variant hiện tại (exact + normalized) để lấy giá
                current_variant = variants.filter(
                    color_name=item_color_name,
                    storage=item_storage
                ).first()
                if not current_variant and (item_color_name or item_storage):
                    ic_norm = item_color_name.split(' - ', 1)[1].strip() if ' - ' in item_color_name else item_color_name
                    for v in variants:
                        vc = (v.color_name or '').strip()
                        vc_norm = vc.split(' - ', 1)[1].strip() if ' - ' in vc else vc
                        if vc_norm == ic_norm and (v.storage or '').strip() == item_storage:
                            current_variant = v
                            break
                if current_variant:
                    if getattr(current_variant, 'original_price', None) and current_variant.original_price > current_variant.price:
                        item.original_price = current_variant.original_price
                    if (not item.display_price or item.display_price <= 0) and current_variant.price:
                        item.display_price = Decimal(str(current_variant.price))

                # Lấy unique colors với SKU
                seen_colors = {}
                color_variants = []
                for v in variants.order_by('color_name'):
                    if v.color_name not in seen_colors:
                        seen_colors[v.color_name] = True
                        color_variants.append(v)

                folder_images = {}
                if product.brand_id:
                    sku_list = list(set(v.sku for v in color_variants if v.sku))
                    if sku_list:
                        imgs = FolderColorImage.objects.filter(
                            brand_id=product.brand_id,
                            sku__in=sku_list
                        ).order_by('sku', 'order')
                        for img in imgs:
                            if img.sku not in folder_images:
                                folder_images[img.sku] = img.image.url

                item_color_norm = item_color_name.split(' - ', 1)[1].strip() if ' - ' in item_color_name else item_color_name
                for v in color_variants:
                    thumb = folder_images.get(v.sku, '')
                    v_norm = (v.color_name or '').strip()
                    if ' - ' in v_norm:
                        v_norm = v_norm.split(' - ', 1)[1].strip()
                    is_selected = (v.color_name == item_color_name) or (v_norm == item_color_norm and item_color_norm)
                    item.color_options.append({
                        'color_name': v.color_name,
                        'sku': v.sku or '',
                        'thumbnail': thumb,
                        'is_selected': is_selected,
                    })
                    if is_selected and thumb:
                        item.color_thumbnail = thumb
                    if is_selected:
                        item.display_color = v.color_name

                if item.color_options and not any(o['is_selected'] for o in item.color_options):
                    item.display_color = item.color_options[0]['color_name']
                    for o in item.color_options:
                        o['is_selected'] = (o['color_name'] == item.display_color)

                # Storage options
                item.storage_options = []
                storage_variants = variants.filter(color_name=item_color_name).order_by('price')
                if not storage_variants.exists() and item_color_norm:
                    for v in variants:
                        vc = (v.color_name or '').strip()
                        vc_n = vc.split(' - ', 1)[1].strip() if ' - ' in vc else vc
                        if vc_n == item_color_norm:
                            storage_variants = variants.filter(color_name=v.color_name).order_by('price')
                            break
                if not storage_variants.exists():
                    storage_variants = variants.order_by('price')
                for sv in storage_variants:
                    is_s = (sv.storage or '').strip() == item_storage
                    item.storage_options.append({
                        'storage': sv.storage,
                        'price': int(sv.price),
                        'is_selected': is_s,
                    })
                    if is_s:
                        item.display_storage = sv.storage
                if item.storage_options and not any(o['is_selected'] for o in item.storage_options):
                    item.display_storage = item.storage_options[0]['storage']
                    for o in item.storage_options:
                        o['is_selected'] = (o['storage'] == item.display_storage)
            except ProductDetail.DoesNotExist:
                pass
    else:
        cart_items = []

    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'store/cart/cart.html', context)



@require_POST
def cart_add(request):
    """
    API thêm sản phẩm vào giỏ hàng (AJAX)
    """
    from store.models import Cart, CartItem, Product

    # Kiểm tra user đã đăng nhập chưa
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Vui lòng đăng nhập để thêm vào giỏ hàng',
            'require_login': True,
        }, status=401)

    # Lấy thông tin từ request (chuẩn hóa)
    product_id = (request.POST.get('product_id') or '').strip()
    quantity = int(request.POST.get('quantity', 1))
    color_name = (request.POST.get('color_name') or '').strip()
    color_code = (request.POST.get('color_code') or '').strip()
    storage = (request.POST.get('storage') or '').strip()
    raw_price = (request.POST.get('price') or '').strip()
    try:
        price = Decimal(raw_price) if raw_price else Decimal('0')
    except Exception:
        price = Decimal('0')

    if not product_id:
        return JsonResponse({
            'success': False,
            'message': 'Thiếu product_id',
        }, status=400)

    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Sản phẩm không tồn tại',
        }, status=404)

    from store.models import ProductDetail, ProductVariant
    detail = None
    variant = None
    try:
        detail = ProductDetail.objects.get(product=product)
    except ProductDetail.DoesNotExist:
        pass
    variants_qs = ProductVariant.objects.filter(detail__product=product) if detail else ProductVariant.objects.none()

    # Thêm từ Home/Wishlist: chưa có màu/dung lượng -> chọn 1 variant active
    if not color_name or not storage:
        active = list(variants_qs.filter(is_active=True))
        cand = active if active else list(variants_qs)
        if cand:
            in_stock = [v for v in cand if (v.stock_quantity or 0) > 0]
            v = random.choice(in_stock if in_stock else cand)
            variant = v
            color_name = v.color_name or ''
            storage = v.storage or ''
            color_code = v.color_hex or color_code

    # Đã có màu + dung lượng (từ chi tiết SP): map sang variant
    if color_name and storage and variant is None and detail:
        variant = detail.variants.filter(
            color_name=color_name,
            storage=storage,
            is_active=True
        ).first()
        if variant is None:
            variant = detail.variants.filter(color_name=color_name, storage=storage).first()
        if variant is None:
            c_norm = color_name.split(' - ', 1)[1].strip() if ' - ' in color_name else color_name
            for v in detail.variants.filter(is_active=True):
                vn = (v.color_name or '').strip()
                vn = vn.split(' - ', 1)[1].strip() if ' - ' in vn else vn
                if vn == c_norm and (v.storage or '').strip() == storage:
                    variant = v
                    color_name = v.color_name or color_name
                    storage = v.storage or storage
                    break
        if variant and (color_name != variant.color_name or storage != variant.storage):
            color_name = variant.color_name or color_name
            storage = variant.storage or storage

    if (not color_name or not storage) and variant is None and variants_qs.exists():
        variant = variants_qs.order_by('id').first()
        if variant:
            color_name = variant.color_name or color_name
            storage = variant.storage or storage
            color_code = variant.color_hex or color_code

    if price <= 0 and variant:
        price = Decimal(str(variant.price)) if variant.price else Decimal('0')
    if price <= 0 and detail:
        if detail.discounted_price:
            price = Decimal(str(detail.discounted_price))
        elif detail.summary_original_price:
            price = Decimal(str(detail.summary_original_price))
    if price <= 0 and product.price:
        price = Decimal(str(product.price))
    if price <= 0 and product.original_price:
        price = Decimal(str(product.original_price))

    available_stock = product.stock
    if color_name and storage and variant and (variant.stock_quantity or 0) > 0:
        available_stock = variant.stock_quantity

    if available_stock <= 0:
        return JsonResponse({
            'success': False,
            'message': 'Sản phẩm đã hết hàng!',
        }, status=400)
    
    if quantity > available_stock:
        return JsonResponse({
            'success': False,
            'message': f'Chỉ còn {available_stock} sản phẩm trong kho!',
        }, status=400)

    # Lấy hoặc tạo giỏ hàng cho user
    cart = Cart.get_or_create_for_user(request.user)

    # Kiểm tra xem sản phẩm đã có trong giỏ chưa (cùng màu, cùng storage)
    existing_item = CartItem.objects.filter(
        cart=cart,
        product=product,
        color_name=color_name,
        storage=storage
    ).first()

    if existing_item:
        # Kiểm tra tổng số lượng mới có vượt quá stock không
        new_quantity = existing_item.quantity + quantity
        if new_quantity > available_stock:
            return JsonResponse({
                'success': False,
                'message': f'Không thể thêm! Trong giỏ đã có {existing_item.quantity}, kho chỉ còn {available_stock} sản phẩm.',
            }, status=400)
        # Tăng số lượng
        existing_item.quantity = new_quantity
        existing_item.save()
        item = existing_item
        message = 'Đã cập nhật số lượng sản phẩm trong giỏ hàng'
    else:
        # Thêm mới (luôn lưu màu + dung lượng + giá)
        item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=quantity,
            color_name=color_name,
            color_code=color_code,
            storage=storage,
            price_at_add=price
        )
        message = 'Đã thêm sản phẩm vào giỏ hàng'

    total_items = cart.get_total_items()
    return JsonResponse({
        'success': True,
        'message': message,
        'total_items': total_items,
        'item_quantity': item.quantity,
        'selected_color': item.color_name,
        'selected_storage': item.storage,
        'selected_price': str(item.price_at_add),
    })



@require_POST
def cart_remove(request):
    """
    API xóa sản phẩm khỏi giỏ hàng (AJAX)
    """
    from store.models import Cart, CartItem

    # Kiểm tra user đã đăng nhập chưa
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Vui lòng đăng nhập',
            'require_login': True,
        }, status=401)

    # Lấy item_id từ request
    item_id = request.POST.get('item_id')
    if not item_id:
        return JsonResponse({
            'success': False,
            'message': 'Thiếu item_id',
        }, status=400)

    try:
        item = CartItem.objects.get(id=item_id, cart__user=request.user)
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Sản phẩm không tồn tại trong giỏ hàng',
        }, status=404)

    cart = item.cart
    item.delete()

    # Đếm tổng số sản phẩm trong giỏ
    total_items = cart.get_total_items()

    return JsonResponse({
        'success': True,
        'message': 'Đã xóa sản phẩm khỏi giỏ hàng',
        'total_items': total_items,
    })



@require_POST
def cart_update_quantity(request):
    """
    API cập nhật số lượng sản phẩm trong giỏ hàng (AJAX)
    """
    from store.models import Cart, CartItem

    # Kiểm tra user đã đăng nhập chưa
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Vui lòng đăng nhập',
            'require_login': True,
        }, status=401)

    # Lấy item_id và quantity từ request
    item_id = request.POST.get('item_id')
    quantity = int(request.POST.get('quantity', 1))

    if not item_id:
        return JsonResponse({
            'success': False,
            'message': 'Thiếu item_id',
        }, status=400)

    if quantity < 1:
        return JsonResponse({
            'success': False,
            'message': 'Số lượng không được nhỏ hơn 1',
        }, status=400)

    try:
        item = CartItem.objects.get(id=item_id, cart__user=request.user)
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Sản phẩm không tồn tại trong giỏ hàng',
        }, status=404)

    cart = item.cart
    item.quantity = quantity
    item.save()

    # Tính lại tổng tiền
    total_price = cart.get_total_price()
    item_total = item.get_total_price()
    total_items = cart.get_total_items()

    return JsonResponse({
        'success': True,
        'message': 'Đã cập nhật số lượng',
        'total_items': total_items,
        'total_price': int(total_price),
        'item_total': int(item_total),
        'item_quantity': item.quantity,
    })



@require_POST
def cart_change_color(request):
    """
    API đổi màu sản phẩm trong giỏ hàng (AJAX)
    Cập nhật color_name, color_code và giá theo variant mới
    """
    from store.models import Cart, CartItem, ProductDetail, ProductVariant

    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Vui lòng đăng nhập',
            'require_login': True,
        }, status=401)

    item_id = request.POST.get('item_id')
    new_color = (request.POST.get('color_name', '') or '').strip()

    if not item_id or not new_color:
        return JsonResponse({
            'success': False,
            'message': 'Thiếu thông tin',
        }, status=400)

    try:
        item = CartItem.objects.get(id=item_id, cart__user=request.user)
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Sản phẩm không tồn tại trong giỏ hàng',
        }, status=404)

    # Tìm variant mới theo color + storage (exact + normalized)
    try:
        detail = ProductDetail.objects.get(product=item.product)
        variants = detail.variants.filter(is_active=True)
        current_storage = (item.storage or '').strip()
        if not current_storage or current_storage == 'Mặc định':
            for v in variants:
                suf = (v.color_name.split(' - ', 1)[1] if ' - ' in v.color_name else v.color_name).strip()
                if suf == (new_color.split(' - ', 1)[1].strip() if ' - ' in new_color else new_color):
                    current_storage = v.storage
                    break
            if not current_storage:
                fv = variants.order_by('price').first()
                if fv:
                    current_storage = fv.storage

        new_variant = variants.filter(
            color_name=new_color,
            storage=current_storage
        ).first()
        if not new_variant:
            new_color_norm = new_color.split(' - ', 1)[1].strip() if ' - ' in new_color else new_color
            for v in variants:
                suf = (v.color_name.split(' - ', 1)[1] if ' - ' in v.color_name else v.color_name).strip()
                if suf == new_color_norm and (not current_storage or v.storage == current_storage):
                    new_variant = v
                    break
        if not new_variant:
            new_variant = variants.filter(color_name=new_color).first()
        if not new_variant:
            new_variant = variants.first()

        if new_variant:
            final_color = new_variant.color_name or new_color
            display_color = final_color
            if ' - ' in display_color:
                display_color = display_color.split(' - ', 1)[1].strip() or final_color
            # Kiểm tra xem đã có item cùng product + color + storage chưa
            existing = CartItem.objects.filter(
                cart=item.cart,
                product=item.product,
                color_name=final_color,
                storage=new_variant.storage
            ).exclude(id=item.id).first()

            if existing:
                existing.quantity += item.quantity
                existing.save()
                item.delete()
                item = existing
            else:
                item.color_name = final_color
                item.color_code = new_variant.color_hex or item.color_code
                item.storage = new_variant.storage
                item.price_at_add = new_variant.price
                item.save()

            cart = item.cart
            total_price = cart.get_total_price()
            item_total = item.get_total_price()
            total_items = cart.get_total_items()

            new_thumbnail = ''
            if new_variant.sku and item.product.brand_id:
                from store.models import FolderColorImage
                thumb_img = FolderColorImage.objects.filter(
                    brand_id=item.product.brand_id,
                    sku=new_variant.sku
                ).order_by('order').first()
                if thumb_img:
                    new_thumbnail = thumb_img.image.url

            return JsonResponse({
                'success': True,
                'message': f'Đã đổi sang màu {display_color}',
                'total_items': total_items,
                'total_price': int(total_price),
                'item_total': int(item_total),
                'item_price': int(new_variant.price),
                'original_price': int(new_variant.original_price) if new_variant.original_price > new_variant.price else 0,
                'new_color': display_color,
                'new_storage': new_variant.storage,
                'new_thumbnail': new_thumbnail,
            })

    except ProductDetail.DoesNotExist:
        pass

    return JsonResponse({
        'success': False,
        'message': 'Không tìm thấy biến thể phù hợp',
    }, status=400)



@require_POST
def cart_change_storage(request):
    """
    API đổi dung lượng sản phẩm trong giỏ hàng (AJAX)
    Cập nhật storage và giá theo variant mới
    """
    from store.models import Cart, CartItem, ProductDetail, ProductVariant

    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Vui lòng đăng nhập',
            'require_login': True,
        }, status=401)

    item_id = request.POST.get('item_id')
    new_storage = (request.POST.get('storage', '') or '').strip()

    if not item_id or not new_storage:
        return JsonResponse({
            'success': False,
            'message': 'Thiếu thông tin',
        }, status=400)

    try:
        item = CartItem.objects.get(id=item_id, cart__user=request.user)
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Sản phẩm không tồn tại trong giỏ hàng',
        }, status=404)

    # Tìm variant mới theo color hiện tại + storage mới (exact + normalized)
    try:
        detail = ProductDetail.objects.get(product=item.product)
        variants = detail.variants.filter(is_active=True)
        current_color = (item.color_name or '').strip()
        new_variant = variants.filter(
            color_name=current_color,
            storage=new_storage
        ).first()
        if not new_variant and current_color:
            c_norm = current_color.split(' - ', 1)[1].strip() if ' - ' in current_color else current_color
            for v in variants:
                vn = (v.color_name or '').strip()
                vn = vn.split(' - ', 1)[1].strip() if ' - ' in vn else vn
                if vn == c_norm and (v.storage or '').strip() == new_storage:
                    new_variant = v
                    break
        if not new_variant:
            new_variant = variants.filter(storage=new_storage).first()

        if new_variant:
            # Kiểm tra xem đã có item cùng product + color + storage chưa
            existing = CartItem.objects.filter(
                cart=item.cart,
                product=item.product,
                color_name=item.color_name,
                storage=new_storage
            ).exclude(id=item.id).first()

            if existing:
                # Gộp vào item đã có
                existing.quantity += item.quantity
                existing.save()
                item.delete()
                item = existing
            else:
                item.storage = new_storage
                item.price_at_add = new_variant.price
                item.save()

            cart = item.cart
            total_price = cart.get_total_price()
            item_total = item.get_total_price()
            total_items = cart.get_total_items()

            return JsonResponse({
                'success': True,
                'message': f'Đã đổi sang {new_storage}',
                'total_items': total_items,
                'total_price': int(total_price),
                'item_total': int(item_total),
                'item_price': int(new_variant.price),
                'original_price': int(new_variant.original_price) if new_variant.original_price > new_variant.price else 0,
                'new_storage': new_storage,
            })

    except ProductDetail.DoesNotExist:
        pass

    return JsonResponse({
        'success': False,
        'message': 'Không tìm thấy biến thể phù hợp',
    }, status=400)
