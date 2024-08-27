from django.contrib import admin
from .models import User, Story, ReadingSession, Student, Class

admin.site.register(User)
admin.site.register(Story)
admin.site.register(ReadingSession)
admin.site.register(Student)
admin.site.register(Class)