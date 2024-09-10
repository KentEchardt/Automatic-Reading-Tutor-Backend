import torch
import librosa
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import subprocess
import io
import re
from difflib import SequenceMatcher
import Levenshtein

model_name = "facebook/wav2vec2-xlsr-53-espeak-cv-ft" #facebook/wav2vec2-lv-60-espeak-cv-ft seems to transcribe more accurately -- Still need to work on alignment either way
model = Wav2Vec2ForCTC.from_pretrained(model_name)
processor = Wav2Vec2Processor.from_pretrained(model_name)


# Function to convert text to phonemes using eSpeak
def text_to_phonemes(text: str, language: str = "en-us") -> str: #Found that US english was best 
    command = f'espeak-ng -v{language} --ipa=1 -q "{text}"'  # Added -q to suppress audio playback
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, _ = process.communicate()
    phonemes = output.decode("utf-8").strip()
    print("Text Phonemes:", phonemes)
    return phonemes

# Function to convert audio file to text using Wav2Vec2 and then to phonemes using eSpeak
def audio_to_phonemes(audio_file) -> str:
    wav_file = convert_audio_to_wav(audio_file)
    waveform, _ = librosa.load(io.BytesIO(wav_file.read()), sr=16000)
    input_values = processor(waveform, return_tensors="pt", sampling_rate=16000).input_values
    with torch.no_grad():
        logits = model(input_values).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)[0]
    print("Audio Transcription:", transcription)
    return transcription

# Function to clean and normalize phoneme strings
def normalize_phonemes(phonemes: str) -> str:
    # Remove non-phoneme characters and normalize whitespace
    phonemes = phonemes.replace('_', ' ')  # Replace underscores with spaces
    phonemes = re.sub(r'\s+', ' ', phonemes)  # Normalize multiple spaces to a single space
    phonemes = phonemes.strip()  # Remove leading and trailing spaces
    return phonemes

# Function to compare phoneme strings
def compare_phonemes(audio_file, text: str) -> bool:
    # Convert audio to text and then to phonemes
    audio_transcription = audio_to_phonemes(audio_file)
    # Convert text to phonemes
    text_phonemes = text_to_phonemes(text)
    # Normalize and map phonemes
    normalized_audio_phonemes = normalize_phonemes(audio_transcription)
    normalized_text_phonemes = normalize_phonemes(text_phonemes)
    print("Normalized Audio Phonemes:", normalized_audio_phonemes)
    print("Normalized Text Phonemes:", normalized_text_phonemes)
    # Compare normalized phonemes
    answer = (normalized_audio_phonemes == normalized_text_phonemes)
    print("Phoneme Comparison Result:", answer)
    return answer


# Function to convert audio_file from webm (as received) to Wav (as needed by Librosa)
def convert_audio_to_wav(audio_file):
    input_audio = io.BytesIO(audio_file.read())
    output_audio = io.BytesIO()

    # Convert audio using ffmpeg
    command = [
        'ffmpeg', '-i', 'pipe:0', '-f', 'wav', 'pipe:1'
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(input=input_audio.read())

    if process.returncode != 0:
        raise RuntimeError(f'ffmpeg error: {stderr.decode()}')

    output_audio.write(stdout)
    output_audio.seek(0)  # Reset buffer position to the beginning
    return output_audio

# Function to compare phonemes with a tolerance using SequenceMatcher
def compare_phonemes_with_sequence_matcher(audio_file, text: str, threshold=0.75) -> bool:  # 0.75 is a little generous, but might be necessary
    audio_transcription = audio_to_phonemes(audio_file)
    text_phonemes = text_to_phonemes(text)
    normalized_audio_phonemes = normalize_phonemes(audio_transcription)
    normalized_text_phonemes = normalize_phonemes(text_phonemes)
    print("Normalized Audio Phonemes:", normalized_audio_phonemes)
    print("Normalized Text Phonemes:", normalized_text_phonemes)
    matcher = SequenceMatcher(None, normalized_audio_phonemes, normalized_text_phonemes)
    similarity = matcher.ratio()
    print(f"SequenceMatcher Similarity: {similarity}")
    return similarity >= threshold

# Function to compare phonemes with a tolerance using Levenshtein distance
def compare_phonemes_with_levenshtein(audio_file, text: str, tolerance=0.2) -> bool:
    audio_transcription = audio_to_phonemes(audio_file)
    text_phonemes = text_to_phonemes(text)
    normalized_audio_phonemes = normalize_phonemes(audio_transcription)
    normalized_text_phonemes = normalize_phonemes(text_phonemes)
    print("Normalized Audio Phonemes:", normalized_audio_phonemes)
    print("Normalized Text Phonemes:", normalized_text_phonemes)
    
    # Calculate Levenshtein Distance
    distance = Levenshtein.distance(normalized_audio_phonemes, normalized_text_phonemes)
    max_len = max(len(normalized_audio_phonemes), len(normalized_text_phonemes))
    
    # Determine if distance is within tolerance
    similarity = 1 - (distance / max_len)
    print(f"Levenshtein Distance: {distance}")
    print(f"Similarity: {similarity}")
    return similarity >= (1 - tolerance)