import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
from store.models import ProductVariant, CartItem

print("=== ProductVariant SKUs ===")
variants = ProductVariant.objects.all()
for v in variants[:30]:
    print(f"  ID={v.id} SKU=[{v.sku}] color=[{v.color_name}] storage=[{v.storage}]")

print()
print("=== CartItem data ===")
items = CartItem.objects.all()
for i in items[:20]:
    print(f"  ID={i.id} product=[{i.product.name}] color=[{i.color_name}] code=[{i.color_code}] storage=[{i.storage}] price={i.price_at_add}")
