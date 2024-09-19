
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
from django.db.models import Count, Sum, Avg, F, Q, OuterRef, Subquery
from django.db import transaction


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
        # match_result = compare_phonemes_with_sequence_matcher(audio_file, matching_text)
        match_result = compare_phonemes_with_levenshtein(audio_file, matching_text)

        with transaction.atomic():
            session = ReadingSession.objects.select_for_update().get(id=session_id)
            
            if not match_result:
                session.total_errors += 1
            else:
                # Update the current position
                current_position = session.current_position
                next_position = current_position + len(matching_text)
                
                # Ensure we don't exceed the story length
                session.current_position = min(next_position, len(session.story.fulltext))

            session.save()

        return JsonResponse({'match': match_result})
    
# View / endpoint for getting pronunciation of a specified word / sentence
@method_decorator(csrf_exempt, name='dispatch')
class PronunciationView(View):
    
    def post(self, request):
        mispronounced_text = request.POST.get('mispronounced_text')
        
        if not mispronounced_text:
            return JsonResponse({'error': 'Invalid input'}, status=400)
        
        correct_pronunciation = get_phonetic_spelling(mispronounced_text)
        
        return JsonResponse({'correct_pronunciation': correct_pronunciation})

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
        request.data['previous_reading_level'] = 0

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


    @action(detail=False, methods=['get'])
    def average_reading_duration(self, request):
        avg_duration = ReadingSession.objects.aggregate(
            avg_duration=Avg('total_reading_time')
        )['avg_duration']
        
        if avg_duration:
            return Response({"average_duration": str(avg_duration)})
        return Response({"detail": "No reading sessions found."}, status=404)

    @action(detail=False, methods=['get'])
    def average_progress(self, request):
        avg_progress = ReadingSession.objects.aggregate(
            avg_progress=Avg('story_progress')
        )['avg_progress']
        
        if avg_progress is not None:
            return Response({"average_progress": avg_progress})
        return Response({"detail": "No reading sessions found."}, status=404)

    @action(detail=False, methods=['get'])
    def average_reading_level(self, request):
        avg_level = User.objects.filter(role='reader').aggregate(
            avg_level=Avg('reading_level')
        )['avg_level']
        
        if avg_level is not None:
            return Response({"average_reading_level": avg_level})
        return Response({"detail": "No reader users found."}, status=404)

    @action(detail=False, methods=['get'])
    def average_time_to_complete(self, request):
        completed_sessions = ReadingSession.objects.filter(story_progress=100)
        avg_time = completed_sessions.aggregate(
            avg_time=Avg('total_reading_time')
        )['avg_time']
        
        if avg_time:
            return Response({"average_time_to_complete": str(avg_time)})
        return Response({"detail": "No completed reading sessions found."}, status=404)
    
    @action(detail=False,methods=['get'])
    def get_user_details(self,request):
        user=request.user
        username = user.username
        email=user.email
        role=user.role
        reading_level = user.reading_level
        return Response({"username":username,"email":email,"reading_level":reading_level,"role":role})
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)


        # Set the new password
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        
        
    
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
    

    @action(detail=False, methods=['get'])
    def get_current_story_listings(self, request):
        user = request.user
        
        # Subquery to get the latest active reading session for each story
        latest_sessions = ReadingSession.objects.filter(
            user=user,
            story=OuterRef('pk'),
            end_datetime__isnull=True
        ).order_by('-start_datetime')
        
        # Query to get stories with their latest active session progress
        stories = Story.objects.annotate(
            latest_progress=Subquery(latest_sessions.values('story_progress')[:1]),
            session_id=Subquery(latest_sessions.values('id')[:1])
        ).filter(
            session_id__isnull=False,  # Ensure there's an active session
            latest_progress__lt=100  # Ensure progress is less than 100
        ).values('id', 'difficulty_level', 'latest_progress', 'session_id')
        
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
    

    @action(detail=False, methods=['get'])
    def most_popular(self, request):
        story = Story.objects.annotate(
            session_count=Count('readingsession')
        ).order_by('-session_count').first()
        
        if story:
            serializer = self.get_serializer(story)
            data = serializer.data
            data['session_count'] = story.session_count
            return Response(data)
        return Response({"detail": "No stories found."}, status=404)

    @action(detail=False, methods=['get'])
    def least_popular(self, request):
        story = Story.objects.annotate(
            session_count=Count('readingsession')
        ).order_by('session_count').first()
        
        if story:
            serializer = self.get_serializer(story)
            data = serializer.data
            data['session_count'] = story.session_count
            return Response(data)
        return Response({"detail": "No stories found."}, status=404)

    @action(detail=False, methods=['get'])
    def most_engaged(self, request):
        story = Story.objects.annotate(
            total_engagement=Sum('readingsession__total_reading_time')
        ).order_by('-total_engagement').first()
        
        if story:
            serializer = self.get_serializer(story)
            data = serializer.data
            data['total_engagement'] = str(story.total_engagement)  # Convert timedelta to string
            return Response(data)
        return Response({"detail": "No stories found."}, status=404)
        
    @action(detail=True, methods=['put'])
    def update_story(self, request, pk=None):
        try:
            story = self.get_object()  # Get the story instance
        except Story.DoesNotExist:
            return Response({'error': 'Story not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Extract the fields from request data
        title = request.data.get('title')
        description = request.data.get('description')
        fulltext = request.data.get('fulltext')
        difficulty_level = request.data.get('difficulty_level')
        image = request.FILES.get('image')  # Handle image file separately

        # Validate required fields
        if not title or not description or not fulltext or not difficulty_level:
            return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Perform the update
        with transaction.atomic():
            story.title = title
            story.description = description
            story.fulltext = fulltext
            story.difficulty_level = difficulty_level

            if image:
                story.image = image  # Update image if provided

            story.save()

        # Return updated story data
        serializer = self.get_serializer(story)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
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
    
    
    @action(detail=False, methods=['post'], url_path='end-session')
    def end_session(self, request):
        session_id = request.data.get('session_id')
        time_reading = request.data.get('time_reading')

        try:
            session = ReadingSession.objects.get(id=session_id)
        except ReadingSession.DoesNotExist:
            return Response({'error': 'Session not found.'}, status=404)

        session.end_datetime = timezone.now()
        
        # Update the user's reading level upon completion of a story
        user = session.user
        story = session.story
        difficulty_level = story.difficulty_level
        initial_reading_level = user.reading_level
        story_length = len(story.fulltext)
        
        difficulty_multipliers = {
            "easy": 2,
            "medium": 4,
            "hard": 5
        }
        
        multiplier = difficulty_multipliers.get(difficulty_level, 2)  # Default to 2 if difficulty_level is not found

        level_factor = 1 - (initial_reading_level / 500)  # Decreases from 1 to 0 as level approaches 500
        word_value = (story_length / 100) * multiplier * level_factor
        new_reading_level = min((initial_reading_level + word_value), 500)
        user.previous_reading_level = initial_reading_level
        user.reading_level = new_reading_level
        user.save()
        
        # Add the time_reading (received from frontend) to total_reading_time
        try:
            time_reading_seconds = int(time_reading)
            session.total_reading_time += timedelta(seconds=time_reading_seconds)
        except ValueError:
            return Response({'error': 'Invalid time_reading value.'}, status=400)

        session.save()
        

        return Response({'message': 'Session ended and time updated successfully.'}, status=200)
    
    @action(detail=False, methods=['get'], url_path='session-stats')
    def session_stats(self, request):
        session_id = request.query_params.get('session_id')  # Use query_params for GET request
        try:
            session = ReadingSession.objects.get(id=session_id)
        except ReadingSession.DoesNotExist:
            return Response({'error': 'Session not found.'}, status=404)
        
        user = session.user
        new_reading_level = user.reading_level
        initial_reading_level = user.previous_reading_level  # Set based on your logic
        total_reading_time = session.total_reading_time
        errors = session.total_errors
        progress = session.story_progress

        return Response({
            'progress': progress,
            'errors': errors,
            'total_reading_time': total_reading_time,
            'initial_reading_level': initial_reading_level,
            'new_reading_level': new_reading_level
        })
        
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
        unique_stories_count = ReadingSession.objects.filter(user=user,story_progress=100).values('story').distinct().count()
        total_stories_count = Story.objects.count()

        return Response({'total_stories_read': unique_stories_count, 'total_stories_count':total_stories_count}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='most-recent-story')
    def most_recent_story(self, request):
        """
        Endpoint to return the most recent story read by the authenticated user, 
        excluding sessions with an end_datetime.
        """
        user = request.user

        # Get the most recent reading session where end_datetime is None
        latest_session = ReadingSession.objects.filter(user=user, end_datetime__isnull=True).order_by('-start_datetime').first()

        if latest_session:
            # Retrieve the story associated with the latest session
            story = get_object_or_404(Story, id=latest_session.story.id)
            return Response({'story_id': story.id}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No reading sessions found for this user.'}, status=status.HTTP_404_NOT_FOUND)

    # Return the progress the user has made in their current reading session
    @action(detail=False, methods=['get'])
    def progress(self, request):
        session_id = request.query_params.get('session_id')  # Fetch from query params for GET request
        user = request.user
        try:
            session = ReadingSession.objects.get(id=session_id, user=user)  # Ensure session belongs to user
            return Response({'progress': session.story_progress}, status=status.HTTP_200_OK)
        except ReadingSession.DoesNotExist:
            return Response({'error': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    # Return the progress the user has made in a specific story
    @action(detail=False, methods=['get'])
    def progress_by_story(self, request):
        story_id = request.query_params.get('story_id')
        user = request.user
        try:
            story = Story.objects.get(id=story_id)  # Get a single Story object
            session = ReadingSession.objects.filter(user=user, story=story).order_by('-start_datetime').first()
            if session:
                return Response({'progress': session.story_progress}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'No reading session found for this story.'}, status=status.HTTP_404_NOT_FOUND)
        except Story.DoesNotExist:
            return Response({'error': 'Story not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
        # Return the current character index of current reading session
    @action(detail=False, methods=['get'])
    def current_position(self, request):
        session_id = request.query_params.get('session_id')  # Fetch from query params for GET request
        user = request.user
        try:
            session = ReadingSession.objects.get(id=session_id, user=user)  # Ensure session belongs to user
            return Response({'current_position': session.current_position}, status=status.HTTP_200_OK)
        except ReadingSession.DoesNotExist:
            return Response({'error': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)
        
    @action(detail=False, methods = ['post'], url_path='previous-sentence')
    def previous_sentence(self,request):
        session_id = request.POST.get('session_id')
        sentence = request.POST.get('sentence')
        
        if not session_id or not sentence:
            return JsonResponse({'error': 'Invalid input'}, status=400)

        try:
            session = ReadingSession.objects.get(id=session_id)
        except ReadingSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)


        with transaction.atomic():
            session = ReadingSession.objects.select_for_update().get(id=session_id)
            
            # Update the current position
            current_position = session.current_position
            previous_position = current_position - len(sentence)
            
            # Ensure we don't exceed the story length
            session.current_position = max(0, previous_position)

            session.save()

        return JsonResponse({'message': 'Sentence position updated successfully.'})

    

class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer