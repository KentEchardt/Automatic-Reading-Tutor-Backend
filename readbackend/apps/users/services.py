from .audio_processing import audio_to_phonemes, text_to_phonemes,compare_phonemes

def match_audio_to_text(audio_file, text):
    
    match = compare_phonemes(audio_file,text)
    
    # Simple matching logic, can be improved
    return match