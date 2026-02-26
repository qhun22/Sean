"""
Cấu hình URL cho dự án QHUN22
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from store import views as store_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    # VNPay Payment Gateway
    path('vnpay/return/', store_views.vnpay_return, name='vnpay_return'),
    path('vnpay/ipn/', store_views.vnpay_ipn, name='vnpay_ipn'),
    path('', include('store.urls')),
]

# Cấu hình static và media files trong môi trường phát triển
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
