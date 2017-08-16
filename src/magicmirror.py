import os
import cv2
import numpy as np

import utils
import speech_utils
import vision_utils

class MagicMirror:
    def __init__(self):
        print('Initializing Magic Mirror...')
        self.video_cap = cv2.VideoCapture(0)

        self.video_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.video_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        cv2.namedWindow("Magic Mirror", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Magic Mirror",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)

        known_faces_path = os.path.join(os.path.abspath('..'), 'data/known_faces')
        self.known_faces = vision_utils.load_known_faces(known_faces_path)
        self.box_colours = dict(zip(self.known_faces.keys(), utils.pretty_colours(len(self.known_faces.keys()))))
        
        self.count = 0

        while(True):
            ret, frame = self.video_cap.read()
            self.process_frame(frame)

    def process_frame(self, image):
        # print(image.shape)

        # Recognize faces every 3 frames
        if self.count % 3 == 0:
            self.detected_faces = vision_utils.get_faces_in_frame(image, self.known_faces.keys(), self.known_faces.values())

        self.display_frame = image.copy()
        self.display_frame = vision_utils.draw_faces_on_frame(self.display_frame, self.detected_faces, self.box_colours)

        # Display the image on the screen
        cv2.imshow('Magic Mirror', self.display_frame)
        key_pressed = cv2.waitKey(1)

        # Exit if spacebar pressed
        if key_pressed == ord(' '):
            print('Exiting')
            cv2.destroyAllWindows()
            exit()

        self.count += 1

if __name__ == "__main__":
    mm = MagicMirror()