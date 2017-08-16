import cv2
import numpy as np

from speech_utils import *
from vision_utils import *

class MagicMirror:
    def __init__(self):
        print('Initializing Magic Mirror...')
        self.video_cap = cv2.VideoCapture(0)

        self.video_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.video_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        cv2.namedWindow("Magic Mirror", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Magic Mirror",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
        
        while(True):
            ret, frame = self.video_cap.read()
            self.process_frame(frame)

    def process_frame(self, image):
        # print(image.shape)

        # Display the image on the screen
        cv2.imshow('Magic Mirror', image)
        key_pressed = cv2.waitKey(1)

        # Exit if spacebar pressed
        if key_pressed == ord(' ') or key_pressed == 27:
            print('Exiting')
            cv2.destroyAllWindows()
            exit()

if __name__ == "__main__":
    mm = MagicMirror()