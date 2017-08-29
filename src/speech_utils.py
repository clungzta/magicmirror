import os
import time
import tempfile
from gtts import gTTS
from utils import run_async
from termcolor import cprint
from collections import deque
from playsound import playsound
from transcribe_streaming_mic import transcribe_speech

SOUND_PATH = os.path.join(os.path.abspath('..'), 'data/sounds')

def spotify(**kwargs):
    print('playing some music from the {} playlist'.format(kwargs.get('playlist')))

class SpeechTaskParameter():
    def __init__(self, name, question, failed_response='Sorry, I could not understand that'):
        self.name = name
        self.question = question
        self._value = None

    def set_value(self, value):
        self._value = value

    def get_value(self):
        return self._value

#TODO: Speech tasks could maybe inherit from this???
class SpeechTask():
    def __init__(self, name, activation_keywords, function, required_parameters=[], optional_parameters=[]):
        self.name = name
        self.activation_keywords = activation_keywords
        self.task_active = False

        assert callable(function)
        self._function = function

        for param in required_parameters:
            assert isinstance(param, SpeechTaskParameter)

        for param in optional_parameters:
            assert isinstance(param, SpeechTaskParameter)

        self.required_parameters = required_parameters
        self.optional_parameters = optional_parameters

        self._parameters = {}

    # TODO: poll task state at every loop
    def run(self, speech_io_instance):
        self.task_active = True

        print('Running task: {}'.format(self.name))

        # Ask Questions
        for parameter in self.required_parameters:
            cprint(parameter.question, 'magenta')
            speech_io_instance.ask_question(speech_io_instance, parameter.question, parameter.name)
        
    def poll_parameters(self):

        for parameter in self.required_parameters:
            if not parameter.name in self._parameters.keys():
                print('parameter: {}, not available'.format(''))
                return 

        # All parameters present
        # Sp, the function with obtained parameters
        self._function(**self._parameters())
        self.task_active = False
    
    def transcription_callback(self, text, param):
        print('PARAMETER: {}'.format(text), 'yellow')
        
        # Set the parameter
        self._parameters[param['name']] = text   
        
        # Poll all set parameters
        self.poll_parameters()

    def ask_question(self, speech_io_instance, callback_param):

        speech_io_instance.ask_question(callback=transcription_callback, callback_param=callback_param)

    # def get_parameter_values_dict(self):
    #     parameters = {}
        
    #     for parameter in self.required_parameters:
    #         parameters[parameter.name] = parameter.get_value()

    #     for parameter in self.optional_parameters:
    #         parameters[parameter.name] = parameter.get_value()

    #     return parameters

class SpeechTasks():
    def __init__(self, **kwargs):
        for k, speech_task in kwargs.items():
            if not isinstance(speech_task, SpeechTask):
                raise ValueError('kwarg {} is not an instance of SpeechTask')

        self.speech_tasks = kwargs.values()

    def is_speech_task(self, sentence):
        '''

        Exhaustive search over activation keywords in ALL speech_tasks

        '''
        for word1 in list(set(sentence.split())):
            for task in self.speech_tasks:
                for word2 in task.activation_keywords:
                    if word1.lower() == word2.lower():
                        return task

class Conversation():
    def __init__(self, person_id):
        self.start_time = int(round(time.time() * 1000))
        self.person_id = person_id
        self._dialogue_list = []

    def process_sentence(self, sentence, is_computer_speaking):
        self._dialogue_list.append((is_computer_speaking, sentence))

    def get_dialogue(self):
        return self._dialogue_list

class MagicMirrorSpeech():

    def __init__(self, master):
        '''

        @master must be an instance of MagicMirror

        '''
        self.master = master
        self.speech_transcription = transcribe_speech(self.speech_transcription_callback, exit_on_response=False)

        self.mode = 'READY'
        self.available_modes = ['READY', 'SPEAKING', 'LISTENING']

        self.conversations = []
        self.conversation_active = True
        
        #FIXME: maybe import from another python file???
        self.speech_tasks = SpeechTasks( 
                            spotify=SpeechTask(
                                'spotify',
                                ['spotify'],
                                function=spotify,
                                required_parameters=[
                                    SpeechTaskParameter('playlist', 'Which playlist would you like to listen to?')
                                ]
                            )
                        )
        self.active_task = None

        self.question_callback = None

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
    def ask_question(self, text, callback=None, callback_param=None):
        self.change_mode('SPEAKING')
        self._say(text)
        # self.start_listening_tone()
        self.change_mode('LISTENING')
        self.question_callback = callback
        self.callback_param = callback_param

    def speech_transcription_callback(self, response_text, is_final):
        stdout_colour = 'green' if is_final else 'blue'
        cprint(response_text, stdout_colour)

        if self.mode != 'SPEAKING':
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
                    
                    self.conversations.append(Conversation(name.lower()))
                    self.ask_question('Hi {}. How can I help?'.format(name))
                    self.conversations.append(Conversation(name))
                    break                            
                else:
                    self.conversations.append(Conversation(None))                    
                    self.ask_question('Hi. How can I help?')

                self.conversation_active = True

        elif self.mode == 'LISTENING':

            if callable(self.question_callback):
                self.question_callback(response_text, param=callback_param)
                self.question_callback = None
                self.change_mode('READY')                
                return

            # ACTIVATE TASKS
            # First, check whether a task is currently running
            if self.active_task:
                print("Task currently running: {}".format(self.active_task.name))
            else:
                # Check for task activation keywords (e.g. 'weather')
                task = self.speech_tasks.is_speech_task(response_text)

                # If activation keywords present...
                if task is not None:
                    # Run the task
                    self.active_task = task 
                    task.run(self)

            # Our question that we are listening too has been answered
            # So revert state back from LISTENING to READY
            self.conversation_active = False
            self.active_task = None
            self.change_mode('READY')

    def change_mode(self, new_mode):
        assert(new_mode in self.available_modes)
        if self.mode != new_mode:
            print("Speech Changing mode from {} to {}".format(self.mode, new_mode))
            self.time_last_changed_mode = time.time()
            self.mode = new_mode

if __name__ == '__main__':
    say_text('Hello World.')