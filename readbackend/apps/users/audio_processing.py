import torch
import librosa
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import subprocess
import io
import re

model_name = "facebook/wav2vec2-xlsr-53-espeak-cv-ft" #facebook/wav2vec2-lv-60-espeak-cv-ft seems to transcribe more accurately -- Still need to work on alignment either way
model = Wav2Vec2ForCTC.from_pretrained(model_name)
processor = Wav2Vec2Processor.from_pretrained(model_name)

# Function to check if espeak-ng is installed
def check_espeak():
    return subprocess.run(["espeak-ng", "--version"], capture_output=True, text=True).returncode == 0

# Function to convert text to phonemes using eSpeak
def text_to_phonemes(text: str, language: str = "en-za") -> str:
    command = f'espeak-ng -v{language} --ipa=1 -q "{text}"'  # Added -q to suppress audio playback
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, _ = process.communicate()
    phonemes = output.decode("utf-8").strip()
    print("Text Phonemes:", phonemes)
    return phonemes

# Function to convert audio file to text using Wav2Vec2 and then to phonemes using eSpeak
def audio_to_phonemes(audio_file) -> str:
    waveform, _ = librosa.load(io.BytesIO(audio_file.read()), sr=16000)
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

# Example Usage
# if __name__ == "__main__":
#     example_text = "the quick brown fox jumps over the lazy dog"
#     audio_file_path = "path/to/your/audio/file.wav"  # Ensure this path points to a WAV file

#     try:
#         with open(audio_file_path, 'rb') as audio_file:
#             # Compare phonemes
#             match = compare_phonemes(audio_file, example_text)
#             if match:
#                 print("The phoneme strings match.")
#             else:
#                 print("The phoneme strings do not match.")
#     except RuntimeError as e:
#         print(f"Error: {e}")
