import os
import django

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'readbackend.readbackend.settings')

# Setup Django
django.setup()


from readbackend.apps.users.models import Stories
#from readbackend.utils import convert_audio_to_text



# Load your text file and read its contents
with open("C:/Users/Admin/Desktop/Capstone_csc3003s/read-backend-application/readbackend/media/text", "r") as f:
    text_data = f.read()

# Convert the audio file to text
audio_file = "C:/Users/Admin/Desktop/Capstone_csc3003s/read-backend-application/readbackend/media/audio/WhatsApp Audio 2024-08-12 at 3.38.46 PM (online-audio-converter.com).mp3"
recognized_text = convert_audio_to_text(audio_file)

# Compare the recognized text with the expected text
if recognized_text == expected_text:
    print("The audio matches the text!")
else:
    print("The audio does not match the text.")