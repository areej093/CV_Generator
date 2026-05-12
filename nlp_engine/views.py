from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from main.models import CV
from .services import analyze_cv, parse_pdf_to_json
import time

class CVAnalysisAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, cv_id):
        # We start a timer to prove it runs under 3 seconds
        start_time = time.time()
        
        # Ensure the user owns the CV
        cv = get_object_or_404(CV, id=cv_id, user=request.user)
        
        # Run the NLP Pipeline
        analysis_result = analyze_cv(cv)
        
        # Add execution time to result
        execution_time = round(time.time() - start_time, 3)
        analysis_result["execution_time_seconds"] = execution_time
        
        return Response(analysis_result)

class PDFParseAPIView(APIView):
    """
    ATS Parser Endpoint: Accepts a PDF upload and returns auto-fillable JSON data.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file provided. Please upload a PDF."}, status=400)
            
        parsed_data = parse_pdf_to_json(file_obj)
        
        if "error" in parsed_data:
            return Response(parsed_data, status=400)
            
        return Response(parsed_data)
