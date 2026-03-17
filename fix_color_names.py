"""
Fix corrupted color_name values in store_productvariant and store_cartitem.
Pattern: "SKU - SKU - ... - ActualColor" → "ActualColor"
"""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from store.models import ProductVariant, CartItem

# Fix ProductVariant
fixed_pv = 0
for pv in ProductVariant.objects.all():
    cn = (pv.color_name or '').strip()
    if not cn:
        continue
    # If color_name contains " - ", extract the last segment (actual color)
    if ' - ' in cn:
        actual = cn.rsplit(' - ', 1)[-1].strip()
        if actual and actual != cn:
            print(f"  ProductVariant #{pv.id} ({pv.sku}): '{cn}' → '{actual}'")
            pv.color_name = actual
            pv.save(update_fields=['color_name'])
            fixed_pv += 1

# Fix CartItem
fixed_ci = 0
for ci in CartItem.objects.all():
    cn = (ci.color_name or '').strip()
    if not cn:
        continue
    if ' - ' in cn:
        actual = cn.rsplit(' - ', 1)[-1].strip()
        if actual and actual != cn:
            print(f"  CartItem #{ci.id}: '{cn}' → '{actual}'")
            ci.color_name = actual
            ci.save(update_fields=['color_name'])
            fixed_ci += 1

print(f"\nDone: fixed {fixed_pv} ProductVariant(s), {fixed_ci} CartItem(s)")
