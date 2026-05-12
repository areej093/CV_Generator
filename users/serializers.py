from django.contrib.auth.models import User
from rest_framework import serializers
import uuid

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    user_type = serializers.CharField(write_only=True, required=False, default='student')

    class Meta:
        model = User
        fields = ('id', 'first_name', 'email', 'password', 'user_type')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        user_type = validated_data.pop('user_type', 'student')
        user = User.objects.create_user(
            username=str(uuid.uuid4())[:30],
            first_name=validated_data.get('first_name', ''),
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        # Set user as inactive until email verification
        user.is_active = False
        user.save()
        
        # Save user_type to profile
        profile = user.profile
        profile.user_type = user_type
        profile.save()
        
        return user
