import os
import tempfile
from gtts import gTTS
from utils import run_async
from playsound import playsound

# Implement some kind of queuing behavior?
@run_async
def say_text(text):
    tts = gTTS(text=text, lang='en')
    tts.save('speech.mp3')
    playsound('speech.mp3')
    os.remove('speech.mp3')

if __name__ == '__main__':
    say_text('Hello Alex, how are you today?')