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