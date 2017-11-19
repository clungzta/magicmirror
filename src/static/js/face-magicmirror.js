// grab the canvas_face and context
var canvas_face = document.getElementById('face_canvas');
var ctx_face = canvas_face.getContext('2d');

var loopCount = 0;
var eyeCenter = 75;
var shiftRange = 35;
var eyeSize = 40;

var leftEyeCenterX = eyeCenter;
var rightEyeCenterX = canvas_face.width - eyeCenter;

xShift = getRandomInt(0, shiftRange)
var leftEyeX = leftEyeCenterX + xShift;
var rightEyeY = rightEyeCenterX + xShift;

function getRandomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function clearTheCanvas(){
    ctx_face.clearRect(0, 0, canvas_face.width, canvas_face.height);
}

function roundRect(ctx, x, y, width, height, radius, fill, stroke) {
    if (typeof stroke == 'undefined') {
        stroke = true;
    }
    if (typeof radius === 'undefined') {
        radius = 5;
    }
    if (typeof radius === 'number') {
        radius = { tl: radius, tr: radius, br: radius, bl: radius };
    } else {
        var defaultRadius = { tl: 0, tr: 0, br: 0, bl: 0 };
        for (var side in defaultRadius) {
            radius[side] = radius[side] || defaultRadius[side];
        }
    }
    ctx.beginPath();
    ctx.moveTo(x + radius.tl, y);
    ctx.lineTo(x + width - radius.tr, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius.tr);
    ctx.lineTo(x + width, y + height - radius.br);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius.br, y + height);
    ctx.lineTo(x + radius.bl, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius.bl);
    ctx.lineTo(x, y + radius.tl);
    ctx.quadraticCurveTo(x, y, x + radius.tl, y);
    ctx.closePath();
    if (fill) {
        ctx.fill();
    }
    if (stroke) {
        ctx.stroke();
    }

}

function drawEye(x, y, eyeSize, pupilShiftX, pupilShiftY, isBlinking){
    if (isBlinking)
    {
        rec_width = eyeSize 
        rec_height = Math.PI 
    }
    else {
        rec_width = eyeSize
        rec_height = 0         
    }

    ctx_face.beginPath();
    ctx_face.arc(x, y+20, rec_width,rec_height, 2*Math.PI);
    ctx_face.fillStyle = "white"; 
    ctx_face.fill();

    ctx_face.beginPath();
    ctx_face.arc(x + pupilShiftX, y + 20 + pupilShiftY, 10,0, 2*Math.PI);
    ctx_face.fillStyle = "black"; 
    // ctx_face.fillStyle = "rgba(0, 0, 0, 1.0)";    
    ctx_face.fill();

}

function animate() {
    
    
    // clear the canvas_face, so we can redraw everything in their new positions
    clearTheCanvas();

    // BEGIN DRAWING
    
    // SET canvas_face BACKGROUND COLOUR
    ctx_face.fillStyle = "rgba(108, 122, 137, .8)";
    ctx_face.fillRect(0, 0, canvas_face.width, canvas_face.height);

    // Every 180 updates: blink
    if (loopCount % 120 == 0) {
        var isBlinking = true;
    }
    else {
        var isBlinking = false;
    }

    // every 60 updates: move the eyes
    if (loopCount % 60 == 0) {
        // Generate a random integer to shift the eyes from the centre
        xShift = getRandomInt(-shiftRange, shiftRange)
        yShift = getRandomInt(-shiftRange, shiftRange)
        leftEyeX = leftEyeCenterX + xShift;
        rightEyeX = rightEyeCenterX + xShift;
    } 

    // DRAW FACE FEATURES
    // left eye
    drawEye(leftEyeX, 50, eyeSize, Math.round(xShift / 3.0), Math.round(yShift / 5.0), isBlinking);

    // right eye
    drawEye(rightEyeX, 50, eyeSize, Math.round(xShift / 3.0), Math.round(yShift / 5.0), isBlinking);
    
    
    // Mouth
    // ctx_face.strokeStyle = "rgb(255, 0, 0)";
    ctx_face.fillStyle = "rgba(255, 255, 255, .5)";
    roundRect(ctx_face, 10, 170, 220, 70, 25, true);
    ctx_face.fillStyle = "rgba(44, 62, 80, .5)";
    roundRect(ctx_face, 20, 180, 200, 50, 25, true);
    
    // Nose
    ctx_face.fillStyle = "rgba(255, 255, 255, .5)";    
    ctx_face.arc(Math.round(canvas_face.width / 2.0), Math.round(canvas_face.width / 2.0), 10, 0, 2 * Math.PI);    
    ctx_face.fill();

    // Teeth
    ctx_face.fillStyle = "rgba(52, 73, 94, .5)";    
    for (var i=0; i<180; i+=33) {

        roundRect(ctx_face, 30 + i, 190, 15, 30, 1, true);        
    }

    loopCount++;
    // redraw in 30 milliseconds (0.03 seconds)
    setTimeout(animate, 30);
}

// call the animate function manually for the first time
animate();