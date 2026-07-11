import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from api.models import ServiceTemplate

TEMPLATES = [
    {
        "name": "Flask Backend Base",
        "template_key": "flask_base",
        "description": "Standard Python Flask blueprint with database integration.",
        "icon": "terminal"
    },
    {
        "name": "React Vite Frontend",
        "template_key": "react_base",
        "description": "Modern React 19 application with Tailwind CSS and Vite.",
        "icon": "atom"
    },
    {
        "name": "Vite Svelte Base",
        "template_key": "vite_base",
        "description": "High-performance Svelte / Vite template for real-time dashboards.",
        "icon": "zap"
    }
]

def seed():
    print("🌱 Seeding Service Templates...")
    for t in TEMPLATES:
        obj, created = ServiceTemplate.objects.get_or_create(
            template_key=t["template_key"],
            defaults={
                "name": t["name"],
                "description": t["description"],
                "icon": t["icon"]
            }
        )
        if created:
            print(f"✅ Created: {t['name']}")
        else:
            print(f"ℹ️ Already exists: {t['name']}")

if __name__ == "__main__":
    seed()
