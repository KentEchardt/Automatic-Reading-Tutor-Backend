from rest_framework import serializers
from .models import User, Story, ReadingSession, Class, Student
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['role'] = user.role
        token['reading_level'] = user.reading_level
        return token
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'role', 'reading_level','date_joined','previous_reading_level']
        extra_kwargs = {
            'reading_level': {'required': False},  # Optional 
            'password': {'write_only': True}  # Ensure password is write-only
        }
    
    def create(self, validated_data):
        # Extract password from validated_data
        password = validated_data.pop('password', None)
        # Create user instance
        user = super().create(validated_data)
        if password:
            # Hash the password and save the user
            user.set_password(password)
            user.save()
        return user

class StorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = ['id', 'title', 'description', 'fulltext', 'difficulty_level', 'image']

class ReadingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingSession
        fields = ['id', 'user', 'story', 'start_datetime', 'end_datetime', 'story_progress']

class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ['id', 'teacher', 'class_code']

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'reader', 'class_code']
