import os
import django
from django.utils.text import slugify

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rocketops_core.settings')
django.setup()

from api.models import Product

def fix_product_slugs():
    print("Starting product slug fix...")
    products = Product.objects.all()
    count = 0
    for product in products:
        new_slug = slugify(product.title)
        if product.slug != new_slug:
            old_slug = product.slug
            product.slug = new_slug
            product.save()
            print(f"Updated: '{product.title}' | {old_slug} -> {new_slug}")
            count += 1
        else:
            print(f"Skipping: '{product.title}' | Slug already correct: {product.slug}")
    
    print(f"\nDone! Updated {count} products.")

if __name__ == "__main__":
    fix_product_slugs()
