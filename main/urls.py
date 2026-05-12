from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register(r'cv', api_views.CVViewSet, basename='cv')

urlpatterns = [
    # Legacy Views (Kept for PDF and web interface)
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='cv_dashboard'),
    path('templates/', views.template_selector, name='template_selector'),
    path('api/download-pdf/<int:cv_id>/', views.download_pdf, name='download_pdf'),
    
    # Restore legacy endpoints so current JS doesn't crash
    path('api/create-cv/', views.create_cv, name='create_cv'),
    path('api/get-cv/<int:cv_id>/', views.get_cv, name='get_cv'),
    path('api/delete-cv/<int:cv_id>/', views.delete_cv, name='delete_cv'),

    # Recruiter & Company Endpoints
    path('manage-company/', views.dashboard), # Alias for legacy links
    path('company/manage/', views.manage_company, name='manage_company'),
    path('post-job/', views.post_job, name='post_job'),
    path('delete-job/<int:job_id>/', views.delete_job, name='delete_job'),
    path('manage-trainings/', views.manage_trainings, name='manage_trainings'),
    path('applications/<int:job_id>/', views.view_applications, name='view_applications'),
    path('update-application/<int:app_id>/', views.update_application_status, name='update_application_status'),

    # Student Marketplace & AI Endpoints
    path('browse-jobs/', views.browse_jobs, name='browse_jobs'),
    path('browse-trainings/', views.browse_trainings, name='browse_trainings'),
    path('apply-job/<int:job_id>/', views.apply_to_job, name='apply_to_job'),
    path('ai-dashboard/<int:cv_id>/', views.ai_dashboard, name='ai_dashboard'),
    path('upload-cv-image/<int:cv_id>/', views.upload_cv_image, name='upload_cv_image'),
    path('update-profile/', views.update_profile, name='update_profile'),
    
    # Communication & Badges
    path('send-message/<int:receiver_id>/', views.send_message, name='send_message'),
    path('submit-accomplishment/<int:course_id>/', views.submit_accomplishment, name='submit_accomplishment'),
    path('review-accomplishment/<int:accomplishment_id>/', views.review_accomplishment, name='review_accomplishment'),
    
    # DRF API Endpoints
    path('api/v1/', include(router.urls)),
]