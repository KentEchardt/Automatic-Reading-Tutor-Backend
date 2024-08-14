import torch
import librosa
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import subprocess

# Function to check if espeak is installed
def check_espeak():
    return subprocess.run(["espeak-ng", "--version"], capture_output=True, text=True).returncode == 0

# Function to convert text to phonemes using eSpeak
def text_to_phonemes(text: str, language: str = "en") -> str:
    if not check_espeak():
        raise RuntimeError("eSpeak is not installed or not in PATH.")
    
    command = f'espeak-ng -v{language} -x "{text}"'
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, _ = process.communicate()
    phonemes = output.decode("utf-8").strip()
    return phonemes

# Function to convert audio file to text using Wav2Vec and then to phonemes using eSpeak
def audio_to_phonemes(audio_path: str, model, processor) -> str:
    try:
        # Load the audio file using librosa
        waveform, sample_rate = librosa.load(audio_path, sr=16000)
    except Exception as e:
        raise RuntimeError(f"Failed to load audio file: {e}")

    # Convert the waveform to a tensor
    waveform = torch.tensor(waveform).unsqueeze(0)  # Add a batch dimension

    # Preprocess the waveform and run it through the model
    input_values = processor(waveform.squeeze(), return_tensors="pt", sampling_rate=16000).input_values
    logits = model(input_values).logits
    predicted_ids = torch.argmax(logits, dim=-1)

    # Decode the predicted IDs to text
    transcription = processor.batch_decode(predicted_ids)[0]

    # Convert the transcribed text to phonemes using eSpeak
    audio_phonemes = text_to_phonemes(transcription)
    
    return audio_phonemes

# Function to compare phoneme strings
def compare_phonemes(phonemes1: str, phonemes2: str) -> bool:
    return phonemes1 == phonemes2

# Example Usage
if __name__ == "__main__":
    # Load Wav2Vec2 model and processor
    model_name = "facebook/wav2vec2-large-960h-lv60-self"
    model = Wav2Vec2ForCTC.from_pretrained(model_name)
    processor = Wav2Vec2Processor.from_pretrained(model_name)

    # Example text and audio file
    example_text = "the quick brown fox jumps over the lazy dog"
    audio_file_path = "WhatsApp Audio 2024-08-12 at 3.38.46 PM (online-audio-converter.com).wav"  # Make sure this path points to a WAV file

    try:
        # Convert text to phonemes
        text_phonemes = text_to_phonemes(example_text)
        print("Text Phonemes:", text_phonemes)

        # Convert audio to phonemes
        audio_phonemes = audio_to_phonemes(audio_file_path, model, processor)
        print("Audio Phonemes:", audio_phonemes)

        # Compare phonemes
        match = compare_phonemes(text_phonemes, audio_phonemes)
        if match:
            print("The phoneme strings match.")
        else:
            print("The phoneme strings do not match.")
    except RuntimeError as e:
        print(f"Error: {e}")
