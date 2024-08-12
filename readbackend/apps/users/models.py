from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth.models import User

class Users(models.Model):
    username = models.CharField(max_length=30)
    password = models.CharField(max_length=30)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    birth_date = models.DateField()
    email = models.EmailField()
    difficulty_level = models.IntegerField()#to show the difficulty level
    allowed_readers = models.ManyToManyField(User, related_name='allowed_stories')#to show the stories on has access to
    

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Stories(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=50)
    description = models.TextField()
    fulltext = models.TextField()

    def __str__(self):
        return self.title

class ReadingSession(models.Model):
    userID = models.ForeignKey('Users', on_delete=models.CASCADE)
    storyID = models.ForeignKey('Stories', on_delete=models.CASCADE)
    progress = models.DecimalField(max_digits=5, decimal_places=2)
    startTime = models.DateTimeField()
    endTime = models.DateTimeField()

# Performance data model to track user's progress with pronunciation and reading
class PerformanceData(models.Model):
    reader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_data')
    word = models.CharField(max_length=100)
    pronunciation_attempts = models.IntegerField(default=0)
    is_correct = models.BooleanField(default=False)
    last_attempt_time = models.DateTimeField(default=timezone.now)
# Extending the User model to include roles (optional)
User.add_to_class('is_reader', models.BooleanField(default=False))
User.add_to_class('is_admin', models.BooleanField(default=False))
