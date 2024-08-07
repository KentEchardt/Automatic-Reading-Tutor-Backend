from django.shortcuts import render
from models import Users
from faster_whisper import WhisperModel

# Create your views here.

# Model reccomended by the Client
model_size = "large-v3"
model = WhisperModel(model_size, device="cpu", compute_type="int8")


