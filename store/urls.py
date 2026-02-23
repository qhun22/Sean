"""
URL configuration cho ứng dụng store
"""
from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Trang chủ
    path('', views.home, name='home'),
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
    # Quên mật khẩu
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('send-otp-forgot-password/', views.send_otp_forgot_password_view, name='send_otp_forgot_password'),
    path('verify-otp-forgot-password/', views.verify_otp_forgot_password_view, name='verify_otp_forgot_password'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
]
