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
from collections import deque
from termcolor import cprint
from datetime import datetime
from expiringdict import ExpiringDict
from zmq_utils import send_array, recv_array, get_uri

# File Imports
import utils
# import speech_utils
import vision_utils

'''

Attempt at threading did not work effectively

'''

# class CameraWorker(threading.Thread):
#     def __init__(self, name, master, in_queue, out_queue):
#         threading.Thread.__init__(self)
#         self.name = name
#         self.master = master
#         self.thread_lock = self.master.thread_lock

#         self.in_q = in_queue
#         self.out_q = out_queue

#         print('Starting vision worker: {}'.format(name))
#         return

#     def run(self):
#         while True:
#             # time.sleep(0.001)
                       
#             # Fetch image from in_queue using the thread lock
#             self.thread_lock.acquire()
#             try:
#                 num_items = len(self.in_q)

#                 print(self.name, num_items)

#                 if num_items < 1:
#                     continue
                
#                 image = self.in_q.pop()

#             finally:
#                 self.thread_lock.release()

#             # Process the image
#             print(image.shape)
#             faces = vision_utils.get_faces_in_frame(image, self.master.known_faces.keys(), self.master.known_faces.values(), self.master.scale_factor)

#             # Store result in out_queue using the thread lock
#             self.thread_lock.acquire()
#             try:
#                 print(self.name, faces)
#                 # out_queue.push(faces)
#             finally:
#                 self.thread_lock.release()

class MagicMirrorCameraHandler(object):
    def __init__(self, debug=False, ip='0.0.0.0', port=6700):
        
        self.debug = debug

        # Choose the webcam with the highest device ID
        devices = vision_utils.list_video_devices()
        device = devices[-1]
        
        print('Initializing Magic Mirror on {}'.format(device))
        device_num = int(re.findall('\d+', device)[0])

        self.video_cap = cv2.VideoCapture(device_num)
        # self.video_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        # self.video_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.video_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.video_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        self.frame_count = 0

        known_faces_path = os.path.join(os.path.abspath('..'), 'data/uploads')
        self.known_faces = vision_utils.load_known_faces(known_faces_path)
        self.box_colours = dict(zip(self.known_faces.keys(), utils.pretty_colours(len(self.known_faces.keys()))))
        self.detected_faces_cache_ = ExpiringDict(max_len=100, max_age_seconds=2.5)
        self.detected_faces = []
    
        self.display_text = ''

        self.zcontext = zmq.Context()
        self.uri = get_uri(ip, port)
        self.socket = self.zcontext.socket(zmq.PUB)
        
        print('Camera handler binding to: {}'.format(self.uri))
        self.socket.bind(self.uri)

        # num_threads = 5
        # self.in_q = deque(maxlen=num_threads*2)
        # self.out_q = deque(maxlen=num_threads*2)
        # self.thread_lock = threading.Lock()
       
        # # Start worker threads for image processing
        # for i in range(num_threads):
        #     t = CameraWorker(i, self, self.in_q, self.out_q)
        #     t.start()

    def __del__(self):
        self.video_cap.release()
    
    def get_frame(self):
        success, image = self.video_cap.read()
        
        if success:

            self.frame_count += 1
            display_img = self.process_frame(image)

            # Publish dict recently seen faces (queued with expiring timout) using zmq
            # (e.g. can be subscribed to by the speech handler and/or websocket server)
            cur_faces = {k: v for k, v in self.detected_faces_cache_.items() if v[1] > 0.98}
            self.socket.send_json(cur_faces)

            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 30]
            ret, jpeg = cv2.imencode('.jpg', display_img)
            return jpeg.tobytes()

    def process_frame(self, image):
         # Perform a horizontal flip transformation to make the image look just like a mirror
        image = cv2.flip(image.copy(), 1)

        # Recognize faces every N frames
        scale_factor = 0.20

        if self.frame_count % 15 == 0:
            prev_detected_people,temporal_likelihood_scores = self.get_detected_faces_cache()
            self.detected_faces_limbo = vision_utils.get_faces_in_frame(image, self.known_faces.keys(), self.known_faces.values(), scale_factor)

            self.detected_faces = []
            for face in self.detected_faces_limbo:
                bbox_area = abs(face[0][2] - face[0][0]) * abs(face[0][1] - face[0][3])
                
                # Use temporal information to help filter false detections which occur in individual frames
                prev_det_people = dict(zip(prev_detected_people, temporal_likelihood_scores))

                if face[1] in prev_det_people:
                    # We have seen the face recently
                    # So, lets increase the temporal likelihood score of that face
                    alpha = 0.5
                    new_temporal_likelihood = prev_det_people[face[1]] + alpha

                    # Clamp the temporal likelihood to a maximum of 1.0
                    if new_temporal_likelihood > 1.0:
                        new_temporal_likelihood = 1.0

                else:
                    # We havent seen the face recently
                    # Initialize the temporal likelihood score with 0.0
                    new_temporal_likelihood = 0.0
                
                # Update the temporal face cache accordingly
                self.detected_faces_cache_[face[1]] = (bbox_area, new_temporal_likelihood)

                # We are very confident that the person is actually there
                # So move from "limbo" to actual detections
                if new_temporal_likelihood > 0.99:
                    self.detected_faces.append(face)

        display_frame = image.copy()
        display_frame = vision_utils.draw_faces_on_frame(display_frame, self.detected_faces, self.box_colours, scale_factor)

        return display_frame

    def get_detected_faces_cache(self):
        faces_sorted_by_size = sorted(self.detected_faces_cache_.items(), key=lambda x: x[1], reverse=True)
        # print(faces_sorted_by_size)

        if len(faces_sorted_by_size):
            names, list_of_tups = zip(*faces_sorted_by_size)
            temporal_likelihood_scores = zip(*list_of_tups)[1]

            return names, temporal_likelihood_scores

        else:
            return [], []