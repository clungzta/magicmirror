"use strict";
var speech_state = 'waiting_for_activation'
var activation_words = ["magic", "mirror", "wall"]

var recognizing = false;
var connection_established = false;
var restart_enabled = true;
var start_timestamp;

var attempting_to_connect = false;
var retryCount=0;
var timerID=0;
var ws;

var apiai_client;
function apiaiInit() {
    var options = {accessToken: 'd700d2f861f3428e994fa7d4a094efb1',
    //   sessionId: 
    }

apiai_client = new ApiAi.ApiAiClient(options);
}


function change_speech_state(new_state) {
    var valid_states = ['waiting_for_activation', 'listening', 'processing_input', 'speaking']
    
    // Ensure that the new state is valid
    if (valid_states.indexOf(new_state) != -1) {
        console.log('Changing speech state from ' + window.speech_state + ' to ' + new_state);
        window.speech_state = new_state; 
    }
    else {
        throw 'Speech state not valid';
    }
}

function sayText(text, response_expected=false) {
    stopListening();
    
    var msg = new SpeechSynthesisUtterance();
    msg.voice = window.speechSynthesis.getVoices()[10]; // Note: some voices don't support altering params
    msg.voiceURI = 'native';
    msg.volume = 1; // 0 to 1
    msg.rate = 0.90; // 0.1 to 10
    msg.pitch = 1; //0 to 2
    msg.text = text;
    msg.lang = 'en-AU';
    
    msg.onend = function(event) {
        if (response_expected) {
            change_speech_state('listening');
            beginListening(null, false);
        }
        else {
            change_speech_state('waiting_for_activation');
            beginListening(null, true);                    
        }
    };
    
    change_speech_state('speaking');
    addNotification(text, 'warning', false)            
    window.speechSynthesis.speak(msg);
}


function initWebSocket(uri) {
    
    console.log('Initializing websocket')
    
    if (!attempting_to_connect) {
        attempting_to_connect = true;
        addNotification('<strong>Connecting</strong> to server...', 'alert')
    }
    
    if (!("WebSocket" in window)) {
        alert("WebSocket NOT supported by your Browser!");
    }
    
    // Let us open a web socket
    ws = new WebSocket(uri);
    
    ws.onopen = function()
    {
        // Web Socket is connected
        connection_established = true;      
        restart_enabled = true;        
        console.log('Websocket connection opened')
        
        // we are no longer attempting, we are connected...
        attempting_to_connect = false;        
        
        // Reset the retry timer
        if(window.timerID){ /* a setInterval has been fired */
            window.clearInterval(window.timerID);
            window.timerID=0;
            window.retryCount=0;
        }
        
        addNotification('<strong>Connected!</strong>', 'success')        
    };
    
    ws.onmessage = function (evt) 
    { 
        var received_msg = evt.data;
        console.log(received_msg);
    };
    
    ws.onerror = function()
    {
        // addNotification('<strong>Connection error</strong>', 'error', killer=false)
        console.log('websocket connection error')
    };
    
    ws.onclose = function()
    { 
        // addNotification('<strong>Connection ended</strong>', 'error')
        // websocket is closed.
        console.log("Connection is closed...");
        
        // Auto-Retry connection
        // if(!window.timerID && window.retryCount<3){ /* Avoid firing a new setInterval, after one has been done */
        //     window.timerID=setInterval(function(){initWebSocket(uri)}, 5000);
        // }
        
        connection_established = false;        
        
        // We do not want to re-initialize the speech on shutdown
        // restart_enabled = false;
        start_img.src = 'https://github.com/GoogleChrome/webplatform-samples/raw/master/webspeechdemo/mic.gif';        
    };
    
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
        start_img.src = 'https://github.com/GoogleChrome/webplatform-samples/raw/master/webspeechdemo/mic-animate.gif';
    };
    
    recognition.onerror = function(event) {
        if (event.error == 'no-speech' || event.error == 'audio-capture') {
      start_img.src = 'https://github.com/GoogleChrome/webplatform-samples/raw/master/webspeechdemo/mic.gif';
    }
    if (event.error !== 'no-speech') {
        console.log('SPEECH ERROR: ', event.error)
    }
  };

  recognition.onend = function() {
    // console.log('Recognition Restarting')

    // Auto Restart on end (e.g. timeout)
    if (restart_enabled) {
        recognition.start()
    }

    recognizing = false;
    start_img.src = 'https://github.com/GoogleChrome/webplatform-samples/raw/master/webspeechdemo/mic.gif';
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
                    addNotification('<strong>Magic Mirror on the wall!</strong>', 'info', false)
                    sayText('Hey Alex, How can I help?', true)
                }
            }

            // If we are expecting the user to say something
            // and the hotword was previously activated
            else if (window.speech_state == 'listening') {
                change_speech_state('processing_input')                       
                addNotification(transcript, 'info', false)
                const promise = apiai_client.textRequest(transcript);
                
                promise.then(function (resp) {
                    console.log(resp);
                    var result = resp['result']
                    var continuing = (!result['actionIncomplete'])
                    var speech_text = result['fulfillment']['speech']

                    if (speech_text) {
                        sayText(speech_text, continuing)
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
    if (recognizing) {
        restart_enabled = false;
        recognition.stop();
        return;
    }
};

function beginListening(event, restart_on_timeout=false) {
  // Google speech API has a timeout 
  // If listening continuously: restart in the onend callback (when the timeout occurs)
  restart_enabled = restart_on_timeout;  
  
  if (recognizing) {
    restart_enabled = false;
    recognition.stop();
    return;
  }

  recognition.lang = 'en-AU';
  recognition.start();

  start_img.src = 'https://github.com/GoogleChrome/webplatform-samples/raw/master/webspeechdemo/mic-slash.gif';
}

apiaiInit();
beginListening(null, true);