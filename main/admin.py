from django.contrib import admin
from .models import CV, Experience, Education, Skill, Language, Certification, Interest, Company, JobOffer, TrainingCourse, Application, SkillReference, Project, Notification, Message

# Customizing the Admin Site Header & Title
admin.site.site_header = "CV Navigator Administration"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Welcome to the CV Navigator Management Portal"

# Inlines for CV Admin
class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 1

class EducationInline(admin.TabularInline):
    model = Education
    extra = 1

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1

@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'professional_title', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['full_name', 'email', 'professional_title']
    inlines = [ExperienceInline, EducationInline, SkillInline]
    
    fieldsets = (
        ('Personal Info', {
            'fields': ('user', 'full_name', 'professional_title', 'email', 'phone', 'profile_image')
        }),
        ('Socials', {
            'fields': ('linkedin_url', 'github_url', 'website_url')
        }),
        ('Summary', {
            'fields': ('summary',)
        }),
    )

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'location', 'contact_email']
    search_fields = ['name', 'contact_email', 'location']
    list_per_page = 20

@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'offer_type', 'location', 'is_active', 'created_at']
    list_filter = ['offer_type', 'is_active', 'company', 'created_at']
    search_fields = ['title', 'description', 'requirements']
    date_hierarchy = 'created_at'

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['cv', 'job_offer', 'status', 'ai_score', 'applied_at']
    list_filter = ['status', 'applied_at']
    search_fields = ['cv__full_name', 'job_offer__title']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']

admin.site.register(TrainingCourse)
admin.site.register(SkillReference)
admin.site.register(Language)
admin.site.register(Certification)
admin.site.register(Interest)
admin.site.register(Project)
admin.site.register(Experience)
admin.site.register(Education)
admin.site.register(Skill)