from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.core.files.storage import FileSystemStorage
from readbackend.apps.users.models import Stories, ReadingSession, PerformanceData

import speech_recognition as sr
import os
def user_signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to login page or another page
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})
def reading_session(request, story_id):
    if request.method == "POST" and request.FILES.get('audio'):
        # Handle uploaded audio file
        audio_file = request.FILES['audio']
        fs = FileSystemStorage()
        filename = fs.save(audio_file.name, audio_file)
        filepath = fs.path(filename)
        
        # Convert audio to text using speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(filepath) as source:
            audio_data = recognizer.record(source)
            try:
                spoken_text = recognizer.recognize_google(audio_data)  # or use another speech-to-text API
            except sr.UnknownValueError:
                return JsonResponse({'error': 'Could not understand the audio'}, status=400)
            except sr.RequestError as e:
                return JsonResponse({'error': f'Error with the speech recognition service: {e}'}, status=500)
        
        # Get the original story
        story = Stories.objects.get(id=story_id)
        original_text = story.fulltext
        
        # Convert both the original text and spoken text to phonemes
        original_phonemes = text_to_phonemes(original_text)
        spoken_phonemes = text_to_phonemes(spoken_text)
        
        # Compare phonemes
        is_correct = original_phonemes == spoken_phonemes
        
        # Save performance data
        performance = PerformanceData(
            reader=request.user,
            word=spoken_text,
            pronunciation_attempts=1,  # This could be more dynamic
            is_correct=is_correct
        )
        performance.save()
        
        # Cleanup - remove the audio file
        os.remove(filepath)
        
        # Return result as JSON
        return JsonResponse({'is_correct': is_correct})
    
    else:
        story = Stories.objects.get(id=story_id)
        return render(request, 'reading_session.html', {'story': story})