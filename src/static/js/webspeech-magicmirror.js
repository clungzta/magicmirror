"use strict";
var speech_state = 'waiting_for_activation'
var activation_words = ["magic", "mirror", "wall"]

var utterances = [];
var voice = speechSynthesis.getVoices()[10];

var recognizing = false;
var connection_established = false;
var continous_recognition_enabled = true;
var start_timestamp;

var ws;


var apiai_client;
function apiaiInit() {
    apiai_client = new ApiAi.ApiAiClient({accessToken: 'd700d2f861f3428e994fa7d4a094efb1'});
    console.log('Beginning APIAI session ' + apiai_client.sessionId)
}

function setContextParameters(apiai_client, context_name, parameters, lifespan=15)
{
    var context_data = [{"name": context_name, "lifespan": lifespan, "parameters":  parameters}]
    console.log('posting to apiai ' + apiai_client.sessionId + ' ' + apiai_client.accessToken)
    console.log(context_data)

    $.ajax({
        url: 'https://api.api.ai/v1/contexts?sessionId=' + apiai_client.sessionId,
        headers: {
            'Authorization' : 'Bearer ' + apiai_client.accessToken,
            'Content-type' : 'application/json',
            'Accept' : 'application/json'            
        },
        method: 'POST',
        data: JSON.stringify(context_data),
        success: function(data){
          console.log('success setting context parameters: ' + data);
        },
        error: function(error){
            console.log('error setting context parameters: ');
            console.log(JSON.parse(error.responseText));
        },
        
      });
}

function getUserLocation() {
    $.getJSON('https://ipapi.co/'+$('.ip').val()+'/json', function(data){
        $('.city').text(data.city);
        $('.country').text(data.country);
    });  
}

function change_speech_state(new_state) {
    var valid_states = ['waiting_for_activation', 'listening', 'processing_input', 'speaking']
    
    // Ensure that the new state is valid
    if (valid_states.indexOf(new_state) != -1) {
        console.log('Changing speech state from ' + window.speech_state + ' to ' + new_state);
        window.speech_state = new_state; 
        
        var img_base_url = 'https://github.com/GoogleChrome/webplatform-samples/raw/master/webspeechdemo/'
        start_img.src = img_base_url + ((new_state == 'listening') ? 'mic-animate.gif' : 'mic.gif');
    }
    else {
        throw 'Speech state not valid';
    }
}

function sayText(text, response_expected=false) {
    stopListening();
    change_speech_state('speaking');
    
    console.log('SAYING: "'+ text + '" RESPONSE_EXPECTED: ' + response_expected.toString())

    var utterance = new SpeechSynthesisUtterance();
    utterances.push(utterance);

    // if (!window.voice) {
    //     window.voice = speechSynthesis.getVoices()[10]
    // }

    utterance.voice = window.voice; // Note: some voices don't support altering params
    utterance.voiceURI = 'native';
    utterance.volume = 1; // 0 to 1
    utterance.rate = 0.90; // 0.1 to 10
    utterance.pitch = 1; //0 to 2
    utterance.text = text;
    utterance.lang = 'en-AU';
    
    utterance.onend = function(event) {
        console.log('Finished speaking')

        if (response_expected) {
            change_speech_state('listening');
            beginListening(false);
        }
        else {
            change_speech_state('waiting_for_activation');
            beginListening(true);                    
        }
    };
    
    window.speechSynthesis.speak(utterance);
}

if (!('webkitSpeechRecognition' in window)) {
    alert('Web speech is not supported by this browser')
}

else {
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    
    recognition.onstart = function() {
        recognizing = true;
    };
    
    recognition.onerror = function(event) {
        console.log(event)
        stopListening();    
    };
    
    recognition.onend = function() {
        recognizing = false;
        console.log('Recognition ended')            
        
        if (speech_state == 'waiting_for_activation') {
            // continous recognition when waiting for activation phrase 
            // Auto Restart (on Google speech recognizer timeout)
            recognition.start()
            console.log('Continuing to wait for activation phrase...')
        }
        else if (speech_state == 'listening' || speech_state == 'processing_input') {
            // user input (response to a question) timeout.
            // Lets start listening for the activation
            change_speech_state('waiting_for_activation');
            listenForActivation();
        }          
            
    };

  recognition.onresult = function(event) {
    for (var i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
            var transcript = event.results[i][0].transcript
            
            // Check if more than n activation words (hotwords) have been mentioned 
            var words = transcript.split(" ");
            var num_hotwords = (words.filter((n) => activation_words.includes(n))).length;
            console.log(words, num_hotwords)            

            // If we are waiting to activate the speech...
            if (window.speech_state == 'waiting_for_activation') {
                // If the number of hotwords is greater than two
                // and the total number of words <= 10
                if (num_hotwords >= 2 && words.length <= 10)
                {
                    addNotification('<strong>Magic Mirror on the wall!</strong>', 'success', 10000);
                    
                    // Get the name of the largest bounding box from the detected people
                    var name = getLargestBBOXLabel(detectedPeople);
                    // var name = 'Alex';
                    
                    if (!name || name.toLowerCase() == 'unknown') {
                        // only continue if a name is present
                        console.log('No known person currently present, ignoring...')
                        addNotification("Sorry, I can't see you there", 'error', 10000);
                        sayText("Sorry, I can't see you there.")
                        return;
                    }
                    
                    change_speech_state('processing_input');
                    const promise = apiai_client.textRequest('Hello Magic Mirror, my name is ' + name);
                    
                    promise.then(function (resp) {
                        console.log(resp);
                        var result = resp['result']
                        var speech_text = result['fulfillment']['speech']
                        // Initial user introduction    
                        if (typeof speech_text !== 'undefined') {
                            sayText(speech_text, true)
                            addNotification(speech_text, 'warning', 10000)    
                        }
                        else {
                            change_speech_state('waiting_for_activation');
                            listenForActivation();
                        }
                    });                
                    
                    promise.catch(function (err) {
                        console.log(err);
                    });
                }
            }

            // If we are expecting the user to say something
            // and the hotword was previously activated
            else if (window.speech_state == 'listening') {
                change_speech_state('processing_input')                       
                addNotification(transcript, 'info', 10000)
                const promise = apiai_client.textRequest(transcript);
                
                promise.then(function (resp) {
                    // speech result from api.ai
                    console.log(resp);
                    var result = resp['result']
                    var speech_text = result['fulfillment']['speech']

                    var is_question = (typeof speech_text !== 'undefined' && speech_text.endsWith('?'))
                    var continue_conversation = (result['actionIncomplete'] || is_question)
                    var action = result['action']

                    if (speech_text) {
                        sayText(speech_text, continue_conversation)

                        if (action  !== null)
                        {
                            // Perform an action, e.g. fetch weather from api
                            processAction(result);                        
                        }
                    }
                    else {
                        change_speech_state('waiting_for_activation');
                        listenForActivation();
                    }
                });                
                
                promise.catch(function (err) {
                    console.log(err);
                });
            }

            // ws.send(JSON.stringify({'topic_suffix' : 'SPEECH_INPUT', 'message' : transcript}));
            console.log('%c ' + transcript, 'color: #00ff11')
        }
        else
        {
            console.log(event.results[i][0].transcript)            
        }
    }
  };
}

function stopListening(event) {
    console.log('Stopping recognition')
    // console.log(recognition)

    if (recognizing) {
        continous_recognition_enabled = false;
        recognition.stop();
        return;
    }
};

function beginListening(restart_on_timeout) {
  // Google speech API has a timeout 
  // If listening continuously: restart in the onend callback (when the timeout occurs)
  stopListening();    
  continous_recognition_enabled = restart_on_timeout;

  console.log('Beginning to listen, restart_on_timeout: ' + restart_on_timeout);

  recognition.lang = 'en-AU';
    
  if (!recognizing) recognition.start();
}

function listenForActivation() {
    beginListening(true)
}