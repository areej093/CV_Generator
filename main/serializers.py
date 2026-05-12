from rest_framework import serializers
from .models import CV, Experience, Education, Skill, Certification, Language, Interest, Project

class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        exclude = ('cv',)

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        exclude = ('cv',)

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        exclude = ('cv',)

class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        exclude = ('cv',)

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        exclude = ('cv',)

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        exclude = ('cv',)

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        exclude = ('cv',)

class CVSerializer(serializers.ModelSerializer):
    experiences = ExperienceSerializer(many=True, required=False)
    education = EducationSerializer(many=True, required=False)
    skills = SkillSerializer(many=True, required=False)
    certifications = CertificationSerializer(many=True, required=False)
    languages = LanguageSerializer(many=True, required=False)
    interests = InterestSerializer(many=True, required=False)
    projects = ProjectSerializer(many=True, required=False)
    
    class Meta:
        model = CV
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

    def create(self, validated_data):
        experiences_data = validated_data.pop('experiences', [])
        education_data = validated_data.pop('education', [])
        skills_data = validated_data.pop('skills', [])
        certifications_data = validated_data.pop('certifications', [])
        languages_data = validated_data.pop('languages', [])
        interests_data = validated_data.pop('interests', [])
        projects_data = validated_data.pop('projects', [])
        
        cv = CV.objects.create(**validated_data)
        
        for exp_data in experiences_data:
            Experience.objects.create(cv=cv, **exp_data)
        for edu_data in education_data:
            Education.objects.create(cv=cv, **edu_data)
        for skill_data in skills_data:
            Skill.objects.create(cv=cv, **skill_data)
        for cert_data in certifications_data:
            Certification.objects.create(cv=cv, **cert_data)
        for lang_data in languages_data:
            Language.objects.create(cv=cv, **lang_data)
        for int_data in interests_data:
            Interest.objects.create(cv=cv, **int_data)
        for proj_data in projects_data:
            Project.objects.create(cv=cv, **proj_data)
            
        return cv

    def update(self, instance, validated_data):
        # Update scalar fields
        for attr, value in validated_data.items():
            if not isinstance(value, list):
                setattr(instance, attr, value)
        instance.save()
        
        # Helper to update nested relations (delete existing and recreate)
        def update_nested(related_manager, model_class, data_list):
            if data_list is not None:
                related_manager.all().delete()
                for item in data_list:
                    model_class.objects.create(cv=instance, **item)
        
        # Note: popping handles required=False
        if 'experiences' in validated_data:
            update_nested(instance.experiences, Experience, validated_data.pop('experiences'))
        if 'education' in validated_data:
            update_nested(instance.education, Education, validated_data.pop('education'))
        if 'skills' in validated_data:
            update_nested(instance.skills, Skill, validated_data.pop('skills'))
        if 'certifications' in validated_data:
            update_nested(instance.certifications, Certification, validated_data.pop('certifications'))
        if 'languages' in validated_data:
            update_nested(instance.languages, Language, validated_data.pop('languages'))
        if 'interests' in validated_data:
            update_nested(instance.interests, Interest, validated_data.pop('interests'))
        if 'projects' in validated_data:
            update_nested(instance.projects, Project, validated_data.pop('projects'))
            
        return instance
