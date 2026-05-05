from django.db import models
from django.contrib.auth.models import User

class CV(models.Model):
    TEMPLATE_CHOICES = [
        ('modern', '✨ Modern Professional'),
        ('classic', '📋 Classic Elegant'),
        ('creative', '🎨 Creative Design'),
        ('minimal', '⚡ Minimal Clean'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cvs')
    title = models.CharField(max_length=200, default='My CV')
    template = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default='modern')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=200, blank=True)
    professional_title = models.CharField(max_length=200, blank=True)
    summary = models.TextField(blank=True)

    linkedin_url = models.URLField(max_length=500, blank=True, null=True)
    
    
    def __str__(self):
        return f"{self.full_name}'s CV"
    
    class Meta:
        ordering = ['-created_at']

class Experience(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='experiences')
    position = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    duration = models.CharField(max_length=100)  # e.g., "2020-2023"
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.position} at {self.company}"

class Education(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='education')
    degree = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    year = models.CharField(max_length=50)  # e.g., "2022" or "2020-2024"
    
    def __str__(self):
        return f"{self.degree} from {self.institution}"

class Skill(models.Model):
    SKILL_LEVELS = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Expert', 'Expert'),
    ]
    
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=20, choices=SKILL_LEVELS, default='Intermediate')
    
    
    def __str__(self):
        return f"{self.name} - {self.level}"