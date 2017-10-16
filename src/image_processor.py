
import os
import zmq
import json
import time
import utils
import vision_utils
import pprint as pp
from zmq_utils import recv_array
from collections import OrderedDict
from sklearn.externals import joblib
from expiringdict import ExpiringDict


class ImageProcessor:

    def __init__(self, process_every=5, person_TTL=2.5):
        self.process_every = process_every
        
        self.zcontext = zmq.Context()

        self.uri_sub = 'tcp://127.0.0.1:6710'
        self.uri_pub = 'tcp://127.0.0.1:6700'

        self.sub_socket = self.zcontext.socket(zmq.SUB)
        self.sub_socket.connect(self.uri_sub)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, '')

        self.pub_socket = self.zcontext.socket(zmq.PUB)
        print('Image processor PUB binding to: {}'.format(self.uri_pub))
        self.pub_socket.bind(self.uri_pub)

        # Face recognition stuff
        known_faces_path = os.path.join(os.path.abspath('..'), 'data/uploads')
        self.known_faces = vision_utils.load_known_faces(known_faces_path)
        self.box_colours = dict(zip(self.known_faces.keys(), utils.pretty_colours(len(self.known_faces.keys()))))
        self.recently_seen_faces_ = ExpiringDict(max_len=100, max_age_seconds=person_TTL)
        self.detected_faces = []

        # Emotion recognition stuff        
        self.emotion_clf = joblib.load('emotion_classifier.pkl')

        self.run()

    def run(self):
        loopCount = 0
        while True:
            loopCount += 1
            image = recv_array(self.sub_socket)
            print(image.shape)
            
            # if (loopCount % self.process_every == 0):
            self.process_frame(image)

    def process_frame(self, frame):
        # print('Processing frame')
        # print(frame.shape)

        known_names = self.known_faces.keys()
        known_encodings = self.known_faces.values()

        # Get dict of people that have been seen recently
        recently_seen_people = self.get_recently_seen_faces()

        # Temporal windowing to filter face matches accross a sequence of frames.
        for bbox, name in vision_utils.get_faces_in_frame(frame, known_names, known_encodings, scale_factor=0.2):
            
            # print('recently seen', recently_seen_people)

            # Update recently_seen_faces
            if name in recently_seen_people:
                num_times_seen = recently_seen_people[name][1] + 1
            else:
                num_times_seen = 1

            self.recently_seen_faces_[name] = (vision_utils.calculate_face_area(bbox), num_times_seen, bbox)

        # Positive match if person recognized at least three times within the prior @person_TTL seconds 
        recognized_faces = {k: v for k, v in self.recently_seen_faces_.items() if v[1] > 3}
        print(recognized_faces)

        emotion_vectors = vision_utils.get_face_landmarks(frame).reshape(1, -1)
        
        if emotion_vectors.any():
            # print(self.emotion_clf.get_params(deep=True))
            predicted_emotions = self.emotion_clf.predict_proba(emotion_vectors)
            
            for person_emotions in predicted_emotions:
                result = sorted(zip(self.emotion_clf.classes_, person_emotions), key=lambda x:x[1], reverse=True)
                print('{} {:.1%}'.format(result[0][0],result[0][1]))

        self.pub_socket.send_json(recognized_faces)

    def get_recently_seen_faces(self):
        # Get the list of recently seen faces from the ExpiringDict, sort by area
        return OrderedDict(sorted(self.recently_seen_faces_.items(), key=lambda x: x[1], reverse=True))

if __name__ == '__main__':
    image_processor = ImageProcessor()