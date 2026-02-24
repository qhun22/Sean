"""
URL configuration cho ứng dụng store
"""
from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Trang chủ
    path('', views.home, name='home'),
    # Chi tiết sản phẩm
    path('product/<int:product_id>/', views.product_detail_view, name='product_detail'),
    # Tìm kiếm sản phẩm
    path('products/search/', views.product_search, name='product_search'),
    # Giỏ hàng
    path('cart/', views.cart_detail, name='cart_detail'),
    # Tra cứu đơn hàng
    path('order-tracking/', views.order_tracking, name='order_tracking'),
    # Yêu thích
    path('wishlist/', views.wishlist, name='wishlist'),
    # Tài khoản
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('send-otp/', views.send_otp_view, name='send_otp'),
    path('profile/', views.profile, name='profile'),
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    # Quản lý hãng
    path('brands/', views.brand_list, name='brand_list'),
    path('brands/add/', views.brand_add, name='brand_add'),
    path('brands/edit/', views.brand_edit, name='brand_edit'),
    path('brands/delete/', views.brand_delete, name='brand_delete'),
    # Quản lý người dùng
    path('users/edit/', views.user_edit, name='user_edit'),
    path('users/delete/', views.user_delete, name='user_delete'),
    # Quan ly san pham
    path('products/add/', views.product_add, name='product_add'),
    path('products/edit/', views.product_edit, name='product_edit'),
    path('products/delete/', views.product_delete, name='product_delete'),
    # Chi tiet san pham
    path('products/detail/save/', views.product_detail_save, name='product_detail_save'),
    path('products/detail/get/', views.get_product_detail, name='get_product_detail'),
    path('products/variant/save/', views.product_variant_save, name='product_variant_save'),
    path('products/variant/delete/', views.product_variant_delete, name='product_variant_delete'),
    path('products/image/upload/', views.product_image_upload, name='product_image_upload'),
    path('products/image/delete/', views.product_image_delete, name='product_image_delete'),
    # Quen mat khau
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('send-otp-forgot-password/', views.send_otp_forgot_password_view, name='send_otp_forgot_password'),
    path('verify-otp-forgot-password/', views.verify_otp_forgot_password_view, name='verify_otp_forgot_password'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
]
