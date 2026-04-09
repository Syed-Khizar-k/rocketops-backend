import os
import django
import shutil
from django.core.files import File

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rocketops_core.settings')
django.setup()

from api.models import CompanyCategory, CompanyLogo

# Paths
FRONTEND_LOGOS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'RocketOps', 'public', 'home', 'logos'))
MEDIA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'media', 'company_logos'))

if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

def seed_data():
    # Clear existing data
    CompanyLogo.objects.all().delete()
    CompanyCategory.objects.all().delete()

    # Create Categories
    gen_ai_cat = CompanyCategory.objects.create(name="Generative AI Companies", display_order=1)
    gov_cat = CompanyCategory.objects.create(name="U.S. Government Agencies", display_order=2)
    ent_cat = CompanyCategory.objects.create(name="Enterprises", display_order=3)

    # Logos mapping
    logos_data = [
        # Gen AI
        {'name': 'n8n', 'file': 'n8n-logo.jpg', 'cat': gen_ai_cat, 'order': 1},
        {'name': 'vapi', 'file': 'vapi-logo.svg', 'cat': gen_ai_cat, 'order': 2},
        {'name': 'gpt', 'file': 'gpt-logo.png', 'cat': gen_ai_cat, 'order': 3},
        {'name': '11 labs', 'file': '11-logo.webp', 'cat': gen_ai_cat, 'order': 4},
        {'name': 'gemini', 'file': 'gemini-logo.jpg', 'cat': gen_ai_cat, 'order': 5},
        {'name': 'claude', 'file': 'claude.jpg', 'cat': gen_ai_cat, 'order': 6},
    ]

    for data in logos_data:
        file_path = os.path.join(FRONTEND_LOGOS_DIR, data['file'])
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                logo = CompanyLogo(
                    category=data['cat'],
                    name=data['name'],
                    alt_text=data['name'],
                    display_order=data['order']
                )
                logo.image.save(data['file'], File(f), save=False)
                logo.save()
            print(f"Successfully seeded {data['name']}")
        else:
            print(f"File not found: {file_path}")

if __name__ == '__main__':
    seed_data()
