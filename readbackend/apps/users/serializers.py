from rest_framework import serializers
from .models import User, Story, ReadingSession, Class, Student

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'reading_level']

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
