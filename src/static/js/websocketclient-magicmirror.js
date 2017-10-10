var detectedPeople = {}
var attempting_to_connect = false;
var retryCount=0;
var timerID=0;

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
        auto_restart_enabled = true;        
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

        detectedPeople = JSON.parse(received_msg);
        console.log(detectedPeople);
    };
    
    ws.onerror = function()
    {
        // addNotification('<strong>Connection error</strong>', 'error', killer=false)
        console.log('websocket connection error')
    };
    
    ws.onclose = function()
    { 
        addNotification('<strong>Connection ended</strong>', 'error')
        // websocket is closed.
        console.log("Connection is closed...");
        connection_established = false;        
        
        // Auto-Retry connection
        if(!window.timerID && window.retryCount<10){
            window.timerID=setInterval(function(){initWebSocket(uri)}, 5000);
        }
        
    };
    
}