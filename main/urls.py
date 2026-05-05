from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='cv_dashboard'),
    path('api/create-cv/', views.create_cv, name='create_cv'),
    path('api/update-cv/<int:cv_id>/', views.update_cv, name='update_cv'),
    path('api/get-cv/<int:cv_id>/', views.get_cv, name='get_cv'),
    path('api/delete-cv/<int:cv_id>/', views.delete_cv, name='delete_cv'),
    path('api/download-pdf/<int:cv_id>/', views.download_pdf, name='download_pdf'),
    path('templates/', views.template_selector, name='template_selector'),
]