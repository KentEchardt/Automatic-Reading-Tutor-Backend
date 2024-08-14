from django.shortcuts import render
from models import Users
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from datasets import load_dataset
import torch
import torchaudio
import subprocess


# Create your views here.

# Model reccomended by the Client
model_name = "facebook/wav2vec2-xlsr-53-espeak-cv-ft"
processor = Wav2Vec2Processor.from_pretrained(model_name)
model = Wav2Vec2ForCTC.from_pretrained(model_name)

#e.g. using Wav2Vec
audio_path = "path_to_your_audio_file.wav"
waveform, sample_rate = torchaudio.load(audio_path)
inputs = processor(waveform, sampling_rate=sample_rate, return_tensors="pt", padding=True)

with torch.no_grad():
    logits = model(inputs.input_values).logits

predicted_ids = torch.argmax(logits, dim=-1)
transcription = processor.batch_decode(predicted_ids, output_word_offsets=True)

#e.g. Using Espeak-ng 
def text_to_phonemes(text):
    result = subprocess.run(
        ["espeak", "-v", "en-za", "--ipa", text],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return result.stdout.strip()

phonemes = text_to_phonemes("Hello, how are you?")
print(phonemes)