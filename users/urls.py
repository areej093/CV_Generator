from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Standard Django Views (Will be removed later)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Password Reset (Django Built-in)
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # API Views
    path('api/register/', views.RegisterAPIView.as_view(), name='api_register'),
    path('api/verify-email/<uidb64>/<token>/', views.VerifyEmailAPIView.as_view(), name='api_verify_email'),
]