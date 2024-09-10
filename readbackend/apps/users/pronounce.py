from lytspel import Converter

#lytspel pronounciation of a word (simple respelling)
def get_phonetic_spelling(text):
    converter = Converter() 
    phonetic_spelling = converter._convert_text_if_simple(text)
    return phonetic_spelling
