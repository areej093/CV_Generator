from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from django.contrib import messages
import json
from .models import CV, Experience, Education, Skill
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import io
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import pdfkit
import os
import qrcode
from io import BytesIO
import base64


def home(request):
    template = request.GET.get('template', 'modern')
    return render(request, 'main/home.html', {'selected_template': template})

@login_required
def dashboard(request):
    # Get all CVs for the logged-in user
    user_cvs = CV.objects.filter(user=request.user)
    
    # Convert CVs to JSON
    cvs_data = []
    for cv in user_cvs:
        cvs_data.append({
            'id': cv.id,
            'full_name': cv.full_name,
            'professional_title': cv.professional_title,
            'email': cv.email,
            'created_at': cv.created_at.isoformat() if cv.created_at else None,
            'updated_at': cv.updated_at.isoformat() if cv.updated_at else None,
        })
    
    return render(request, 'main/dashboard.html', {
        'user': request.user,
        'cvs': user_cvs,  # Add this for Django template
        'cvs_json': json.dumps(cvs_data)  # Keep this for JavaScript
    })

@login_required
def create_cv(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from request
            data = json.loads(request.body)
            
            # Create CV
            cv = CV.objects.create(
                user=request.user,
                full_name=data['personalInfo']['name'],
                email=data['personalInfo']['email'],
                phone=data['personalInfo']['phone'],
                address=data['personalInfo']['address'],
                professional_title=data['personalInfo']['title'],
                summary=data['personalInfo']['summary'],
                linkedin_url=data['personalInfo'].get('linkedin', ''),
                template=data.get('template', 'modern')
            )
            
            # Add experiences
            for exp in data['experiences']:
                if exp.get('position') or exp.get('company'):  # Only save if has data
                    Experience.objects.create(
                        cv=cv,
                        position=exp.get('position', ''),
                        company=exp.get('company', ''),
                        duration=exp.get('duration', ''),
                        description=exp.get('description', '')
                    )
            
            # Add education
            for edu in data['education']:
                if edu.get('degree') or edu.get('institution'):  # Only save if has data
                    Education.objects.create(
                        cv=cv,
                        degree=edu.get('degree', ''),
                        institution=edu.get('institution', ''),
                        year=edu.get('year', '')
                    )
            
            # Add skills
            for skill in data['skills']:
                if skill.get('name'):  # Only save if has name
                    Skill.objects.create(
                        cv=cv,
                        name=skill['name'],
                        level=skill.get('level', 'Intermediate')
                    )
            
            return JsonResponse({
                'success': True,
                'message': 'CV saved successfully!',
                'cv_id': cv.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def get_cv(request, cv_id):
    """Get a specific CV for editing"""
    try:
        cv = get_object_or_404(CV, id=cv_id, user=request.user)
        
        # Format data for frontend
        data = {
            'personalInfo': {
                'name': cv.full_name,
                'email': cv.email,
                'phone': cv.phone,
                'address': cv.address,
                'title': cv.professional_title,
                'summary': cv.summary,
                'linkedin': cv.linkedin_url,
            },
            'template': cv.template,
            'experiences': [
                {
                    'position': exp.position,
                    'company': exp.company,
                    'duration': exp.duration,
                    'description': exp.description
                } for exp in cv.experiences.all()
            ],
            'education': [
                {
                    'degree': edu.degree,
                    'institution': edu.institution,
                    'year': edu.year
                } for edu in cv.education.all()
            ],
            'skills': [
                {
                    'name': skill.name,
                    'level': skill.level
                } for skill in cv.skills.all()
            ]
        }
        
        return JsonResponse(data)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

def generate_qr_code(data):
    """Generate QR code image and return as base64 string"""
    try:
        if not data:
            return ""
            
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str
    except Exception as e:
        print(f"QR generation error: {e}")
        return ""
@login_required
def delete_cv(request, cv_id):
    """Delete a CV"""
    if request.method == 'DELETE':
        try:
            cv = get_object_or_404(CV, id=cv_id, user=request.user)
            cv.delete()
            return JsonResponse({
                'success': True,
                'message': 'CV deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
@login_required
def download_pdf(request, cv_id):
    """Generate and download PDF for a CV"""
    try:
        # Get the CV
        cv = get_object_or_404(CV, id=cv_id, user=request.user)
        
        # Get all related data
        experiences = cv.experiences.all()
        education = cv.education.all()
        skills = cv.skills.all()
         # NEW: Generate QR code from LinkedIn URL
        qr_code_base64 = ""
        qr_section = ""
        
        if cv.linkedin_url and cv.linkedin_url.strip():
            qr_code_base64 = generate_qr_code(cv.linkedin_url)
            qr_section = f'''
            <!-- QR Code Section -->
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ccc;">
                <h4 style="margin-bottom: 10px; color: #333;">📱 Connect on LinkedIn</h4>
                <img src="data:image/png;base64,{qr_code_base64}" alt="LinkedIn QR Code" style="width: 120px; height: 120px;">
                <p style="font-size: 10px; color: #666; margin-top: 5px;">
                    Scan with your phone camera to view LinkedIn profile
                </p>
            </div>
            '''
        # Template names for display
        template_names = {
            'modern': 'Modern Professional',
            'classic': 'Classic Elegant',
            'creative': 'Creative Design',
            'minimal': 'Minimal Clean'
        }
        
        # Initialize html_string
        html_string = ""
        
        # MODERN TEMPLATE
        if cv.template == 'modern':
            html_string = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{cv.full_name} - CV</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        margin: 0;
                        padding: 30px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }}
                    .cv-container {{
                        background: white;
                        border-radius: 20px;
                        padding: 40px;
                        box-shadow: 0 20px 40px rgba(0,0,0,0.2);
                        max-width: 1000px;
                        margin: 0 auto;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                        border-bottom: 3px solid #667eea;
                        padding-bottom: 20px;
                    }}
                    .name {{
                        color: #667eea;
                        font-size: 36px;
                        margin: 0;
                    }}
                    .title {{
                        color: #764ba2;
                        font-size: 20px;
                        margin: 5px 0 0 0;
                    }}
                    .grid-2 {{
                        display: grid;
                        grid-template-columns: 1fr 2fr;
                        gap: 30px;
                    }}
                    .sidebar {{
                        background: #f8f9fa;
                        padding: 20px;
                        border-radius: 15px;
                    }}
                    .section-title {{
                        color: #667eea;
                        font-size: 18px;
                        margin: 0 0 15px 0;
                        border-bottom: 2px solid #667eea;
                        padding-bottom: 5px;
                    }}
                    .contact-info p {{
                        margin: 10px 0;
                    }}
                    .skill-item {{
                        margin-bottom: 10px;
                    }}
                    .skill-name {{
                        font-weight: bold;
                        color: #333;
                    }}
                    .skill-level {{
                        color: #667eea;
                    }}
                    .experience-item, .education-item {{
                        margin-bottom: 20px;
                    }}
                    .experience-item h4, .education-item h4 {{
                        color: #333;
                        margin: 0 0 5px 0;
                    }}
                    .company, .institution {{
                        color: #667eea;
                        font-weight: bold;
                        margin: 0 0 5px 0;
                    }}
                    .date {{
                        color: #666;
                        font-size: 14px;
                        margin: 0 0 5px 0;
                    }}
                    .footer {{
                        text-align: center;
                        color: #999;
                        font-size: 10px;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #eee;
                    }}
                </style>
            </head>
            <body>
                <div class="cv-container">
                    <div class="header">
                        <h1 class="name">{cv.full_name}</h1>
                        <h2 class="title">{cv.professional_title}</h2>
                    </div>
                    
                    <div class="grid-2">
                        <div class="sidebar">
                            <h3 class="section-title">📞 Contact</h3>
                            <div class="contact-info">
                                <p>✉ {cv.email}</p>
                                <p>📱 {cv.phone}</p>
                                <p>📍 {cv.address}</p>
                            </div>
                            
                            <h3 class="section-title" style="margin-top: 30px;">⚙️ Skills</h3>
                            {''.join([f'''
                            <div class="skill-item">
                                <span class="skill-name">{skill.name}:</span>
                                <span class="skill-level">{skill.level}</span>
                            </div>
                            ''' for skill in skills])}
                        </div>
                        
                        <div class="main-content">
                            <h3 class="section-title">📄 Summary</h3>
                            <p>{cv.summary}</p>
                            
                            <h3 class="section-title" style="margin-top: 30px;"> 💼 Experience</h3>
                            {''.join([f'''
                            <div class="experience-item">
                                <h4>{exp.position}</h4>
                                <div class="company">{exp.company}</div>
                                <div class="date">{exp.duration}</div>
                                <p>{exp.description}</p>
                            </div>
                            ''' for exp in experiences])}
                            
                            <h3 class="section-title" style="margin-top: 30px;">🎓 Education</h3>
                            {''.join([f'''
                            <div class="education-item">
                                <h4>{edu.degree}</h4>
                                <div class="institution">{edu.institution}</div>
                                <div class="date">{edu.year}</div>
                            </div>
                            ''' for edu in education])}
                        </div>
                    </div>
                    <div class="footer">Generated by CV Generator • {template_names[cv.template]} Template</div>
                </div>
             {qr_section}   
            </body>
            </html>
            '''
        
        # CLASSIC TEMPLATE
        elif cv.template == 'classic':
            html_string = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{cv.full_name} - CV</title>
                <style>
                    body {{
                        font-family: 'Times New Roman', Times, serif;
                        background: #f4e9d8;
                        padding: 40px;
                        margin: 0;
                    }}
                    .cv-container {{
                        background: white;
                        border: 2px solid #8b7355;
                        padding: 40px;
                        max-width: 1000px;
                        margin: 0 auto;
                    }}
                    .header {{
                        text-align: center;
                        border-bottom: 2px solid #8b7355;
                        padding-bottom: 20px;
                        margin-bottom: 30px;
                    }}
                    .name {{
                        color: #2c1810;
                        font-size: 42px;
                        margin: 0;
                    }}
                    .title {{
                        color: #8b7355;
                        font-style: italic;
                        margin: 5px 0 0 0;
                    }}
                    .grid-2 {{
                        display: grid;
                        grid-template-columns: 1fr 2fr;
                        gap: 40px;
                    }}
                    .section-title {{
                        color: #2c1810;
                        border-bottom: 1px solid #8b7355;
                        padding-bottom: 5px;
                        font-size: 20px;
                    }}
                    .contact-info p {{
                        margin: 10px 0;
                        color: #2c1810;
                    }}
                    .skill-item {{
                        margin: 8px 0;
                    }}
                    .experience-item, .education-item {{
                        margin-bottom: 25px;
                    }}
                    .experience-item h4, .education-item h4 {{
                        margin: 0;
                        color: #2c1810;
                    }}
                    .company, .institution {{
                        color: #8b7355;
                        margin: 5px 0;
                        font-style: italic;
                    }}
                    .footer {{
                        text-align: center;
                        color: #8b7355;
                        font-size: 11px;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px dashed #8b7355;
                    }}
                </style>
            </head>
            <body>
                <div class="cv-container">
                    <div class="header">
                        <h1 class="name">{cv.full_name}</h1>
                        <h2 class="title">{cv.professional_title}</h2>
                    </div>
                    
                    <div class="grid-2">
                        <div>
                            <h3 class="section-title">Contact</h3>
                            <div class="contact-info">
                                <p>✉ {cv.email}</p>
                                <p>📞 {cv.phone}</p>
                                <p>🏠 {cv.address}</p>
                            </div>
                            
                            <h3 class="section-title" style="margin-top: 30px;">Skills</h3>
                            {''.join([f'<p class="skill-item">• {skill.name} - {skill.level}</p>' for skill in skills])}
                        </div>
                        
                        <div>
                            <h3 class="section-title">Professional Summary</h3>
                            <p>{cv.summary}</p>
                            
                            <h3 class="section-title" style="margin-top: 30px;">Experience</h3>
                            {''.join([f'''
                            <div class="experience-item">
                                <h4>{exp.position}</h4>
                                <div class="company">{exp.company}</div>
                                <div class="date">{exp.duration}</div>
                                <p>{exp.description}</p>
                            </div>
                            ''' for exp in experiences])}
                            
                            <h3 class="section-title" style="margin-top: 30px;">Education</h3>
                            {''.join([f'''
                            <div class="education-item">
                                <h4>{edu.degree}</h4>
                                <div class="institution">{edu.institution}</div>
                                <div class="date">{edu.year}</div>
                            </div>
                            ''' for edu in education])}
                        </div>
                    </div>
                    <div class="footer">Generated by CV Generator • {template_names[cv.template]} Template</div>
                </div>
                {qr_section}
            </body>
            </html>
            '''
        
        # CREATIVE TEMPLATE
        elif cv.template == 'creative':
            html_string = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{cv.full_name} - CV</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                        font-family: 'Poppins', 'Helvetica', sans-serif;
                    }}
                    .grid-2 {{
                        display: grid;
                        grid-template-columns: 280px 1fr;
                        min-height: 100vh;
                    }}
                    .sidebar {{
                        background: #e74c3c;
                        padding: 40px 20px;
                        color: white;
                    }}
                    .main {{
                        background: white;
                        padding: 40px;
                    }}
                    .name {{
                        font-size: 28px;
                        margin: 0 0 5px 0;
                        color: white;
                    }}
                    .title {{
                        font-size: 16px;
                        opacity: 0.9;
                        margin: 0 0 30px 0;
                        color: white;
                    }}
                    .section-title {{
                        border-bottom: 2px solid white;
                        padding-bottom: 5px;
                        margin: 30px 0 15px 0;
                        color: white;
                        font-size: 18px;
                    }}
                    .main .section-title {{
                        color: #e74c3c;
                        border-bottom: 2px solid #e74c3c;
                    }}
                    .contact-info p {{
                        margin: 10px 0;
                        font-size: 14px;
                    }}
                    .skill-item {{
                        margin-bottom: 10px;
                    }}
                    .experience-item, .education-item {{
                        margin-bottom: 25px;
                    }}
                    .experience-item h4, .education-item h4 {{
                        color: #e74c3c;
                        margin: 0;
                    }}
                    .company, .institution {{
                        color: #e74c3c;
                        font-weight: bold;
                        margin: 5px 0;
                    }}
                    .footer {{
                        text-align: center;
                        color: #999;
                        font-size: 10px;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #eee;
                    }}
                </style>
            </head>
            <body>
                <div class="grid-2">
                    <div class="sidebar">
                        <h1 class="name">{cv.full_name}</h1>
                        <h2 class="title">{cv.professional_title}</h2>
                        
                        <h3 class="section-title">Contact</h3>
                        <div class="contact-info">
                            <p>📧 {cv.email}</p>
                            <p>📱 {cv.phone}</p>
                            <p>📍 {cv.address}</p>
                        </div>
                        
                        <h3 class="section-title">Skills</h3>
                        {''.join([f'<div class="skill-item"><b>{skill.name}:</b> {skill.level}</div>' for skill in skills])}
                    </div>
                    
                    <div class="main">
                        <h3 class="section-title">Summary</h3>
                        <p>{cv.summary}</p>
                        
                        <h3 class="section-title" style="margin-top: 30px;">Experience</h3>
                        {''.join([f'''
                        <div class="experience-item">
                            <h4>{exp.position}</h4>
                            <div class="company">{exp.company}</div>
                            <div class="date">{exp.duration}</div>
                            <p>{exp.description}</p>
                        </div>
                        ''' for exp in experiences])}
                        
                        <h3 class="section-title" style="margin-top: 30px;">Education</h3>
                        {''.join([f'''
                        <div class="education-item">
                            <h4>{edu.degree}</h4>
                            <div class="institution">{edu.institution}</div>
                            <div class="date">{edu.year}</div>
                        </div>
                        ''' for edu in education])}
                        
                        <div class="footer">Generated by CV Generator • {template_names[cv.template]} Template</div>
                    </div>
                </div>
                {qr_section}
            </body>
            </html>
            '''
        
        # MINIMAL TEMPLATE
        elif cv.template == 'minimal':
            html_string = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{cv.full_name} - CV</title>
                <style>
                    body {{
                        font-family: 'Helvetica', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 40px;
                    }}
                    .name {{
                        font-size: 48px;
                        font-weight: 300;
                        color: #333;
                        letter-spacing: 2px;
                        margin: 0;
                    }}
                    .title {{
                        font-size: 20px;
                        font-weight: 300;
                        color: #666;
                        margin: 5px 0 20px 0;
                    }}
                    .line {{
                        width: 50px;
                        height: 2px;
                        background: #007bff;
                        margin: 20px 0;
                    }}
                    .grid-2 {{
                        display: grid;
                        grid-template-columns: 1fr 2fr;
                        gap: 40px;
                        margin-top: 30px;
                    }}
                    .contact-info p {{
                        color: #666;
                        margin: 10px 0;
                    }}
                    .section-title {{
                        font-weight: 400;
                        color: #333;
                        margin: 20px 0 15px 0;
                    }}
                    .skill-item {{
                        color: #666;
                        margin: 5px 0;
                    }}
                    .experience-item, .education-item {{
                        margin-bottom: 25px;
                    }}
                    .experience-item h4, .education-item h4 {{
                        font-weight: 500;
                        margin: 0 0 5px 0;
                    }}
                    .company, .institution {{
                        color: #666;
                        margin: 0 0 5px 0;
                    }}
                    .date {{
                        color: #999;
                        font-size: 14px;
                        margin: 0 0 5px 0;
                    }}
                    .footer {{
                        text-align: center;
                        color: #999;
                        font-size: 10px;
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 1px solid #eee;
                    }}
                </style>
            </head>
            <body>
                <h1 class="name">{cv.full_name}</h1>
                <h2 class="title">{cv.professional_title}</h2>
                <div class="line"></div>
                
                <div class="grid-2">
                    <div>
                        <div class="contact-info">
                            <p>📧 {cv.email}</p>
                            <p>📱 {cv.phone}</p>
                            <p>📍 {cv.address}</p>
                        </div>
                        
                        <h3 class="section-title">Skills</h3>
                        {''.join([f'<p class="skill-item">• {skill.name} - {skill.level}</p>' for skill in skills])}
                    </div>
                    
                    <div>
                        <h3 class="section-title">Summary</h3>
                        <p>{cv.summary}</p>
                        
                        <h3 class="section-title">Experience</h3>
                        {''.join([f'''
                        <div class="experience-item">
                            <h4>{exp.position}</h4>
                            <div class="company">{exp.company}</div>
                            <div class="date">{exp.duration}</div>
                            <p>{exp.description}</p>
                        </div>
                        ''' for exp in experiences])}
                        
                        <h3 class="section-title">Education</h3>
                        {''.join([f'''
                        <div class="education-item">
                            <h4>{edu.degree}</h4>
                            <div class="institution">{edu.institution}</div>
                            <div class="date">{edu.year}</div>
                        </div>
                        ''' for edu in education])}
                    </div>
                </div>
                <div class="footer">Generated by CV Generator • {template_names[cv.template]} Template</div>
                {qr_section}
            </body>
            </html>
            '''
        
        # DEFAULT CASE - if template not recognized, use modern
        else:
            # Use modern template as default
            cv.template = 'modern'
            html_string = "Error: Template not found"  # This shouldn't happen
        
        # Configure pdfkit
        options = {
            'page-size': 'A4',
            'margin-top': '20mm',
            'margin-right': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None
        }
        
        # Path to wkhtmltopdf (default installation path)
        wkhtmltopdf_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        
        # Check if file exists, if not try alternative path
        if not os.path.exists(wkhtmltopdf_path):
            wkhtmltopdf_path = r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe'
        
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        
        # Generate PDF
        pdf = pdfkit.from_string(html_string, False, options=options, configuration=config)
        
        # Create response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{cv.full_name}_{cv.template}_CV.pdf"'
        response.write(pdf)
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
@login_required
def update_cv(request, cv_id):
    """Update an existing CV"""
    if request.method == 'PUT':
        try:
            # Get the existing CV
            cv = get_object_or_404(CV, id=cv_id, user=request.user)
            
            # Parse JSON data from request
            data = json.loads(request.body)
            
            # Update CV fields
            cv.full_name = data['personalInfo']['name']
            cv.email = data['personalInfo']['email']
            cv.phone = data['personalInfo']['phone']
            cv.address = data['personalInfo']['address']
            cv.professional_title = data['personalInfo']['title']
            cv.summary = data['personalInfo']['summary']
            cv.linkedin_url = data['personalInfo'].get('linkedin', '')
            cv.template = data.get('template', cv.template)
            cv.save()
            
            # Delete existing experiences, education, skills
            cv.experiences.all().delete()
            cv.education.all().delete()
            cv.skills.all().delete()
            
            # Add new experiences
            for exp in data['experiences']:
                if exp.get('position') or exp.get('company'):
                    Experience.objects.create(
                        cv=cv,
                        position=exp.get('position', ''),
                        company=exp.get('company', ''),
                        duration=exp.get('duration', ''),
                        description=exp.get('description', '')
                    )
            
            # Add new education
            for edu in data['education']:
                if edu.get('degree') or edu.get('institution'):
                    Education.objects.create(
                        cv=cv,
                        degree=edu.get('degree', ''),
                        institution=edu.get('institution', ''),
                        year=edu.get('year', '')
                    )
            
            # Add new skills
            for skill in data['skills']:
                if skill.get('name'):
                    Skill.objects.create(
                        cv=cv,
                        name=skill['name'],
                        level=skill.get('level', 'Intermediate')
                    )
            
            return JsonResponse({
                'success': True,
                'message': 'CV updated successfully!',
                'cv_id': cv.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
def template_selector(request):
    """Template selection page"""
    return render(request, 'main/templates.html')
def generate_qr_code(data):
    """Generate QR code image and return as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str
def render_cv_html(cv):
    """Render CV as HTML based on template"""
    
    # Get all related data
    experiences = cv.experiences.all()
    education = cv.education.all()
    skills = cv.skills.all()
    
    # Modern Template
    if cv.template == 'modern':
        html = f'''
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 0 auto; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 20px;">
            <div style="background: white; border-radius: 15px; padding: 30px; box-shadow: 0 20px 40px rgba(0,0,0,0.2);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #667eea; font-size: 36px; margin-bottom: 5px;">{cv.full_name}</h1>
                    <h2 style="color: #764ba2; font-size: 20px; font-weight: normal;">{cv.professional_title}</h2>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 30px;">
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
                        <h3 style="color: #667eea; margin-bottom: 15px;">📞 Contact</h3>
                        <p style="margin-bottom: 10px;">📧 {cv.email}</p>
                        <p style="margin-bottom: 10px;">📱 {cv.phone}</p>
                        <p style="margin-bottom: 10px;">📍 {cv.address}</p>
                        
                        <h3 style="color: #667eea; margin: 20px 0 15px;">🔧 Skills</h3>
                        {''.join([f'<div style="margin-bottom: 10px;"><span style="font-weight: bold;">{skill.name}:</span> {skill.level}</div>' for skill in skills])}
                    </div>
                    
                    <div>
                        <h3 style="color: #667eea; margin-bottom: 15px;">📝 Summary</h3>
                        <p style="margin-bottom: 20px;">{cv.summary}</p>
                        
                        <h3 style="color: #667eea; margin-bottom: 15px;">💼 Experience</h3>
                        {''.join([f'''
                        <div style="margin-bottom: 20px;">
                            <h4 style="color: #333; font-weight: bold;">{exp.position}</h4>
                            <p style="color: #667eea; margin-bottom: 5px;">{exp.company} | {exp.duration}</p>
                            <p>{exp.description}</p>
                        </div>
                        ''' for exp in experiences])}
                        
                        <h3 style="color: #667eea; margin-bottom: 15px;">🎓 Education</h3>
                        {''.join([f'''
                        <div style="margin-bottom: 15px;">
                            <h4 style="color: #333; font-weight: bold;">{edu.degree}</h4>
                            <p style="color: #667eea;">{edu.institution} | {edu.year}</p>
                        </div>
                        ''' for edu in education])}
                    </div>
                </div>
            </div>
        </div>
        '''
    
    # Classic Template
    elif cv.template == 'classic':
        html = f'''
        <div style="font-family: 'Times New Roman', serif; max-width: 800px; margin: 0 auto; background: #f4e9d8; padding: 40px; border: 2px solid #8b7355;">
            <div style="text-align: center; border-bottom: 2px solid #8b7355; padding-bottom: 20px; margin-bottom: 30px;">
                <h1 style="color: #2c1810; font-size: 42px; margin-bottom: 5px;">{cv.full_name}</h1>
                <h2 style="color: #8b7355; font-style: italic;">{cv.professional_title}</h2>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 40px;">
                <div>
                    <h3 style="color: #2c1810; border-bottom: 1px solid #8b7355; padding-bottom: 5px; margin-bottom: 15px;">Contact</h3>
                    <p style="margin-bottom: 10px;">✉️ {cv.email}</p>
                    <p style="margin-bottom: 10px;">📞 {cv.phone}</p>
                    <p style="margin-bottom: 10px;">🏠 {cv.address}</p>
                    
                    <h3 style="color: #2c1810; border-bottom: 1px solid #8b7355; padding-bottom: 5px; margin: 20px 0 15px;">Skills</h3>
                    {''.join([f'<p style="margin-bottom: 5px;">• {skill.name} - {skill.level}</p>' for skill in skills])}
                </div>
                
                <div>
                    <h3 style="color: #2c1810; border-bottom: 1px solid #8b7355; padding-bottom: 5px; margin-bottom: 15px;">Professional Summary</h3>
                    <p style="margin-bottom: 25px;">{cv.summary}</p>
                    
                    <h3 style="color: #2c1810; border-bottom: 1px solid #8b7355; padding-bottom: 5px; margin-bottom: 15px;">Experience</h3>
                    {''.join([f'''
                    <div style="margin-bottom: 20px;">
                        <h4 style="font-weight: bold;">{exp.position}</h4>
                        <p style="color: #8b7355; margin-bottom: 5px;">{exp.company} — {exp.duration}</p>
                        <p>{exp.description}</p>
                    </div>
                    ''' for exp in experiences])}
                    
                    <h3 style="color: #2c1810; border-bottom: 1px solid #8b7355; padding-bottom: 5px; margin-bottom: 15px;">Education</h3>
                    {''.join([f'''
                    <div style="margin-bottom: 15px;">
                        <h4 style="font-weight: bold;">{edu.degree}</h4>
                        <p style="color: #8b7355;">{edu.institution}, {edu.year}</p>
                    </div>
                    ''' for edu in education])}
                </div>
            </div>
        </div>
        '''
    
    # Creative Template
    elif cv.template == 'creative':
        html = f'''
        <div style="font-family: 'Poppins', sans-serif; max-width: 800px; margin: 0 auto; display: grid; grid-template-columns: 280px 1fr; background: #2c3e50;">
            <div style="background: #e74c3c; padding: 30px 20px; color: white;">
                <h1 style="font-size: 28px; margin-bottom: 5px;">{cv.full_name}</h1>
                <h2 style="font-size: 16px; font-weight: normal; opacity: 0.9; margin-bottom: 30px;">{cv.professional_title}</h2>
                
                <div style="margin-bottom: 30px;">
                    <h3 style="border-bottom: 2px solid white; padding-bottom: 5px; margin-bottom: 15px;">Contact</h3>
                    <p style="margin-bottom: 10px; font-size: 14px;">📧 {cv.email}</p>
                    <p style="margin-bottom: 10px; font-size: 14px;">📱 {cv.phone}</p>
                    <p style="margin-bottom: 10px; font-size: 14px;">📍 {cv.address}</p>
                </div>
                
                <div>
                    <h3 style="border-bottom: 2px solid white; padding-bottom: 5px; margin-bottom: 15px;">Skills</h3>
                    {''.join([f'<div style="margin-bottom: 10px;"><span style="font-weight: bold;">{skill.name}:</span> {skill.level}</div>' for skill in skills])}
                </div>
            </div>
            
            <div style="background: white; padding: 30px;">
                <div style="margin-bottom: 30px;">
                    <h3 style="color: #e74c3c; border-bottom: 2px solid #e74c3c; padding-bottom: 5px; margin-bottom: 15px;">Summary</h3>
                    <p>{cv.summary}</p>
                </div>
                
                <div style="margin-bottom: 30px;">
                    <h3 style="color: #e74c3c; border-bottom: 2px solid #e74c3c; padding-bottom: 5px; margin-bottom: 15px;">Experience</h3>
                    {''.join([f'''
                    <div style="margin-bottom: 20px;">
                        <h4 style="font-weight: bold;">{exp.position}</h4>
                        <p style="color: #e74c3c; margin-bottom: 5px;">{exp.company} | {exp.duration}</p>
                        <p>{exp.description}</p>
                    </div>
                    ''' for exp in experiences])}
                </div>
                
                <div>
                    <h3 style="color: #e74c3c; border-bottom: 2px solid #e74c3c; padding-bottom: 5px; margin-bottom: 15px;">Education</h3>
                    {''.join([f'''
                    <div style="margin-bottom: 15px;">
                        <h4 style="font-weight: bold;">{edu.degree}</h4>
                        <p style="color: #e74c3c;">{edu.institution}, {edu.year}</p>
                    </div>
                    ''' for edu in education])}
                </div>
            </div>
        </div>
        '''
    
    # Minimal Template
    else:  # minimal
        html = f'''
        <div style="font-family: 'Helvetica', Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 40px;">
            <h1 style="font-size: 48px; font-weight: 300; color: #333; letter-spacing: 2px; margin-bottom: 5px;">{cv.full_name}</h1>
            <h2 style="font-size: 20px; font-weight: 300; color: #666; margin-bottom: 20px;">{cv.professional_title}</h2>
            
            <div style="width: 50px; height: 2px; background: #007bff; margin: 20px 0;"></div>
            
            <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 40px;">
                <div>
                    <p style="margin-bottom: 10px; color: #666;">📧 {cv.email}</p>
                    <p style="margin-bottom: 10px; color: #666;">📱 {cv.phone}</p>
                    <p style="margin-bottom: 20px; color: #666;">📍 {cv.address}</p>
                    
                    <h3 style="font-weight: 400; color: #333; margin-bottom: 15px;">Skills</h3>
                    {''.join([f'<p style="margin-bottom: 5px; color: #666;">• {skill.name} - {skill.level}</p>' for skill in skills])}
                </div>
                
                <div>
                    <h3 style="font-weight: 400; color: #333; margin-bottom: 15px;">Summary</h3>
                    <p style="color: #666; margin-bottom: 25px;">{cv.summary}</p>
                    
                    <h3 style="font-weight: 400; color: #333; margin-bottom: 15px;">Experience</h3>
                    {''.join([f'''
                    <div style="margin-bottom: 20px;">
                        <h4 style="font-weight: 500;">{exp.position}</h4>
                        <p style="color: #666; margin-bottom: 5px;">{exp.company} | {exp.duration}</p>
                        <p style="color: #777;">{exp.description}</p>
                    </div>
                    ''' for exp in experiences])}
                    
                    <h3 style="font-weight: 400; color: #333; margin-bottom: 15px;">Education</h3>
                    {''.join([f'''
                    <div style="margin-bottom: 15px;">
                        <h4 style="font-weight: 500;">{edu.degree}</h4>
                        <p style="color: #666;">{edu.institution}, {edu.year}</p>
                    </div>
                    ''' for edu in education])}
                </div>
            </div>
        </div>
        '''
    
    return html