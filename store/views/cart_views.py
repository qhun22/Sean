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
            item.color_thumbnail = ''  # Ảnh màu hiện tại

            # Lấy variants để biết các màu có sẵn
            try:
                detail = ProductDetail.objects.get(product=product)
                variants = detail.variants.filter(is_active=True)

                # Tìm original_price của variant hiện tại
                current_variant = variants.filter(
                    color_name=item.color_name,
                    storage=item.storage
                ).first()
                if current_variant and current_variant.original_price > current_variant.price:
                    item.original_price = current_variant.original_price

                # Lấy unique colors với SKU
                seen_colors = {}
                color_variants = []
                for v in variants.order_by('color_name'):
                    if v.color_name not in seen_colors:
                        seen_colors[v.color_name] = True
                        color_variants.append(v)

                # Lấy ảnh thumbnail cho từng màu từ FolderColorImage
                if product.brand_id:
                    sku_list = list(set(v.sku for v in color_variants if v.sku))
                    folder_images = {}
                    if sku_list:
                        imgs = FolderColorImage.objects.filter(
                            brand_id=product.brand_id,
                            sku__in=sku_list
                        ).order_by('sku', 'order')
                        for img in imgs:
                            if img.sku not in folder_images:
                                folder_images[img.sku] = img.image.url

                    for v in color_variants:
                        thumb = folder_images.get(v.sku, '')
                        item.color_options.append({
                            'color_name': v.color_name,
                            'sku': v.sku or '',
                            'thumbnail': thumb,
                            'is_selected': v.color_name == item.color_name,
                        })
                        # Lưu thumbnail của màu hiện tại
                        if v.color_name == item.color_name and thumb:
                            item.color_thumbnail = thumb

                # Lấy storage options cho màu hiện tại
                item.storage_options = []
                storage_variants = variants.filter(
                    color_name=item.color_name
                ).order_by('price')
                for sv in storage_variants:
                    item.storage_options.append({
                        'storage': sv.storage,
                        'price': int(sv.price),
                        'is_selected': sv.storage == item.storage,
                    })
            except ProductDetail.DoesNotExist:
                pass
    else:
        cart_items = []

    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'store/cart.html', context)



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

    # Lấy thông tin từ request
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    color_name = request.POST.get('color_name', '')
    color_code = request.POST.get('color_code', '')
    storage = request.POST.get('storage', '')
    price = request.POST.get('price', 0)

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

    # Kiểm tra tồn kho trước khi thêm vào giỏ
    from store.models import ProductDetail
    available_stock = product.stock  # Mặc định dùng Product.stock
    
    # Nếu có color_name và storage, kiểm tra ProductVariant.stock_quantity
    if color_name and storage:
        try:
            detail = ProductDetail.objects.get(product=product)
            variant = detail.variants.filter(
                color_name=color_name,
                storage=storage,
                is_active=True
            ).first()
            if variant and variant.stock_quantity > 0:
                available_stock = variant.stock_quantity
            # Nếu variant không có stock riêng, giữ nguyên product.stock
        except ProductDetail.DoesNotExist:
            pass
    
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
        # Thêm mới
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

    # Đếm tổng số sản phẩm trong giỏ
    total_items = cart.get_total_items()

    return JsonResponse({
        'success': True,
        'message': message,
        'total_items': total_items,
        'item_quantity': item.quantity,
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
    new_color = request.POST.get('color_name', '')

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

    # Tìm variant mới theo color + storage
    try:
        detail = ProductDetail.objects.get(product=item.product)
        new_variant = detail.variants.filter(
            color_name=new_color,
            storage=item.storage,
            is_active=True
        ).first()

        if not new_variant:
            # Nếu không tìm thấy variant cùng storage, lấy variant đầu tiên của màu đó
            new_variant = detail.variants.filter(
                color_name=new_color,
                is_active=True
            ).first()

        if new_variant:
            # Kiểm tra xem đã có item cùng product + color + storage chưa
            existing = CartItem.objects.filter(
                cart=item.cart,
                product=item.product,
                color_name=new_color,
                storage=new_variant.storage
            ).exclude(id=item.id).first()

            if existing:
                # Gộp vào item đã có
                existing.quantity += item.quantity
                existing.save()
                item.delete()
                item = existing
            else:
                item.color_name = new_color
                item.storage = new_variant.storage
                item.price_at_add = new_variant.price
                item.save()

            cart = item.cart
            total_price = cart.get_total_price()
            item_total = item.get_total_price()
            total_items = cart.get_total_items()

            # Lấy thumbnail của màu mới
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
                'message': f'Đã đổi sang màu {new_color}',
                'total_items': total_items,
                'total_price': int(total_price),
                'item_total': int(item_total),
                'item_price': int(new_variant.price),
                'original_price': int(new_variant.original_price) if new_variant.original_price > new_variant.price else 0,
                'new_color': new_color,
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
    new_storage = request.POST.get('storage', '')

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

    # Tìm variant mới theo color hiện tại + storage mới
    try:
        detail = ProductDetail.objects.get(product=item.product)
        new_variant = detail.variants.filter(
            color_name=item.color_name,
            storage=new_storage,
            is_active=True
        ).first()

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
            total_items = cart.get_total_items()

            return JsonResponse({
                'success': True,
                'message': f'Đã đổi sang {new_storage}',
                'total_items': total_items,
                'total_price': int(total_price),
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
