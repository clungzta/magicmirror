# Libraries
import os
import re
import cv2
import zmq
import time
import numpy as np
import pprint as pp
import vision_utils
from termcolor import cprint
from collections import deque
from zmq_utils import send_array, recv_array, get_uri

class MagicMirrorCameraHandler(object):
    def __init__(self, debug=False, ip='0.0.0.0'):
        
        self.debug = debug

        # Choose the webcam with the highest device ID
        devices = vision_utils.list_video_devices()
        device = devices[-1]
        
        print('Initializing Magic Mirror on {}'.format(device))
        device_num = int(re.findall('\d+', device)[0])

        self.video_cap = cv2.VideoCapture(device_num)
        self.video_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.video_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.zcontext = zmq.Context()
        
        # Output gets sent to tornado websocket bridge (on port 6700)
        # self.uri_output = get_uri(ip, 6700)
        # self.output_socket = self.zcontext.socket(zmq.PUB)
        # self.output_socket.bind(self.uri_output)

        # Images get sent to the image processor (to perform face recognition etc.) (on port 6710)
        self.uri_image = get_uri(ip, 6710)
        self.image_socket = self.zcontext.socket(zmq.PUB)
        print('Camera handler iamge socket binding to: {}'.format(self.uri_image))
        self.image_socket.bind(self.uri_image)

        self.frame_history = deque(maxlen=100)
        
        self.frame_count = 0 

    def __del__(self):
        self.video_cap.release()
    
    def get_frame(self):
        success, image = self.video_cap.read()
        
        if success:
            self.frame_count += 1
            image = cv2.flip(image.copy(), 1)
            self.frame_history.append(image.copy())

            # Process (face and emotion recognition) every 8 frames
            if self.frame_count % 8 == 0:
                send_array(self.image_socket, image)

            # recent_frames = list(self.frame_history)[-5:]
            # print(len(recent_frames))
            
            # if len(recent_frames) == 5:
            #     display_image = cv2.fastNlMeansDenoisingMulti(recent_frames, 4, 5, None, 4, 7, 35)
            # else:
            #     display_image = image

            display_image = image.copy()

            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 5]
            ret, jpeg = cv2.imencode('.jpg', display_image)
            return jpeg.tobytes()