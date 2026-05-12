import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cvproject.settings')
django.setup()

from django.contrib.auth.models import User

for u in User.objects.all():
    print(f"User: {u.username}, Email: {u.email}, Active: {u.is_active}, Has usable password: {u.has_usable_password()}")
