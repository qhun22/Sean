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
    # Quên mật khẩu
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('send-otp-forgot-password/', views.send_otp_forgot_password_view, name='send_otp_forgot_password'),
    path('verify-otp-forgot-password/', views.verify_otp_forgot_password_view, name='verify_otp_forgot_password'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
]
