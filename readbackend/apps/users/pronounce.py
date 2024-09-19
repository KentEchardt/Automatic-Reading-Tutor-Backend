from lytspel import Converter

#lytspel pronounciation of a word (simple respelling)
def get_phonetic_spelling(text):
    converter = Converter() 
    phonetic_spelling = converter.convert_para(text)
 
    return phonetic_spelling
