
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets
from .models import User, Story, ReadingSession, Class, Student
from .serializers import UserSerializer, StorySerializer, ReadingSessionSerializer, StudentSerializer, ClassSerializer
from rest_framework.decorators import action
from rest_framework.response import Response

from .services import match_audio_to_text

@method_decorator(csrf_exempt, name='dispatch')
class AudioMatchView(View):
    def post(self, request):
        session_id = request.POST.get('session_id')
        audio_file = request.FILES.get('audio_file')

        if not session_id or not audio_file:
            return JsonResponse({'error': 'Invalid input'}, status=400)

        matching_text = "the quick brown fox jumps over the lazy dog" #Need to change function to receive sentence
        match_result = match_audio_to_text(audio_file, matching_text)

        return JsonResponse({'match': match_result})
    
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def create(self, request, *args, **kwargs):
        role = request.data.get('role')
        reading_level = request.data.get('reading_level')

        if role == 'reader' and not reading_level:
            return Response({"error": "Reading level is required for readers."}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    @action(detail=False)
    def admins(self, request):
        admins = self.queryset.filter(role='admin')
        serializer = self.get_serializer(admins, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def teachers(self, request):
        teachers = self.queryset.filter(role='teacher')
        serializer = self.get_serializer(teachers, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def readers(self, request):
        readers = self.queryset.filter(role='reader')
        serializer = self.get_serializer(readers, many=True)
        return Response(serializer.data)

    @action(detail=True, url_path=r'by-username/(?P<username>\w+)')
    def get_by_username(self, request, username=None):
        user = self.queryset.filter(username=username).first()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

class StoryViewSet(viewsets.ModelViewSet):
    queryset = Story.objects.all()
    serializer_class = StorySerializer

class ReadingSessionViewSet(viewsets.ModelViewSet):
    queryset = ReadingSession.objects.all()
    serializer_class = ReadingSessionSerializer

    @action(detail=True, url_path=r'by-user/(?P<user_id>\d+)/story/(?P<story_id>\d+)')
    def get_user_story(self, request, user_id=None, story_id=None):
        session = self.queryset.filter(user__id=user_id, story__id=story_id).first()
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    

class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer