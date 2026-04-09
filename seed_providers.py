import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rocketops_core.settings')
django.setup()

from api.models import AIProvider

def seed_providers():
    providers = [
        {'name': 'n8n', 'order': 1},
        {'name': 'Gemini', 'order': 2},
        {'name': '11 Labs', 'order': 3},
        {'name': 'ChatGpt', 'order': 4},
    ]

    for data in providers:
        AIProvider.objects.update_or_create(
            name=data['name'],
            defaults={'display_order': data['order']}
        )
        print(f"Seeded AI Provider: {data['name']}")

if __name__ == '__main__':
    seed_providers()
