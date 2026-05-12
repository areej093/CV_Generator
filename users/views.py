from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# DRF Imports
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer

# Email Verification Imports
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Send Login Notification Email
            try:
                subject = "New Login Detected - CV Navigator"
                html_message = render_to_string('users/email/login_alert.html', {'username': user.username})
                plain_message = strip_tags(html_message)
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=html_message,
                    fail_silently=True
                )
            except:
                pass
                
            messages.success(request, f'Welcome back, {username}!')
            return redirect('cv_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'users/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            # Generate token and uid
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # Build activation link
            activation_link = request.build_absolute_uri(
                reverse('api_verify_email', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Prepare HTML Message
            html_message = render_to_string('users/email/activation_email.html', {
                'full_name': user.first_name,
                'activation_link': activation_link,
            })
            plain_message = strip_tags(html_message)
            
            # Send Email
            subject = "Activate Your CV Generator Account"
            send_mail(
                subject, 
                plain_message, 
                settings.DEFAULT_FROM_EMAIL, 
                [user.email], 
                html_message=html_message
            )
            
            messages.success(request, 'Registration successful! Please check your email to activate your account.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

class RegisterAPIView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        
        # Generate token and uid
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Build activation link
        activation_link = self.request.build_absolute_uri(
            reverse('api_verify_email', kwargs={'uidb64': uid, 'token': token})
        )
        
        # Prepare HTML Message
        html_message = render_to_string('users/email/activation_email.html', {
            'username': user.username,
            'activation_link': activation_link,
        })
        plain_message = strip_tags(html_message)
        
        # Send Email
        subject = "Activate Your CV Generator Account"
        send_mail(
            subject, 
            plain_message, 
            settings.DEFAULT_FROM_EMAIL, 
            [user.email], 
            html_message=html_message
        )

class VerifyEmailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, "Email successfully verified. You can now login!")
            return redirect('login')
        else:
            messages.error(request, "Activation link is invalid or has expired.")
            return redirect('login')
