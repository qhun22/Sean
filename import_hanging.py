import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from store.models import Product, HangingProduct

# Lấy tất cả sản phẩm đang active
products = Product.objects.filter(is_active=True)

# Import vào HangingProduct
count = 0
for p in products:
    # Kiểm tra đã tồn tại chưa
    if not HangingProduct.objects.filter(name=p.name, brand=p.brand).exists():
        HangingProduct.objects.create(
            brand=p.brand,
            name=p.name,
            original_price=p.price,
            discount_percent=0,
            stock_quantity=p.stock,
            installment_0_percent=False,
            is_active=True
        )
        count += 1

print('Da them', count, 'san pham vao HangingProduct')
print('Tong san pham trong HangingProduct:', HangingProduct.objects.count())
