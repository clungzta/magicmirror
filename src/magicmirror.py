# __future__ imports
from __future__ import print_function

# Libraries
import os
import re
import cv2
import zmq
import time
import random
import argparse
import threading
import numpy as np
import pprint as pp
import subprocess as sp
from termcolor import cprint
from datetime import datetime
from expiringdict import ExpiringDict
from zmq_utils import send_array, recv_array, get_uri

# File Imports
import utils
# import speech_utils
import vision_utils

command = [ '/usr/bin/ffmpeg',
        '-y', # (optional) overwrite output file if it exists        
        '-f', 'rawvideo',
        '-vcodec','rawvideo',
        '-s', '1920x1080', # size of one frame
        '-pix_fmt', 'rgb24',
        '-r', '24', # frames per second
        '-i', '-', # The imput comes from a pipe
        '-an', # Tells FFMPEG not to expect any audio
        'http://localhost:8090/monitoring1.ffm' ]

ffmpeg_pipe = sp.Popen( command, stdin=sp.PIPE, stderr=sp.PIPE, stdout=sp.PIPE)

class MagicMirror:
    def __init__(self, fullscreen=True, debug=False, ip='0.0.0.0', ports=[6700, 6701, 6702]):
        devices = vision_utils.list_video_devices()
        device = devices[-1]
        
        print('Initializing Magic Mirror on {}'.format(device))
        device_num = int(re.findall('\d+', device)[0])

        self.debug = debug
        self.mode = 'READY'
        self.available_modes = ['READY']
        
        reset_mode_time = 20
        self.time_last_changed_mode = time.time()

        greeting_timer = 10
        self.last_greeting_time = time.time() - greeting_timer


        self.video_cap = cv2.VideoCapture(device_num)

        self.video_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.video_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        if self.debug:
            if fullscreen:
                cv2.namedWindow("Magic Mirror", cv2.WND_PROP_FULLSCREEN)
                cv2.setWindowProperty("Magic Mirror",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
            else:
                cv2.namedWindow("Magic Mirror", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Magic Mirror", 1280,720)

        known_faces_path = os.path.join(os.path.abspath('..'), 'data/known_faces')
        self.known_faces = vision_utils.load_known_faces(known_faces_path)
        self.box_colours = dict(zip(self.known_faces.keys(), utils.pretty_colours(len(self.known_faces.keys()))))
        self.detected_faces_cache_ = ExpiringDict(max_len=100, max_age_seconds=2.5)

        # self.speech = speech_utils.MagicMirrorSpeech(self)

        self.display_text = ''
        self.frame_count = 0

        self.zcontext = zmq.Context()

        pubsub_uri = get_uri(ip, ports[0])
        reqrep_uri = get_uri(ip, ports[1])
        pushpull_uri = get_uri(ip, ports[2])
        
        utils.start_thread(self.grab_images, pubsub_uri)

    def grab_images(self, url):
        """Grab images from the camera. This could later be replaced with an incoming image stream (from WebRTC for example)"""
        zsock = self.zcontext.socket(zmq.PUB)
        zsock.bind(url)

        cap = cv2.VideoCapture(0)

        while True:
            ret, frame = cap.read()

            if ret:
                send_array(zsock, flipped_frame)

                try:
                    ffmpeg_pipe.stdin.write(cv2.cvtColor(disp, cv2.COLOR_BGR2RGB).tostring())
                    # print(ffmpeg_pipe.stderr.read())
                except Exception as e:
                    print(e)

    def process_image_thread(zcontext, in_url, facerecognition_url, out_url):
        """Process the image stream in this thread."""
        isock = zcontext.socket(zmq.SUB)
        isock.connect(in_url)
        isock.setsockopt(zmq.SUBSCRIBE, '')

        # tsock = zcontext.socket(zmq.REQ)
        # tsock.connect(facerecognition_url)
        
        osock = zcontext.socket(zmq.PUSH)
        osock.connect(out_url)

        while True:
            img = recv_array(isock)
            print(img.shape)

            self.process_frame(img)
            print(self.frame_count, end=' ')

            cv2.imshow('image', img)
            cv2.waitKey(1)

            # tsock.send_json((1))
            # transcription_str = tsock.recv_json()

            # osock.send_string(transcription_str)

    def process_frame(self, image):
        # print(image.shape)
        self.frame_count += 1

        # Perform a horizontal flip transformation to make the image look just like a mirror
        image = cv2.flip(image.copy(), 1)

        # Recognize faces every N frames
        # TODO Add worker processes, rather than process every N frames
        if self.frame_count % 6 == 0:
            self.detected_faces = vision_utils.get_faces_in_frame(image, self.known_faces.keys(), self.known_faces.values())
            
            for face in self.detected_faces:
                bbox_area = abs(face[0][2] - face[0][0]) * abs(face[0][1] - face[0][3])
                self.detected_faces_cache_[face[1]] = (bbox_area)

        display_frame = image.copy()
        display_frame = vision_utils.draw_faces_on_frame(display_frame, self.detected_faces, self.box_colours)
        display_frame = vision_utils.draw_overlay(self.mode, display_frame)

        font = cv2.FONT_HERSHEY_DUPLEX
        h, w, c = display_frame.shape
        cv2.rectangle(display_frame,(0,h-100),(w,h),(0,0,0),-1)
        cv2.putText(display_frame, self.display_text, (50,h - 50), font, 0.8, (255, 255, 255), 2)        
        
        if self.debug:
            # cv2.putText(display_frame, self.speech.mode, (w-300,h-50), font, 1.5, (0, 0, 255), 2)
            print(self.get_detected_faces_cache())

        if self.debug:
            # Display the image in cv2 window
            cv2.imshow('Magic Mirror', display_frame)
            key_pressed = cv2.waitKey(1)

            # Exit if spacebar pressed
            if key_pressed == ord(' '):
                print('Exiting')
                cv2.destroyAllWindows()
                exit()

        # return display_frame

    def get_detected_faces_cache(self):
        names, areas = zip(*sorted(self.detected_faces_cache_.items(), key=lambda x: x[1], reverse=True))
        return names

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Magic Mirror Parameters')
    parser.add_argument("--debug", required=False)
    parser.add_argument("--fullscreen", required=False)
    args = parser.parse_args()
    debug_enabled = (args.debug is not None)
    fullscreen_enabled = (args.fullscreen is not None)
    
    mm = MagicMirror(fullscreen = fullscreen_enabled, debug = debug_enabled)

    if debug_enabled:
        print('Debug Enabled')

    # @app.route('/video_feed')
    # def video_feed():
    #     return Response(mm.http_deque[0], mimetype='multipart/x-mixed-replace; boundary=frame')

    # app.run(host='0.0.0.0', debug=True, port=9090)