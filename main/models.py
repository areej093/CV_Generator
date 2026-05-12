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
    profile_image = models.ImageField(upload_to='cv_photos/', null=True, blank=True)
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
    is_verified = models.BooleanField(default=False)
    certificate = models.FileField(upload_to='certificates/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.level}"

class Certification(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    year = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.name} from {self.issuer}"

class Language(models.Model):
    PROFICIENCY_LEVELS = [
        ('A1', 'A1 - Beginner'),
        ('A2', 'A2 - Elementary'),
        ('B1', 'B1 - Intermediate'),
        ('B2', 'B2 - Upper Intermediate'),
        ('C1', 'C1 - Advanced'),
        ('C2', 'C2 - Proficient/Native'),
    ]
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='languages')
    name = models.CharField(max_length=100)
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_LEVELS, default='B1')

    def __str__(self):
        return f"{self.name} ({self.proficiency})"

class Interest(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='interests')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    name = models.CharField(max_length=200)
    description = models.TextField()
    website = models.URLField(blank=True)
    location = models.CharField(max_length=200)
    contact_email = models.EmailField()
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    
    def __str__(self):
        return self.name

class JobOffer(models.Model):
    OFFER_TYPES = [
        ('job', 'Full-time Job'),
        ('internship', 'Internship'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_offers')
    title = models.CharField(max_length=200)
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPES, default='job')
    location = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField(blank=True, null=True)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} at {self.company.name}"

class TrainingCourse(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='training_courses', null=True, blank=True)
    title = models.CharField(max_length=200)
    provider_name = models.CharField(max_length=200) # e.g. "Tech Academy"
    description = models.TextField()
    duration = models.CharField(max_length=100)
    link = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', '⏳ Pending'),
        ('reviewed', '👀 Reviewed'),
        ('accepted', '✅ Accepted'),
        ('rejected', '❌ Rejected'),
    ]
    job_offer = models.ForeignKey(JobOffer, on_delete=models.CASCADE, related_name='applications')
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='job_applications')
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"{self.cv.full_name} - {self.job_offer.title}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

class Project(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='project_images/', null=True, blank=True)
    link = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.cv.full_name} - {self.title}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username}"

class Interview(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='interview')
    option1 = models.DateTimeField()
    option2 = models.DateTimeField()
    option3 = models.DateTimeField()
    selected_option = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, default='Online (Link to be sent)')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='pending') # pending, confirmed, rescheduled
    
    def __str__(self):
        return f"Interview for {self.application.cv.full_name}"

class SkillReference(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.name

class CourseAccomplishment(models.Model):
    STATUS_CHOICES = [
        ('pending', '⏳ Pending Review'),
        ('approved', '✅ Approved (Badge Issued)'),
        ('rejected', '❌ Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accomplishments')
    course = models.ForeignKey(TrainingCourse, on_delete=models.CASCADE, related_name='submissions')
    proof_file = models.FileField(upload_to='course_proofs/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submission_date = models.DateTimeField(auto_now_add=True)
    review_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title}"

class Badge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    course = models.ForeignKey(TrainingCourse, on_delete=models.CASCADE)
    issued_by = models.ForeignKey(Company, on_delete=models.CASCADE)
    issued_at = models.DateTimeField(auto_now_add=True)
    badge_code = models.CharField(max_length=100, unique=True) # For verification
    
    def __str__(self):
        return f"Badge: {self.course.title} for {self.user.username}"