from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils import timezone
from datetime import timedelta

# User model, broken down into admin, teacher and reader roles
class User(AbstractUser):
    ROLES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('reader', 'Reader'),
    )
    role = models.CharField(max_length=10, choices=ROLES)
    reading_level = models.FloatField()  # Only for Readers
    previous_reading_level = models.FloatField()

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  # Custom related name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',  # Custom related name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username

# Story model
class Story(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    fulltext = models.TextField()
    difficulty_level = models.CharField(max_length=50)
    image = models.ImageField(upload_to='resources/story_images/')

    def __str__(self):
        return self.title

# Reading Session model
class ReadingSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    start_datetime = models.DateTimeField(default=timezone.now)
    end_datetime = models.DateTimeField(null=True, blank=True)
    story_progress = models.FloatField()  # e.g., percentage of story completed
    total_errors = models.IntegerField(default=0)  # Track the total number of errors
    total_reading_time = models.DurationField(default=timedelta(0))  # Track the total reading time
    current_position = models.PositiveIntegerField(default=0)  # Add this new field

    def save(self, *args, **kwargs):
        # Update story_progress whenever the model is saved
        if self.story:
            self.story_progress = (self.current_position / len(self.story.fulltext)) * 100
        super().save(*args, **kwargs)

    @property
    def calculated_progress(self):
        if self.story:
            return (self.current_position / len(self.story.fulltext)) * 100
        return 0

    def __str__(self):
        return f'{self.user.username} - {self.story.title}'
    
# Class model and Student model- store relations between Teachers and Readers (a Reader is in a Teacher's class)
class Class(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    class_code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.class_code
    
class Student(models.Model):
    reader = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'reader'})
    class_code = models.ForeignKey(Class, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.reader.username} in {self.class_code.class_code}'


