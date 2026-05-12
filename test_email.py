import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cvproject.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

try:
    print(f"Using EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"Using EMAIL_HOST_PASSWORD: {settings.EMAIL_HOST_PASSWORD}")
    
    send_mail(
        'Test Email from CV Generator',
        'This is a test to verify SMTP configuration.',
        settings.DEFAULT_FROM_EMAIL,
        ['careernavigatoria@gmail.com'], # Sending to itself to test
        fail_silently=False,
    )
    print("SUCCESS: Test email sent without exceptions!")
except Exception as e:
    print(f"ERROR: {str(e)}")
