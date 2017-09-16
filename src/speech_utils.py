import os
import re
import zmq
import time
import json
import tempfile
import numpy as np
from gtts import gTTS
from zmq_utils import get_uri
from utils import run_async
from termcolor import cprint
from collections import deque
from playsound import playsound
from apiai_client import ApiAIClient
from nltk.metrics import masi_distance, edit_distance
from transcribe_streaming_mic import transcribe_speech

SOUND_PATH = os.path.join(os.path.abspath('..'), 'data/sounds')

def sentence_similarity(query_str, original_str):
    return float(len(set(query_str.lower().split()).intersection(original_str.lower().split()))) / len(query_str)

def weighted_avg_edit_distance(phrase1, phrase2):
    '''

    Custom distance metric for comparing two phrases, developed by Alex.

    Intended for comparing a known phrase with a speech transcription.
    Uses the assumption that AT LEAST one transcribed word is spelled similarly to another in the known phrase.

    Returns a distance value between 0 and 1

    '''

    word_set1 = set(filter(bool, re.split('[^a-zA-Z]', str(phrase1))))
    word_set2 = set(filter(bool, re.split('[^a-zA-Z]', str(phrase2))))

    # Exhaustive search for minumum edit_distance between all words in each string
    word_min_edit_distances = [np.amin([edit_distance(word1, word2) for word2 in list(word_set2)]) for word1 in list(word_set1)]

    # Take weighted average of the min_edit_distance
    # Compute reciprocal so that words with lower distance get a higher weight in the average
    weights = 1.0 / (np.asarray(word_min_edit_distances) + 0.05)
    return np.average(word_min_edit_distances, weights=weights)

    # return np.average(word_min_edit_distances)

class MagicMirrorSpeech():

    def __init__(self):
        self.ai = ApiAIClient('d700d2f861f3428e994fa7d4a094efb1', logging=0)
        self.speech_transcription = transcribe_speech(self.speech_transcription_callback, exit_on_response=False)

        self.available_states = ['READY', 'SPEAKING', 'LISTENING', 'PROCESSING_INPUT']
        self.state = 'READY'

        self.last_speech_output_str = None

        # Socket to subscribe to computer vision handler
        self.zcontext = zmq.Context()
        self.socket_sub = self.zcontext.socket(zmq.SUB)
        self.socket_sub.connect(get_uri('0.0.0.0', 6700))
        self.socket_sub.setsockopt(zmq.CONFLATE, 1)
        self.socket_sub.setsockopt(zmq.SUBSCRIBE, '')

        self.detected_people = {}
        # self.poller = zmq.Poller()
        # self.poller.register(self.socket_sub, zmq.POLLIN)

    def start_listening_tone(self):
        playsound(os.path.join(SOUND_PATH, 'up_and_high_beep.mp3'))

    def couldnt_understand_tone(self):
        playsound(os.path.join(SOUND_PATH, 'layered_low_beep.mp3'))

    def _say(self, text, state_on_finished='READY'):
        self.change_state('SPEAKING')
        cprint('SAYING: "{}"'.format(text), 'grey', 'on_yellow')
        self.last_speech_output_str = text
        if text:
            tts = gTTS(text=text, lang='en')
            tts.save('speech.mp3')
            playsound('speech.mp3')
            os.remove('speech.mp3')
        self.change_state(state_on_finished)

    @run_async
    def say_text(self, text):
        self._say(text)

    @run_async
    def ask_question(self, text):
        self._say(text, state_on_finished='LISTENING')

    def is_activation_catchphrase(self, sentence):
        '''
        Is the sentence an activation catchphrase?
        (i.e. Should we begin listening for further input?)

        '''

        activation_words = ['magic', 'mirror', 'wall']
        
        # Ensure that at least 2 of the activation words have been spoken
        if len(set(sentence.split()).intersection(activation_words)) < 2:
            return False

        # If the sentence is too long, we should ignore it, it is likely a false positive
        if len(sentence.split()) > 10:
            return False

        return True

    def begin_introduction(self, detected_people):
        '''

        Let's begin talking!
        Note: Only known people will be accepted

        '''

        names = filter(lambda a: a != 'unknown', detected_people)

        if names:
            # The person with the largest bounding box is chosen (presumably closest to the mirror)
            name = names[0]
            cprint('Starting a conversation with {}'.format(name), 'grey', 'on_magenta')        
            
            response = self.ai.send_query('Hello Magic Mirror, my name is {}'.format(name))
            fulfillment_text = response['fulfillment']['speech']
            print('Action Completed: {}'.format(not(response['actionIncomplete'])))                    
            self.ask_question(fulfillment_text)

        else:
            self.say_text("Sorry, I don't know you yet. I'm not allowed to talk to strangers.")

    def speech_transcription_callback(self, utterance_transcription, is_end_of_utterance):
        # TODO request from websocket handler
        # res = self.socket.recv()
        # print(res)

        # TODO: Find a better solution to this hack...
        # zmq subscriber stores the entire buffer of messages
        while True:
            try:
                self.detected_people = json.loads(self.socket_sub.recv(zmq.NOBLOCK))
            except zmq.ZMQError as e:
                break
        
        # TODO: Sort by size
        print(self.detected_people.keys())

        # We do NOT want to listen while in the SPEAKING state
        if self.state == 'SPEAKING':
            return

        if is_end_of_utterance:
            # The person has paused their speaking
            cprint(utterance_transcription, 'grey', 'on_green')
        else:
            # The person is still speaking
            cprint(utterance_transcription, 'blue')
            return

        # If waiting for the activation catchphrase
        if self.state == 'READY' and self.is_activation_catchphrase(utterance_transcription):
            self.change_state('PROCESSING_INPUT')        
            self.begin_introduction(self.detected_people.keys())

        elif self.state == 'LISTENING':

            if self.last_speech_output_str:
                dist = weighted_avg_edit_distance(utterance_transcription, self.last_speech_output_str)

                if dist < 0.2:
                    cprint('Overheard speech output, ignoring this utterance... (dist: {:.3f})'.format(dist), 'grey', 'on_red')
                    # return if we have overheard what we have just said
                    return

            # We have finished listening to an utterance from the user, lets process what theyve said
            self.change_state('PROCESSING_INPUT')

            response = self.ai.send_query(utterance_transcription)
            fulfillment_text = response['fulfillment']['speech'] 
            action_completed = not(response['actionIncomplete'])

            print('Response Action: {}, Action Completed: {}'.format(response['action'], action_completed))
            
            try:
                if response['metadata']['webhookUsed']:
                    print('Webhook Used!')
            except KeyError:
                pass

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