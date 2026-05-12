import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cvproject.settings')
django.setup()

from main.models import CV

cv = CV.objects.first()
if cv:
    print(f"First CV ID: {cv.id}, Full Name: {cv.full_name}")
else:
    print("No CVs found in the database.")
