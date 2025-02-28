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
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView



router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'stories', views.StoryViewSet)
router.register(r'readingsessions', views.ReadingSessionViewSet)
router.register(r'classes', views.ClassViewSet)
router.register(r'students', views.StudentViewSet)





urlpatterns = [
    path('match-audio/', views.AudioMatchView.as_view(), name='match-audio'),
    path('get-pronunciation/', views.PronunciationView.as_view(), name='get-pronunciation'),
    path('api/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
    
]
