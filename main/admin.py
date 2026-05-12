from django.contrib import admin
from .models import CV, Experience, Education, Skill, Language, Certification, Interest, Company, JobOffer, TrainingCourse, Application, SkillReference, Project

@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'professional_title', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['full_name', 'email']

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ['position', 'company', 'cv']
    
@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ['degree', 'institution', 'cv']
    
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'cv']

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'location', 'contact_email']
    search_fields = ['name', 'contact_email']

@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'offer_type', 'location', 'is_active', 'created_at']
    list_filter = ['offer_type', 'is_active', 'company']
    search_fields = ['title', 'description']

@admin.register(TrainingCourse)
class TrainingCourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'provider_name', 'duration', 'created_at']
    search_fields = ['title', 'provider_name', 'description']

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['cv', 'job_offer', 'status', 'applied_at']
    list_filter = ['status', 'applied_at']

@admin.register(SkillReference)
class SkillReferenceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']
    search_fields = ['name']

admin.site.register(Language)
admin.site.register(Certification)
admin.site.register(Interest)