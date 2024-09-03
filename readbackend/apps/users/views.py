
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets
from .models import User, Story, ReadingSession, Class, Student
from .serializers import UserSerializer, StorySerializer, ReadingSessionSerializer, StudentSerializer, ClassSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from .audio_processing import compare_phonemes,  compare_phonemes_with_sequence_matcher, compare_phonemes_with_levenshtein
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from rest_framework import status
import base64
import mimetypes
from django.utils import timezone

from datetime import timedelta




@method_decorator(csrf_exempt, name='dispatch')
class AudioMatchView(View):
    def post(self, request):
        session_id = request.POST.get('session_id')
        audio_file = request.FILES.get('audio_file')
        matching_text = request.POST.get('matching_text')

        if not session_id or not audio_file or not matching_text:
            return JsonResponse({'error': 'Invalid input'}, status=400)

        try:
            session = ReadingSession.objects.get(id=session_id)
        except ReadingSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)

        # Perform the phoneme matching
        match_result = compare_phonemes_with_sequence_matcher(audio_file, matching_text)

        if not match_result:
            # Increment the error count if the match fails
            session.total_errors += 1
            session.save()
        else:
            # Logic for updating story progress could go here
            # For now, we simply increment the progress by some placeholder logic
            session.story_progress += 10.0  # Example increment (this would depend on your logic)
            session.save()

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
    
    @action(detail=False, url_path=r'check-username/(?P<username>\w+)')
    def check_username_exists(self, request, username=None):
        user_exists = self.queryset.filter(username=username).exists()
        return Response({"exists": user_exists}, status=status.HTTP_200_OK)

class StoryViewSet(viewsets.ModelViewSet):
    queryset = Story.objects.all()
    serializer_class = StorySerializer
    
    # Return only story IDs and difficulty levels - to be categorized on main page
    @action(detail=False, methods=['get'] )
    def get_story_listings(self, request):
        stories = Story.objects.values('id', 'difficulty_level')  # Fetch only 'id' and 'title'
        return Response(list(stories))
    
    
     # Return the image data and title of a story by its ID (for display in Story Card)
    @action(detail=True, methods=['get'])
    def get_story_cover(self, request, pk=None):
        story = get_object_or_404(Story, pk=pk)
        if story.image:
            try:
                # Open the image file
                with story.image.open() as image_file:
                    # Read image data
                    image_data = image_file.read()
                    # Encode image data to base64
                    encoded_image_data = base64.b64encode(image_data).decode('utf-8')
                    
                    # Determine the content type based on the file extension
                    content_type, _ = mimetypes.guess_type(story.image.name)

                    # Create the response data
                    response_data = {
                        'title': story.title,
                        'image_data': encoded_image_data,
                        'content_type': content_type or 'application/octet-stream'  # Default content type if not found
                    }

                    return JsonResponse(response_data)

            except FileNotFoundError:
                return Response({'error': 'Image not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'error': 'No image available for this story'}, status=status.HTTP_404_NOT_FOUND)
    

class ReadingSessionViewSet(viewsets.ModelViewSet):
    queryset = ReadingSession.objects.all()
    serializer_class = ReadingSessionSerializer

    @action(detail=True, url_path=r'by-user/(?P<user_id>\d+)/story/(?P<story_id>\d+)')
    def get_user_story(self, request, user_id=None, story_id=None):
        session = self.queryset.filter(user__id=user_id, story__id=story_id).first()
        serializer = self.get_serializer(session)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='create-session')
    def create_session(self, request):
        user_id = request.data.get('user_id')
        story_id = request.data.get('story_id')

        if not user_id or not story_id:
            return Response({'error': 'User ID and Story ID are required.'}, status=400)

        session = ReadingSession.objects.create(user_id=user_id, story_id=story_id, start_datetime=timezone.now())
        return Response({'session_id': session.id}, status=201)

    @action(detail=False, methods=['post'], url_path='start-session')
    def start_session(self, request):
        user_id = request.data.get('user_id')
        story_id = request.data.get('story_id')

        if not user_id or not story_id:
            return Response({'error': 'User ID and Story ID are required.'}, status=400)

        session = ReadingSession.objects.filter(user_id=user_id, story_id=story_id).order_by('-end_datetime').first()

        if session and not session.end_datetime:
            # Resume an existing session that hasn't been ended yet
            return Response({'session_id': session.id}, status=200)

        # Otherwise, create a new session
        new_session = ReadingSession.objects.create(user_id=user_id, story_id=story_id, start_datetime=timezone.now())
        return Response({'session_id': new_session.id}, status=201)

    @action(detail=False, methods=['post'], url_path='end-session')
    def end_session(self, request):
        session_id = request.data.get('session_id')
        time_reading = request.data.get('time_reading')

        try:
            session = ReadingSession.objects.get(id=session_id)
        except ReadingSession.DoesNotExist:
            return Response({'error': 'Session not found.'}, status=404)

        session.end_datetime = timezone.now()
        
        # Add the time_reading (received from frontend) to total_reading_time
        session.total_reading_time += timedelta(seconds=int(time_reading))
        session.save()

        return Response({'message': 'Session ended and time updated successfully.'}, status=200)
    

class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer