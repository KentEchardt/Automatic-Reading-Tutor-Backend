import os
import django
from pydub import AudioSegment

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'readbackend.readbackend.settings')

# Setup Django
django.setup()


from readbackend.apps.users.models import Stories
from readbackend.apps.users.views import *
#from readbackend.utils import convert_audio_to_text



# Load your text file and read its contents
with open("C:/Users/kent1/Documents/Reading Tutor Project/read-backend-application/test_document.txt", "r") as f:
    text_data = f.read()

print(text_data)
# Convert the audio file to text
audio_file = "C:/Users/kent1/Documents/Reading Tutor Project/read-backend-application/WhatsApp Audio 2024-08-12 at 3.38.46 PM (online-audio-converter.com).mp3"
recognized_text = convert_audio_to_text(audio_file)
print(recognized_text)

text_phonemes = text_to_phonemes(text_data)
print(text_phonemes)

similarity = phoneme_similarity(recognized_text, text_phonemes)
# Compare the recognized text with the expected text
if recognized_text == text_phonemes:
    print("The audio matches the text!")
else:
    print("The audio does not match the text.")