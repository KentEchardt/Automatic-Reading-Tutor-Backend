
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
from rest_framework import status
import base64
import mimetypes
from django.utils import timezone

from datetime import timedelta
from .permissions import IsAdmin, IsTeacher, IsReader
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.hashers import make_password


from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from .pronounce import get_phonetic_spelling


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# View / endpoint for matching received audio to text
@method_decorator(csrf_exempt, name='dispatch')
class AudioMatchView(View):
    # permission_classes = [IsReader] e.g. of setting permission class
    
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
    
# View / endpoint for getting pronunciation of a specified word / sentence
@method_decorator(csrf_exempt, name='dispatch')
class PronunciationView(View):
    
    def post(self,request):
        mispronounced_text = request.POST.get('mispronounced_text')
        
        if not(mispronounced_text) or mispronounced_text=="":
            return JsonResponse({'error': 'Invalid input'}, status=400)
        
        correct_pronunciation = get_phonetic_spelling(mispronounced_text)
        
        return JsonResponse({'correct_pronunciation':correct_pronunciation})

# Viewsets - views & endpoints for all models 

# Viewset for Users
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action == 'create' or self.action=='check_username_exists':
            return [AllowAny()]  # Allow user creation without authentication
        return [IsAuthenticated()]  # Require authentication for all other actions
    
    @action(detail=False, methods=['get'])
    def role(self, request):
        """
        Endpoint to return the role of the logged-in user.
        """
        user = request.user
        return Response({'role': user.role})
    
    @action(detail=False, methods=['get'])
    def username(self, request):
        """
        Endpoint to return the username of the logged-in user based on the token.
        """
        user = request.user
        return Response({'username': user.username})
    
    @action(detail=False, methods=['get'])
    def readinglevel(self, request):
        """
        Endpoint to return the reading level of the logged-in user based on the token.
        """
        user = request.user
        return Response({'reading_level': user.reading_level})
    
    
    def create(self, request, *args, **kwargs):
        role = request.data.get('role')

        # Set the reading level to 0 
        request.data['reading_level'] = 0

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Validate request data

        # Call the superclass method to save the user
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



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
        user_exists = self.queryset.filter(username__iexact=username).exists()
        return Response({"exists": user_exists}, status=status.HTTP_200_OK)

# Viewset for Stories
class StoryViewSet(viewsets.ModelViewSet):
    queryset = Story.objects.all()
    serializer_class = StorySerializer
    
    # View to return all stories (without images)
    @action(detail=False, methods=['get'] )
    def get_stories(self,request):
        stories = Story.objects.values('id','title','description','difficulty_level','fulltext')
        return Response(list(stories)) 
    
    # View to return easy stories (without images)
    @action(detail=False, methods=['get'] )
    def get_easy_stories(self,request):
        stories = Story.objects.filter(difficulty_level='easy').values('id','title','description','difficulty_level','fulltext')
        return Response(list(stories)) 
    
    # View to return medium stories (without images)
    @action(detail=False, methods=['get'] )
    def get_medium_stories(self,request):
        stories = Story.objects.filter(difficulty_level='medium').values('id','title','description','difficulty_level','fulltext')
        return Response(list(stories)) 

    # View to return hard stories (without images)
    @action(detail=False, methods=['get'] )
    def get_hard_stories(self,request):
        stories = Story.objects.filter(difficulty_level='hard').values('id','title','description','difficulty_level','fulltext')
        return Response(list(stories)) 
    
    # Return only story IDs and difficulty levels - to be categorized on main page
    @action(detail=False, methods=['get'] )
    def get_story_listings(self, request):
        stories = Story.objects.values('id', 'difficulty_level')  # Fetch only 'id' and 'difficulty level' 
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
    

        
# Viewset for ReadingSessions
class ReadingSessionViewSet(viewsets.ModelViewSet):
    queryset = ReadingSession.objects.all()
    serializer_class = ReadingSessionSerializer
   
    # View to start a reading session
    @action(detail=False, methods=['post'], url_path='start-session')
    def start_session(self, request):
        user = request.user
        story_id = request.data.get('story_id')

        if not story_id:
            return Response({'error': 'Story ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        story = Story.objects.filter(id=story_id).first()
        
        if not story:
            return Response({'error': 'Story not found.'}, status=status.HTTP_404_NOT_FOUND)

        session = ReadingSession.objects.filter(user=user, story=story).order_by('-end_datetime').first()

        if session and not session.end_datetime:
            # Resume an existing session that hasn't been ended yet
            return Response({'session_id': session.id}, status=status.HTTP_200_OK)

        # Otherwise, create a new session
        new_session = ReadingSession.objects.create(
            user=user,
            story=story,
            start_datetime=timezone.now(),
            story_progress=0.0,  # Initialize progress
            total_errors=0,       # Initialize errors
            total_reading_time=timedelta(0)  # Initialize reading time
        )

        return Response({'session_id': new_session.id}, status=status.HTTP_201_CREATED)
    
    
    # View to end a reading session
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
    
    # View to pause a reading session
    @action(detail=False, methods=['post'], url_path='pause-session')
    def pause_session(self, request):
        session_id = request.data.get('session_id')
        time_reading = request.data.get('time_reading')

        try:
            session = ReadingSession.objects.get(id=session_id)
        except ReadingSession.DoesNotExist:
            return Response({'error': 'Session not found.'}, status=404)
        
        # Add the time_reading (received from frontend) to total_reading_time
        session.total_reading_time += timedelta(seconds=int(time_reading))
        session.save()

        return Response({'message': 'Session paused and time updated successfully.'}, status=200)
    
    
    @action(detail=False, methods=['get'], url_path='total-stories-read')
    def total_stories_read(self, request):
        """
        Endpoint to return the total number of unique stories read by the authenticated user.
        """
        user = request.user

        # Count the number of unique stories the user has read
        unique_stories_count = ReadingSession.objects.filter(user=user).values('story').distinct().count()

        return Response({'total_stories_read': unique_stories_count}, status=status.HTTP_200_OK)


    @action(detail=False, methods=['get'], url_path='most-recent-story')
    def most_recent_story(self, request):
        """
        Endpoint to return the most recent story read by the authenticated user.
        """
        user = request.user

        # Get the most recent reading session for the user
        latest_session = ReadingSession.objects.filter(user=user).order_by('-start_datetime').first()

        if latest_session:
            # Retrieve the story associated with the latest session
            story = get_object_or_404(Story, id=latest_session.story.id)
            return Response({'story_id':story.id}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No reading sessions found for this user.'}, status=status.HTTP_404_NOT_FOUND)    

class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer