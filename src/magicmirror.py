# Libraries
import os
import re
import cv2
import time
import argparse
import numpy as np
from termcolor import cprint

# File Imports
import utils
import speech_utils
import vision_utils

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

        if fullscreen:
            cv2.namedWindow("Magic Mirror", cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty("Magic Mirror",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
        else:
            cv2.namedWindow("Magic Mirror", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Magic Mirror", 1280,720)

        known_faces_path = os.path.join(os.path.abspath('..'), 'data/known_faces')
        self.known_faces = vision_utils.load_known_faces(known_faces_path)
        self.box_colours = dict(zip(self.known_faces.keys(), utils.pretty_colours(len(self.known_faces.keys()))))

        self.speech = speech_utils.MagicMirrorSpeech(self)

        self.display_text = ''
        self.frame_count = 0

        while(True):
            ret, frame = self.video_cap.read()
            self.process_frame(frame)
            self.frame_count += 1
            
            # Reset the mode to ready after 20 seconds
            # if (time.time() - self.time_last_changed_mode) > reset_mode_time:
            #     if not self.mode is 'READY':
            #         self.change_mode('READY')

    # def change_mode(self, new_mode):
    #     assert(new_mode in self.available_modes)
    #     if self.mode != new_mode:
    #         print("Changing mode from {} to {}".format(self.mode, 'READY'))
    #         self.time_last_changed_mode = time.time()
    #         self.mode = new_mode

    def process_frame(self, image):
        # print(image.shape)

        # Recognize faces every 3 frames
        if self.frame_count % 4 == 0:
            self.detected_faces = vision_utils.get_faces_in_frame(image, self.known_faces.keys(), self.known_faces.values())

        display_frame = image.copy()
        display_frame = vision_utils.draw_faces_on_frame(display_frame, self.detected_faces, self.box_colours)
        display_frame = vision_utils.draw_overlay(self.mode, display_frame)

        font = cv2.FONT_HERSHEY_DUPLEX
        h, w, c = display_frame.shape
        cv2.rectangle(display_frame,(0,h-100),(w,h),(0,0,0),-1)
        cv2.putText(display_frame, self.display_text, (50,h - 50), font, 0.8, (255, 255, 255), 2)        
        
        # if self.debug:
        #     cv2.putText(display_frame, self.mode, (50,50), font, 0.8, (255, 255, 255), 1)

        # Display the image on the screen
        cv2.imshow('Magic Mirror', display_frame)
        key_pressed = cv2.waitKey(1)

        # Exit if spacebar pressed
        if key_pressed == ord(' '):
            print('Exiting')
            cv2.destroyAllWindows()
            exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Magic Mirror Parameters')
    parser.add_argument("--debug", required=False)
    parser.add_argument("--fullscreen", required=False)
    args = parser.parse_args()
    debug_enabled = (args.debug is not None)
    fullscreen_enabled = (args.fullscreen is not None)

    if debug_enabled:
        print('Debug Enabled')

    mm = MagicMirror(fullscreen = fullscreen_enabled, debug = debug_enabled)