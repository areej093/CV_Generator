from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # The 'username' parameter receives the email address from the login form
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # Fallback if there are multiple users with the same email (shouldn't happen after our fixes)
            user = User.objects.filter(email=username).first()
            
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
