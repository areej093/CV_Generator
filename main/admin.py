from django.contrib import admin
from .models import CV, Experience, Education, Skill

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