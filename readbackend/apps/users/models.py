from django.db import models

class Users(models.Model):
    username = models.CharField(max_length=30)
    password = models.CharField(max_length=30)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    birth_date = models.DateField()
    email = models.EmailField()

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
