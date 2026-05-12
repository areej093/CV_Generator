from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from django.contrib import messages
import json
from django.contrib.auth.models import User
from .models import CV, Experience, Education, Skill, JobOffer, Application, Company, TrainingCourse, Notification, CourseAccomplishment, Badge, Message
from nlp_engine.services import match_cv_to_job, analyze_cv
from django.core.mail import send_mail
from django.urls import reverse
from django.template.loader import render_to_string
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

def template_selector(request):
    return render(request, 'main/templates.html')

@login_required
def dashboard(request):
    # If recruiter, go to company_dashboard
    if hasattr(request.user, 'profile') and request.user.profile.user_type == 'recruiter':
        company, _ = Company.objects.get_or_create(user=request.user, defaults={'name': f"{request.user.username}'s Company"})
        jobs = JobOffer.objects.filter(company=company)
        verification_requests = CourseAccomplishment.objects.filter(course__company=company, status='pending')
        return render(request, 'main/company_dashboard.html', {
            'company': company,
            'jobs': jobs,
            'verification_requests': verification_requests
        })

    # Get all CVs for the logged-in user
    user_cvs = CV.objects.filter(user=request.user)
    
    # Get notifications
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get job applications
    applications = Application.objects.filter(cv__user=request.user).order_by('-applied_at')
    
    # Convert CVs to JSON
    cvs_data = []
    for cv in user_cvs:
        cvs_data.append({
            'id': cv.id,
            'full_name': cv.full_name,
            'professional_title': cv.professional_title,
            'email': cv.email,
            'profile_image': cv.profile_image.url if cv.profile_image else None,
            'created_at': cv.created_at.isoformat() if cv.created_at else None,
            'updated_at': cv.updated_at.isoformat() if cv.updated_at else None,
        })
    
    # Get AI Recommended Training Courses
    recommended_trainings = []
    if user_cvs.exists():
        primary_cv = user_cvs.first()
        try:
            # Simple keyword matching for demo, or real NLP if available
            all_trainings = TrainingCourse.objects.all()
            for course in all_trainings:
                # Check if course title or description matches CV title or summary
                cv_text = f"{primary_cv.professional_title} {primary_cv.summary}".lower()
                if course.title.lower() in cv_text or any(word in cv_text for word in course.title.lower().split()):
                    recommended_trainings.append(course)
            
            recommended_trainings = recommended_trainings[:3] # Limit to 3
        except:
            pass

    return render(request, 'main/dashboard.html', {
        'cvs': user_cvs,
        'cvs_json': json.dumps(cvs_data),
        'notifications': notifications,
        'applications': applications,
        'recommended_trainings': recommended_trainings
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
                full_name=data.get('personalInfo', {}).get('name', 'My Name'),
                email=data.get('personalInfo', {}).get('email', ''),
                phone=data.get('personalInfo', {}).get('phone', ''),
                address=data.get('personalInfo', {}).get('address', ''),
                professional_title=data.get('personalInfo', {}).get('title', ''),
                summary=data.get('personalInfo', {}).get('summary', ''),
                linkedin_url=data.get('personalInfo', {}).get('linkedin', ''),
                template=data.get('template', 'modern')
            )
            
            # AUTO-SYNC: If user has a profile picture and no image was uploaded for this CV, copy it
            if not cv.profile_image and hasattr(request.user, 'profile') and request.user.profile.profile_picture:
                cv.profile_image = request.user.profile.profile_picture
                cv.save()
            
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
        # Get the CV - Allow owner OR recruiter who received application
        if hasattr(request.user, 'profile') and request.user.profile.user_type == 'recruiter':
            cv = get_object_or_404(CV, id=cv_id)
            # Check if this recruiter has an application from this CV
            if not Application.objects.filter(cv=cv, job_offer__company__user=request.user).exists():
                return JsonResponse({'success': False, 'error': 'You do not have permission to view this CV.'}, status=403)
        else:
            cv = get_object_or_404(CV, id=cv_id, user=request.user)
        
        # Get all related data
        experiences = cv.experiences.all()
        education = cv.education.all()
        skills = cv.skills.all()
        
        # Template names for display
        template_names = {
            'modern': 'Modern Professional',
            'classic': 'Classic Elegant',
            'creative': 'Creative Design',
            'minimal': 'Minimal Clean'
        }
        
        # Generate QR Code - use LinkedIn URL if provided, else fallback to CV link
        qr_data = cv.linkedin_url if cv.linkedin_url else request.build_absolute_uri(reverse('get_cv', args=[cv.id]))
        qr_base64 = generate_qr_code(qr_data)
        
        # Get Profile Image Base64
        profile_base64 = ""
        if cv.profile_image:
            try:
                with open(cv.profile_image.path, "rb") as img_file:
                    profile_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            except Exception as e:
                print(f"Profile image encoding error: {e}")
        
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
                    .profile-img {{
                        width: 100px;
                        height: 100px;
                        border-radius: 50%;
                        border: 3px solid #667eea;
                        object-fit: cover;
                    }}
                    .grid-2 {{
                        display: grid;
                        grid-template-columns: 1fr 2fr;
                        gap: 30px;
                    }}
                    .sidebar {{
                        background: #f8fafc;
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
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="text-align: left;">
                                <h1 class="name">{cv.full_name}</h1>
                                <h2 class="title">{cv.professional_title}</h2>
                            </div>
                            {f'<img src="data:image/png;base64,{profile_base64}" class="profile-img">' if profile_base64 else ''}
                        </div>
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
                    <div class="footer">
                        <div style="border-top: 1px solid #eee; margin-top: 20px; padding-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                            <div style="color: #999; font-size: 10px;">Generated by CV Navigator • Digital Verification Enabled</div>
                            <div style="text-align: right;">
                                <img src="data:image/png;base64,{qr_base64}" style="width: 50px; height: 50px; opacity: 0.8;">
                                <div style="font-size: 7px; color: #999;">SCAN TO VERIFY</div>
                            </div>
                        </div>
                    </div>
                </div>
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
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 40px;">
                            <div style="text-align: center; flex: 1;">
                                <h1 class="name">{cv.full_name}</h1>
                                <h2 class="title">{cv.professional_title}</h2>
                            </div>
                            {f'<img src="data:image/png;base64,{profile_base64}" style="width: 100px; height: 100px; border-radius: 8px; border: 2px solid #8b7355; object-fit: cover;">' if profile_base64 else ''}
                        </div>
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
                    <div class="footer">
                        <div style="border-top: 1px solid #8b7355; margin-top: 20px; padding-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                            <div style="color: #8b7355; font-size: 10px;">Generated by CV Navigator • Digital Verification Enabled</div>
                            <div style="text-align: right;">
                                <img src="data:image/png;base64,{qr_base64}" style="width: 50px; height: 50px; opacity: 0.8; border: 1px solid #8b7355;">
                                <div style="font-size: 7px; color: #8b7355;">SCAN TO VERIFY</div>
                            </div>
                        </div>
                    </div>
                </div>
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
                        {f'<div style="margin-bottom: 20px; text-align: center;"><img src="data:image/png;base64,{profile_base64}" style="width: 120px; height: 120px; border-radius: 50%; border: 4px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.2); object-fit: cover;"></div>' if profile_base64 else ''}
                        
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
                        
                        <div class="footer">
                            <div style="border-top: 1px solid #eee; margin-top: 20px; padding-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                                <div style="color: #999; font-size: 10px;">Generated by CV Navigator • Digital Verification Enabled</div>
                                <div style="text-align: right;">
                                    <img src="data:image/png;base64,{qr_base64}" style="width: 50px; height: 50px; opacity: 0.8;">
                                    <div style="font-size: 7px; color: #999;">SCAN TO VERIFY</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
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
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h1 class="name">{cv.full_name}</h1>
                        <h2 class="title">{cv.professional_title}</h2>
                    </div>
                    <img src="data:image/png;base64,{qr_base64}" style="width: 70px; height: 70px;">
                </div>
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
                <div class="footer">
                    <div style="border-top: 1px solid #eee; margin-top: 20px; padding-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="color: #999; font-size: 10px;">Generated by CV Navigator • Digital Verification Enabled</div>
                        <div style="text-align: right;">
                            <img src="data:image/png;base64,{qr_base64}" style="width: 50px; height: 50px; opacity: 0.8;">
                            <div style="font-size: 7px; color: #999;">SCAN TO VERIFY</div>
                        </div>
                    </div>
                </div>
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
        
        # Paths to wkhtmltopdf (common Windows installation paths)
        wkhtmltopdf_paths = [
            r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
            r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
            os.path.join(os.environ.get('USERPROFILE', ''), r'AppData\Local\Programs\wkhtmltopdf\bin\wkhtmltopdf.exe'),
            'wkhtmltopdf' # Try from PATH
        ]
        
        wkhtmltopdf_path = None
        for path in wkhtmltopdf_paths:
            if os.path.exists(path) or path == 'wkhtmltopdf':
                wkhtmltopdf_path = path
                if path == 'wkhtmltopdf': break # If in PATH, use it
                if os.path.exists(path): break
        
        if not wkhtmltopdf_path:
            return JsonResponse({
                'success': False,
                'error': 'wkhtmltopdf not found. Please install it on the server to enable PDF downloads.'
            }, status=400)
            
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        
        # Generate PDF
        try:
            pdf = pdfkit.from_string(html_string, False, options=options, configuration=config)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'PDF Generation failed: {str(e)}. Make sure wkhtmltopdf is correctly installed.'
            }, status=400)
        
        # Create response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{cv.full_name}_{cv.template}_CV.pdf"'
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
            cv.full_name = data.get('personalInfo', {}).get('name', cv.full_name)
            cv.email = data.get('personalInfo', {}).get('email', cv.email)
            cv.phone = data.get('personalInfo', {}).get('phone', cv.phone)
            cv.address = data.get('personalInfo', {}).get('address', cv.address)
            cv.professional_title = data.get('personalInfo', {}).get('title', cv.professional_title)
            cv.summary = data.get('personalInfo', {}).get('summary', cv.summary)
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
@login_required
def upload_cv_image(request, cv_id):
    cv = get_object_or_404(CV, id=cv_id, user=request.user)
    
    # Handle deletion
    if request.GET.get('delete') == '1':
        if cv.profile_image:
            cv.profile_image.delete()
        messages.success(request, 'Profile image deleted.')
        return redirect('cv_dashboard')
        
    if request.method == 'POST' and request.FILES.get('profile_image'):
        cv.profile_image = request.FILES['profile_image']
        cv.save()
        messages.success(request, 'Profile image updated successfully!')
        
    return redirect('cv_dashboard')

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

@login_required
def manage_company(request):
    if hasattr(request.user, 'profile') and request.user.profile.user_type != 'recruiter':
        return redirect('cv_dashboard')
        
    company, _ = Company.objects.get_or_create(user=request.user, defaults={'name': f"{request.user.username}'s Company"})
    
    if request.method == 'POST':
        company.name = request.POST.get('name')
        company.description = request.POST.get('description')
        company.website = request.POST.get('website')
        company.location = request.POST.get('location')
        company.contact_email = request.POST.get('contact_email')
        if 'logo' in request.FILES:
            company.logo = request.FILES['logo']
        company.save()
        messages.success(request, 'Company profile updated successfully!')
        return redirect('cv_dashboard')
        
    return render(request, 'main/manage_company.html', {'company': company})

@login_required
def post_job(request):
    if hasattr(request.user, 'profile') and request.user.profile.user_type != 'recruiter':
        return redirect('cv_dashboard')
        
    company, _ = Company.objects.get_or_create(user=request.user, defaults={'name': f"{request.user.username}'s Company"})
        
    if request.method == 'POST':
        title = request.POST.get('title')
        offer_type = request.POST.get('offer_type', 'job')
        location = request.POST.get('location')
        description = request.POST.get('description')
        requirements = request.POST.get('requirements')
        salary_range = request.POST.get('salary_range')
        
        JobOffer.objects.create(
            company=company,
            title=title,
            offer_type=offer_type,
            location=location,
            description=description,
            requirements=requirements,
            salary_range=salary_range
        )
        messages.success(request, 'Job offer posted successfully!')
        return redirect('cv_dashboard')
        
    return render(request, 'main/post_job.html', {'company': company})

@login_required
def delete_job(request, job_id):
    if hasattr(request.user, 'profile') and request.user.profile.user_type != 'recruiter':
        return redirect('cv_dashboard')
    job = get_object_or_404(JobOffer, id=job_id, company__user=request.user)
    job.delete()
    messages.success(request, 'Job offer deleted.')
    return redirect('cv_dashboard')

@login_required
def manage_trainings(request):
    if hasattr(request.user, 'profile') and request.user.profile.user_type != 'recruiter':
        return redirect('cv_dashboard')
    
    company, _ = Company.objects.get_or_create(user=request.user, defaults={'name': f"{request.user.username}'s Company"})
    
    if request.method == 'POST':
        title = request.POST.get('title')
        provider = request.POST.get('provider')
        description = request.POST.get('description')
        duration = request.POST.get('duration')
        link = request.POST.get('link')
        
        TrainingCourse.objects.create(
            company=company,
            title=title,
            provider_name=provider,
            description=description,
            duration=duration,
            link=link
        )
        messages.success(request, 'Training course added!')
        return redirect('manage_trainings')

    trainings = TrainingCourse.objects.filter(company=company)
    return render(request, 'main/manage_trainings.html', {'trainings': trainings, 'company': company})

@login_required
def view_applications(request, job_id):
    if hasattr(request.user, 'profile') and request.user.profile.user_type != 'recruiter':
        return redirect('cv_dashboard')
    job = get_object_or_404(JobOffer, id=job_id, company__user=request.user)
    applications_list = list(job.applications.all())
    
    # Enrich applications with AI scores and data
    for app in applications_list:
        try:
            analysis = match_cv_to_job(app.cv, job)
            app.ai_score = analysis.get('match_percentage', 0)
            app.matching_skills = analysis.get('matching_skills', [])
            app.missing_skills = analysis.get('missing_skills', [])
        except Exception as e:
            app.ai_score = 0
            app.matching_skills = []
            app.missing_skills = []
    
    # Sort by AI score (Descending)
    applications_list.sort(key=lambda x: x.ai_score, reverse=True)
    
    return render(request, 'main/view_applications.html', {
        'job': job,
        'applications': applications_list
    })

@login_required
def update_application_status(request, app_id):
    if hasattr(request.user, 'profile') and request.user.profile.user_type != 'recruiter':
        return redirect('cv_dashboard')
    
    application = get_object_or_404(Application, id=app_id, job_offer__company__user=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status', '').lower()
        if new_status in dict(Application.STATUS_CHOICES):
            application.status = new_status
            application.save()
            
            # Prepare Highly Developed HTML Message
            dashboard_url = request.build_absolute_uri(reverse('cv_dashboard'))
            
            if new_status == 'accepted':
                subject = f"🎉 Congratulations! Your application for {application.job_offer.title} was Accepted"
                status_color = "#16a34a"
                status_text = "ACCEPTED"
                message_body = f"""
                    <p style="font-size: 16px; line-height: 1.6;">Great news! We are pleased to inform you that your application for the <strong>{application.job_offer.title}</strong> position at <strong>{application.job_offer.company.name}</strong> has been <strong>Accepted</strong>.</p>
                    <p>The hiring team was impressed with your profile and matching skills. They will be in touch with you shortly regarding the next steps in the onboarding process.</p>
                    <div style="margin: 30px 0; text-align: center;">
                        <a href="{dashboard_url}" style="background: #6366f1; color: white; padding: 12px 25px; border-radius: 30px; text-decoration: none; font-weight: bold; display: inline-block;">View My Dashboard</a>
                    </div>
                """
            elif new_status == 'rejected':
                subject = f"Update regarding your application for {application.job_offer.title}"
                status_color = "#dc2626"
                status_text = "NOT SELECTED"
                message_body = f"""
                    <p style="font-size: 16px; line-height: 1.6;">Thank you for your interest in the <strong>{application.job_offer.title}</strong> position at <strong>{application.job_offer.company.name}</strong>.</p>
                    <p>After a careful review of all applications, we regret to inform you that we will not be moving forward with your candidacy at this time.</p>
                    <p>This was a difficult decision, as we received many qualified applications. We encourage you to continue developing your skills and apply for future openings that match your profile. Don't be discouraged—your perfect opportunity is out there!</p>
                    <div style="margin: 30px 0; text-align: center;">
                        <a href="{dashboard_url}" style="color: #6366f1; text-decoration: underline; font-weight: bold;">Explore more jobs on CV Navigator</a>
                    </div>
                """
            else:
                subject = f"Status update for {application.job_offer.title}"
                status_color = "#d97706"
                status_text = application.get_status_display().upper()
                message_body = f"<p>Your application status has been updated to: <strong>{status_text}</strong>. Log in to your dashboard for more details.</p>"

            html_message = f"""
            <div style="font-family: 'Inter', sans-serif, Arial; max-width: 600px; margin: 0 auto; padding: 40px; border: 1px solid #e2e8f0; border-radius: 24px; color: #1e293b;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <span style="font-size: 40px;">📄</span>
                    <h2 style="color: #6366f1; margin: 10px 0;">CV Navigator Update</h2>
                </div>
                
                <p>Hello <strong>{application.cv.full_name}</strong>,</p>
                
                {message_body}
                
                <div style="background: #f8fafc; padding: 20px; border-radius: 12px; margin: 20px 0; text-align: center; border: 1px solid #e2e8f0;">
                    <span style="font-size: 12px; font-weight: 800; color: #64748b; display: block; margin-bottom: 5px;">CURRENT STATUS</span>
                    <span style="font-size: 24px; font-weight: 900; color: {status_color};">{status_text}</span>
                </div>
                
                <p style="font-size: 14px; color: #64748b; margin-top: 40px;">Best regards,<br>The Hiring Team at {application.job_offer.company.name}</p>
                
                <div style="margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 20px; font-size: 11px; color: #94a3b8; text-align: center;">
                    This is an automated notification from CV Navigator. Please do not reply to this email.
                </div>
            </div>
            """
            plain_message = strip_tags(html_message)
            
            try:
                send_mail(
                    subject,
                    plain_message,
                    'noreply@cvgenerator.com',
                    [application.cv.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                messages.success(request, f'Status updated to {application.get_status_display()} and HTML email sent to candidate.')
            except Exception as e:
                messages.warning(request, f'Status updated to {application.get_status_display()}, but email could not be sent. Error: {str(e)}')
                
    return redirect('view_applications', job_id=application.job_offer.id)

@login_required
def browse_jobs(request):
    jobs = JobOffer.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'main/browse_jobs.html', {'jobs': jobs})

@login_required
def browse_trainings(request):
    trainings = TrainingCourse.objects.all().order_by('-id')
    return render(request, 'main/browse_trainings.html', {'trainings': trainings})

@login_required
def apply_to_job(request, job_id):
    job = get_object_or_404(JobOffer, id=job_id, is_active=True)
    if request.method == 'POST':
        cv_id = request.POST.get('cv_id')
        cv = get_object_or_404(CV, id=cv_id, user=request.user)
        
        # Check if already applied
        if Application.objects.filter(job_offer=job, cv=cv).exists():
            messages.warning(request, 'You have already applied to this job with this CV.')
        else:
            Application.objects.create(job_offer=job, cv=cv)
            messages.success(request, f'Successfully applied to {job.title}!')
            
        return redirect('browse_jobs')
    
    user_cvs = CV.objects.filter(user=request.user)
    return render(request, 'main/apply_job.html', {'job': job, 'cvs': user_cvs})

@login_required
@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.save()
        
        profile = user.profile
        profile.bio = request.POST.get('bio', '')
        profile.location = request.POST.get('location', '')
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
    return redirect('cv_dashboard')

def ai_dashboard(request, cv_id):
    cv = get_object_or_404(CV, id=cv_id, user=request.user)
    
    # Try to use NLP engine to analyze CV and match jobs
    analysis_results = None
    job_matches = []
    
    try:
        # Get AI analysis
        analysis_results = analyze_cv(cv)
        
        # Get all active jobs
        active_jobs = JobOffer.objects.filter(is_active=True)
        
        # Match CV to each job
        for job in active_jobs:
            match_score = match_cv_to_job(cv, job)
            if match_score > 30:  # Only show reasonably good matches
                job_matches.append({
                    'job': job,
                    'score': match_score
                })
                
        # Sort matches by score descending
        job_matches.sort(key=lambda x: x['score'], reverse=True)
        
    except Exception as e:
        messages.warning(request, f"AI analysis is currently unavailable: {str(e)}")
        
    return render(request, 'main/ai_dashboard.html', {
        'cv': cv,
        'analysis': analysis_results,
        'job_matches': job_matches
    })

@login_required
def send_message(request, receiver_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        receiver = get_object_or_404(User, id=receiver_id)
        
        Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=content
        )
        
        # Also create a notification for the receiver
        Notification.objects.create(
            user=receiver,
            title="New Message",
            message=f"You have a new message from {request.user.first_name or request.user.username}."
        )
        
        messages.success(request, "Message sent successfully!")
    return redirect(request.META.get('HTTP_REFERER', 'cv_dashboard'))

@login_required
def submit_accomplishment(request, course_id):
    course = get_object_or_404(TrainingCourse, id=course_id)
    if request.method == 'POST':
        proof = request.FILES.get('proof_file')
        if proof:
            CourseAccomplishment.objects.create(
                user=request.user,
                course=course,
                proof_file=proof,
                status='pending'
            )
            messages.success(request, "Accomplishment submitted! The company will review it and issue your badge soon.")
        else:
            messages.error(request, "Please upload a proof file (PDF or Image).")
    return redirect('browse_trainings')

@login_required
def review_accomplishment(request, accomplishment_id):
    # Only recruiters from the company that owns the course can review
    accomplishment = get_object_or_404(CourseAccomplishment, id=accomplishment_id)
    if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'recruiter':
        return HttpResponse("Forbidden", status=403)
    
    if request.method == 'POST':
        action = request.POST.get('action') # 'approve' or 'reject'
        if action == 'approve':
            accomplishment.status = 'approved'
            accomplishment.save()
            
            # Issue Badge
            import uuid
            Badge.objects.create(
                user=accomplishment.user,
                course=accomplishment.course,
                issued_by=accomplishment.course.company,
                badge_code=str(uuid.uuid4())[:8].upper()
            )
            
            Notification.objects.create(
                user=accomplishment.user,
                title="🏆 New Badge Earned!",
                message=f"Congratulations! Your accomplishment for {accomplishment.course.title} has been approved and a badge has been issued to your profile."
            )
            messages.success(request, "Accomplishment approved and badge issued!")
        else:
            accomplishment.status = 'rejected'
            accomplishment.save()
            messages.warning(request, "Accomplishment rejected.")
            
    return redirect('cv_dashboard')