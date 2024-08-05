from django.contrib import admin
from .models import Users, Stories, ReadingSession

admin.site.register(Users)
admin.site.register(Stories)
admin.site.register(ReadingSession)