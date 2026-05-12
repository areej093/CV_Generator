from django.urls import path
from . import views

urlpatterns = [
    path('cv/<int:cv_id>/analyze/', views.CVAnalysisAPIView.as_view(), name='api_analyze_cv'),
    path('parse-pdf/', views.PDFParseAPIView.as_view(), name='api_parse_pdf'),
]
