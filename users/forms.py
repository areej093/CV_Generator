from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import uuid

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, label="Full Name")
    user_type = forms.ChoiceField(choices=[('student', 'Student / Recent Graduate'), ('recruiter', 'Company / Recruiter')], initial='student')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "email", "user_type")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = str(uuid.uuid4())[:30]
        if commit:
            user.save()
            # Profile is created automatically by signal, so we update it
            profile = user.profile
            profile.user_type = self.cleaned_data.get('user_type')
            profile.save()
        return user
