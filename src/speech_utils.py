import os
import tempfile
from gtts import gTTS
from playsound import playsound

def say_text(text):
    tts = gTTS(text=text, lang='en')
    tts.save('speech.mp3')
    playsound('speech.mp3')
    os.remove('speech.mp3')

say_text('Hello Alex, how are you today?')