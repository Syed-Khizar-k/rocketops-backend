from django.db import migrations
from django.utils.text import slugify

def update_slugs(apps, schema_editor):
    Product = apps.get_model('api', 'Product')
    for product in Product.objects.all():
        new_slug = slugify(product.title)
        if product.slug != new_slug:
            product.slug = new_slug
            product.save()

def reverse_slugs(apps, schema_editor):
    # This is a bit tricky to reverse exactly, but we can prefix with explore- if needed
    # However, usually data migrations like this are one-way or we just leave them.
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0011_casestudy_product_alter_casestudy_link'),
    ]

    operations = [
        migrations.RunPython(update_slugs, reverse_slugs),
    ]
