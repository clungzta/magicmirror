import os
import time
import tempfile
from gtts import gTTS
from utils import run_async
from termcolor import cprint
from playsound import playsound
from transcribe_streaming_mic import transcribe_speech

SOUND_PATH = os.path.join(os.path.abspath('..'), 'data/sounds')

class MagicMirrorSpeech():

    def __init__(self, master):
        '''

        @master must be an instance of MagicMirror

        '''
        self.master = master
        self.speech_transcription = transcribe_speech(self.speech_transcription_callback, exit_on_response=False)

        self.mode = 'READY'
        self.available_modes = ['READY', 'SPEAKING', 'LISTENING']

    def start_listening_tone(self):
        playsound(os.path.join(SOUND_PATH, 'up_and_high_beep.mp3'))

    def couldnt_understand_tone(self):
        playsound(os.path.join(SOUND_PATH, 'layered_low_beep.mp3'))

    def _say(self, text):
        print('SAYING: "{}"'.format(text))
        tts = gTTS(text=text, lang='en')
        tts.save('speech.mp3')
        playsound('speech.mp3')
        os.remove('speech.mp3')

    @run_async
    def say_text(self, text):
        self.change_mode('SPEAKING')
        self._say(text)
        self.change_mode('READY')

    @run_async
    def ask_question(self, text):
        self.change_mode('SPEAKING')
        self._say(text)
        # self.start_listening_tone()
        self.change_mode('LISTENING')

    def speech_transcription_callback(self, response_text, is_final):
        stdout_colour = 'green' if is_final else 'blue'
        cprint(response_text, stdout_colour)

        if not self.mode == 'SPEAKING':
            # NOTE: We do NOT want to listen while in the SPEAKING state
            self.master.display_text = response_text.capitalize()

        if not is_final:
            return

        if self.mode == 'READY':
            # Wait for the initial 'magic mirror on the wall' triggering call
            if any(word in response_text for word in ['mirror', 'wall']):
                det_faces_cache = self.master.get_detected_faces_cache()
                
                for name in (det_faces_cache):
                    if name.lower() == "unknown":
                        continue
                    
                    self.ask_question('Hi {}. How can I help?'.format(name))
                    break                            
                else:
                    self.ask_question('Hi. How can I help?')

        elif self.mode == 'LISTENING':

            ### DO NLP PROCESSING STUFF HERE
            
            # Our question that we are listening too has been answered
            # So revert state back from LISTENING to READY
            self.change_mode('READY')

    def change_mode(self, new_mode):
        assert(new_mode in self.available_modes)
        if self.mode != new_mode:
            print("Speech Changing mode from {} to {}".format(self.mode, new_mode))
            self.time_last_changed_mode = time.time()
            self.mode = new_mode

if __name__ == '__main__':
    say_text('Hi Alex.')