"""
URL configuration for readbackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.users import views



urlpatterns = [
    # path('admin/', admin.site.urls),
    # path('users/',include('readbackend.urls')),
    path('match-audio/', views.AudioMatchView.as_view(), name='match-audio'),
    #path('signup/', views.user_signup, name='signup'),
    #path('login/', views.user_login, name='login'),
    #path('stories/<int:difficulty_level>/', views.list_stories, name='list_stories'),
    #path('start-reading/<int:story_id>/', views.start_reading, name='start_reading'),
    #path('pronounce/<str:word>/', views.pronounce_word, name='pronounce_word'),
    #path('end-reading/<int:session_id>/', views.end_reading, name='end_reading'),
    #path('performance/<int:reader_id>/', views.check_performance, name='check_performance'),
]
