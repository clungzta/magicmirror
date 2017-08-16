import os
import cv2
import time
import argparse
import numpy as np

# File Imports
import utils
import speech_utils
import vision_utils

class MagicMirror:
    def __init__(self, debug=False):
        print('Initializing Magic Mirror...')

        self.debug = debug
        self.mode = 'READY'
        self.available_modes = ['READY', 'WEATHER', 'CALENDAR', 'TRAFFIC', 'NEWS', 'QUESTION']
        
        reset_mode_time = 20
        self.time_last_changed_mode = time.time()

        greeting_timer = 10
        self.last_greeting_time = time.time() - greeting_timer

        self.video_cap = cv2.VideoCapture(0)

        self.video_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.video_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        cv2.namedWindow("Magic Mirror", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Magic Mirror",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)

        known_faces_path = os.path.join(os.path.abspath('..'), 'data/known_faces')
        self.known_faces = vision_utils.load_known_faces(known_faces_path)
        self.box_colours = dict(zip(self.known_faces.keys(), utils.pretty_colours(len(self.known_faces.keys()))))
        
        self.count = 0

        if self.debug:
            self.change_mode('CALENDAR')

        while(True):
            ret, frame = self.video_cap.read()
            self.process_frame(frame)
            self.count += 1
            
            # Reset the mode to ready after 20 seconds
            if (time.time() - self.time_last_changed_mode) > reset_mode_time:
                self.change_mode('READY')

    def change_mode(self, new_mode):
        assert(new_mode in self.available_modes)
        print("Changing mode from {} to {}".format(self.mode, 'READY'))
        self.time_last_changed_mode = time.time()
        self.mode = new_mode

    def process_frame(self, image):
        print(image.shape)

        # Recognize faces every 3 frames
        if self.count % 4 == 0:
            self.detected_faces = vision_utils.get_faces_in_frame(image, self.known_faces.keys(), self.known_faces.values())

            if any(self.detected_faces):
                if time.time() - self.last_greeting_time > 10:
                    speech_utils.say_text('Hello {}, how are you today'.format(self.detected_faces[0][1]))
                    self.last_greeting_time = time.time()

        self.display_frame = image.copy()
        self.display_frame = vision_utils.draw_faces_on_frame(self.display_frame, self.detected_faces, self.box_colours)
        self.display_frame = vision_utils.draw_overlay(self.mode, self.display_frame)

        font = cv2.FONT_HERSHEY_DUPLEX
        
        if self.debug:
            cv2.putText(self.display_frame, self.mode, (50,50), font, 0.8, (255, 255, 255), 1)

        # Display the image on the screen
        cv2.imshow('Magic Mirror', self.display_frame)
        key_pressed = cv2.waitKey(1)

        # Exit if spacebar pressed
        if key_pressed == ord(' '):
            print('Exiting')
            cv2.destroyAllWindows()
            exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Magic Mirror Parameters')
    parser.add_argument("--debug", required=False)
    args = parser.parse_args()
    debug_enabled = (args.debug is not None)

    if debug_enabled:
        print('Debug Enabled')

    mm = MagicMirror(debug = debug_enabled)