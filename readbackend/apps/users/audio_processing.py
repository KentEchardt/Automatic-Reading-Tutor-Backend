import torch
import librosa
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import subprocess
import io

model_name = "facebook/wav2vec2-large-960h-lv60-self"
model = Wav2Vec2ForCTC.from_pretrained(model_name)
processor = Wav2Vec2Processor.from_pretrained(model_name)
    
# Function to check if espeak-ng is installed
def check_espeak():
    return subprocess.run(["espeak-ng", "--version"], capture_output=True, text=True).returncode == 0

# Function to convert text to phonemes using eSpeak
def text_to_phonemes(text: str, language: str = "en") -> str:
    
    command = f'espeak-ng -v{language} -x -q "{text}"'  # Added -q to suppress audio playback
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, _ = process.communicate()
    phonemes = output.decode("utf-8").strip()
    print(phonemes)
    return phonemes

# Function to convert audio file to text using Wav2Vec2 and then to phonemes using eSpeak
def audio_to_phonemes(audio_file) -> str:
    # Load the audio file from a file-like object using librosa
    
    
    waveform, _ = librosa.load(io.BytesIO(audio_file.read()), sr=16000)

    # Convert the waveform to a tensor and preprocess it
    input_values = processor(waveform, return_tensors="pt", sampling_rate=16000).input_values

    # Run the model to get logits and decode to text
    with torch.no_grad():  # Disables gradient calculation, speeding up the process
        logits = model(input_values).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)[0]

    # Convert the transcribed text to phonemes using eSpeak
    audio_phonemes = text_to_phonemes(transcription)
    
    return audio_phonemes

# Function to compare phoneme strings
def compare_phonemes(audio_file, text:str) -> bool:
    answer = audio_to_phonemes(audio_file)==text_to_phonemes(text)
    print(answer)
    return (answer)

# # Example Usage
# if __name__ == "__main__":
#     # Load Wav2Vec2 model and processor
    

#     # Example text and audio file
#     example_text = "the quick brown fox jumps over the lazy dog"
#     audio_file_path = "WhatsApp Audio 2024-08-12 at 3.38.46 PM (online-audio-converter.com).wav"  # Ensure this path points to a WAV file

#     try:
#         # Convert text to phonemes
#         text_phonemes = text_to_phonemes(example_text)
#         print("Text Phonemes:", text_phonemes)

#         # Convert audio to phonemes
#         audio_phonemes = audio_to_phonemes(audio_file_path, model, processor)
#         print("Audio Phonemes:", audio_phonemes)

#         # Compare phonemes
#         match = compare_phonemes(text_phonemes, audio_phonemes)
#         if match:
#             print("The phoneme strings match.")
#         else:
#             print("The phoneme strings do not match.")
#     except RuntimeError as e:
#         print(f"Error: {e}")
