# Generated migration for ProductVariant: original_price, discount_percent

from django.db import migrations, models


def set_original_price_from_price(apps, schema_editor):
    ProductVariant = apps.get_model('store', 'ProductVariant')
    for v in ProductVariant.objects.all():
        if v.original_price == 0 and v.price and int(v.price) > 0:
            v.original_price = v.price
            v.save(update_fields=['original_price'])


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0013_imagefolder_foldercolorimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='productvariant',
            name='original_price',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Giá gốc (VNĐ)'),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='discount_percent',
            field=models.PositiveIntegerField(default=0, verbose_name='% Giảm giá'),
        ),
        migrations.RunPython(set_original_price_from_price, migrations.RunPython.noop),
    ]
