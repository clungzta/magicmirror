import os
import time
import tempfile
from gtts import gTTS
from utils import run_async
from termcolor import cprint
from collections import deque
from playsound import playsound
from apiai_client import ApiAIClient
from transcribe_streaming_mic import transcribe_speech

SOUND_PATH = os.path.join(os.path.abspath('..'), 'data/sounds')

class MagicMirrorSpeech():

    def __init__(self):
        self.ai = ApiAIClient('d700d2f861f3428e994fa7d4a094efb1', logging=0)
        self.speech_transcription = transcribe_speech(self.speech_transcription_callback, exit_on_response=False)

        self.available_states = ['READY', 'SPEAKING', 'LISTENING', 'PROCESSING_INPUT']
        self.state = 'READY'

    def start_listening_tone(self):
        playsound(os.path.join(SOUND_PATH, 'up_and_high_beep.mp3'))

    def couldnt_understand_tone(self):
        playsound(os.path.join(SOUND_PATH, 'layered_low_beep.mp3'))

    def _say(self, text):
        self.change_state('SPEAKING')
        cprint('SAYING: "{}"'.format(text), 'grey', 'on_yellow')
        tts = gTTS(text=text, lang='en')
        tts.save('speech.mp3')
        playsound('speech.mp3')
        os.remove('speech.mp3')
        self.change_state('READY')

    @run_async
    def say_text(self, text):
        self._say(text)

    @run_async
    def ask_question(self, text):
        self._say(text)
        self.change_state('LISTENING')

    def speech_transcription_callback(self, utterance_transcription, is_end_of_utterance):
        # We do NOT want to listen while in the SPEAKING state
        if self.state == 'SPEAKING':
            return

        # The person has finished speaking for a little while
        if is_end_of_utterance:
            cprint(utterance_transcription, 'grey', 'on_green')
        else:
            cprint(utterance_transcription, 'blue')
            return

        if self.state == 'READY':
            # Wait for the initial 'magic mirror on the wall' activation call
            if any(word in utterance_transcription for word in ['mirror', 'wall']):
                self.change_state('PROCESSING_INPUT')                    
                
                # Get a list of detected faces from the computer vision handler
                det_faces_cache = ['alex']

                # Only known people will be accepted
                names = filter(lambda a: a != 'unknown', det_faces_cache)

                if names:
                    # The person with the largest bounding box is chosen (presumably closest to the mirror)
                    name = names[0]
                    cprint('Starting a conversation with {}'.format(name), 'grey', 'on_magenta')        
                    
                    response = self.ai.send_query('Hello Magic Mirror, my name is {}'.format(name))
                    fulfillment_text = response['fulfillment']['speech']
                    print('Action Completed: {}'.format(not(response['actionIncomplete'])))                    
                    self.ask_question(fulfillment_text)

                else:
                    say_text("Sorry, I don't know you yet. I'm not allowed to talk to strangers.")
                    return

        elif self.state == 'LISTENING':
            # We have finished listening to an utterance from the user, lets process what theyve said
            self.change_state('PROCESSING_INPUT')

            response = self.ai.send_query(utterance_transcription)
            fulfillment_text = response['fulfillment']['speech'] 

            print('Response Text: {}'.format(fulfillment_text))
            print('Response Action: {}'.format(response['action']))
            
            try:
                print('Webhook Used: {}'.format(response['metadata']['webhookUsed']))
            except KeyError:
                pass

            print('Action Completed: {}'.format(not(response['actionIncomplete'])))

            if response['actionIncomplete']:
                self.ask_question(fulfillment_text)            
            elif response['action'] == 'input.unknown':
                print("Couldn't understand input, asking again")
                self.ask_question(fulfillment_text)
            else:
                self.say_text(fulfillment_text)    
            
            # We're finished listening here...
            cprint('-------------', 'white', 'on_magenta')
            self.change_state('READY')

    def change_state(self, new_state):
        assert new_state in self.available_states, 'Chosen state "{}" not defined'.format(new_state)
        
        if self.state != new_state:
            cprint("Speech Changing state from {} to {}".format(self.state, new_state), 'grey', 'on_cyan')
            self.state = new_state

if __name__ == '__main__':
    mm_speech = MagicMirrorSpeech()