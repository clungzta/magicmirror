# __future__ imports
from __future__ import print_function

# Libraries
import os
import re
import cv2
import time
import argparse
import numpy as np
import subprocess as sp
from termcolor import cprint
# from collections import deque
from expiringdict import ExpiringDict
# from flask import Flask, render_template, Response

# File Imports
import utils
import speech_utils
import vision_utils

# app = Flask(__name__)

# command = [ '/usr/bin/ffmpeg',
#         '-y', # (optional) overwrite output file if it exists
#         '-f', 'rawvideo',
#         '-vcodec','rawvideo',
#         '-s', '1920x1080', # size of one frame
#         '-pix_fmt', 'rgb24',
#         '-r', '24', # frames per second
#         '-i', '-', # The imput comes from a pipe
#         '-an', # Tells FFMPEG not to expect any audio
#         '-vcodec', 'mjpeg',
#         '/home/alex/my_output_videofile.mp4' ]

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
    def __init__(self, fullscreen=True, debug=False):
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

        self.speech = speech_utils.MagicMirrorSpeech(self)

        self.display_text = ''
        self.frame_count = 0

        # self.http_bytes =

    # def change_mode(self, new_mode):
    #     assert(new_mode in self.available_modes)
    #     if self.mode != new_mode:
    #         print("Changing mode from {} to {}".format(self.mode, 'READY'))
    #         self.time_last_changed_mode = time.time()
    #         self.mode = new_mode

    def run(self):
        while(True):
            ret, frame = self.video_cap.read()
            disp = self.process_frame(frame)
            self.frame_count += 1
            print(self.frame_count, end=' ')
            # ret, jpeg = cv2.imencode('.jpg', frame)
            try:
                ffmpeg_pipe.stdin.write(cv2.cvtColor(disp, cv2.COLOR_BGR2RGB).tostring())
            except Exception as e:
                print(e)
            # print(ffmpeg_pipe.stderr.read())

            # while True:
            #     inline = ffmpeg_pipe.stderr.readline()
            #     if not inline:
            #         break
            #     print(inline.strip())

            # self.http_deque.append(b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
            
            # Reset the mode to ready after 20 seconds
            # if (time.time() - self.time_last_changed_mode) > reset_mode_time:
            #     if not self.mode is 'READY':
            #         self.change_mode('READY')


    def process_frame(self, image):
        # print(image.shape)

        # Recognize faces every 6 frames
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
            cv2.putText(display_frame, self.speech.mode, (w-300,h-50), font, 1.5, (0, 0, 255), 2)
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

        return display_frame

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
    mm.run()

    if debug_enabled:
        print('Debug Enabled')

    # @app.route('/video_feed')
    # def video_feed():
    #     return Response(mm.http_deque[0], mimetype='multipart/x-mixed-replace; boundary=frame')

    # app.run(host='0.0.0.0', debug=True, port=9090)