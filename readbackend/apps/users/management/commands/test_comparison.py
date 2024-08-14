from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.users.models import Stories
import speech_recognition as sr

class Command(BaseCommand):
    help = 'Test audio text comparison'

    def handle(self, *args, **kwargs):
        # Read the story from the database
        story = Stories.objects.get(id=1)  # Adjust the ID as needed
        original_text = story.fulltext
        
        # Read the test audio file
        audio_file_path = r'C:/Users/kent1/Documents/Reading Tutor Project/read-backend-application/WhatsApp Audio 2024-08-13 at 16.11.36_a29358fe.dat'
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)
            try:
                spoken_text = recognizer.recognize_google(audio_data)
            except sr.UnknownValueError:
                self.stdout.write(self.style.ERROR('Could not understand the audio'))
                return
            except sr.RequestError as e:
                self.stdout.write(self.style.ERROR(f'Error with the speech recognition service: {e}'))
                return
        
        # Read the expected text from file
        text_file_path = r'C:/Users/kent1/Documents/Reading Tutor Project/read-backend-application/test_document.txt'
        with open(text_file_path, 'r') as file:
            expected_text = file.read().strip()
        
        # Convert both texts to phonemes
        original_phonemes = text_to_phonemes(original_text)
        spoken_phonemes = text_to_phonemes(spoken_text)
        expected_phonemes = text_to_phonemes(expected_text)
        
        # Compare phonemes
        is_correct = spoken_phonemes == expected_phonemes
        
        # Output the result
        self.stdout.write(f'Spoken Text: {spoken_text}')
        self.stdout.write(f'Original Text: {original_text}')
        self.stdout.write(f'Is Correct: {is_correct}')