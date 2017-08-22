import os
import re
import cv2
import fnmatch
import numpy as np
import face_recognition

def list_video_devices():
    return sorted(filter(re.compile('video[0-9]').match, os.listdir('/dev')))

def load_known_faces(path):
    names, face_encodings_training = [], []

    for file in os.listdir(path):
        if fnmatch.fnmatch(file, '*.jpg'):
            # print('Loading {}'.format(file))
            names.append(os.path.splitext(file)[0].title())
            loaded_image = face_recognition.load_image_file(os.path.join(path, file))
            face_encodings_training.append(face_recognition.face_encodings(loaded_image)[0])

    return dict(zip(names, face_encodings_training))

def get_faces_in_frame(frame, names, face_encodings_training):
    
    # Downscale frame resolution for faster processing
    small_frame = cv2.resize(frame.copy(), (0, 0), fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)

    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(small_frame)
    face_encodings = face_recognition.face_encodings(small_frame, face_locations)

    face_names = []
    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s)
        match = face_recognition.compare_faces(face_encodings_training, face_encoding)
        name = "Unknown"

        detected_people = np.asarray(names)[np.asarray(match)]
        
        if any(detected_people):
            name = detected_people[0]

        face_names.append(name)

    # Sort face names by area
    return sorted(zip(face_locations, face_names), key=lambda x: abs(x[0][2] - x[0][0]) * abs(x[0][1] - x[0][3]), reverse=True)

def draw_faces_on_frame(frame, detected_faces, box_colours):
    for count, ((top, right, bottom, left), name) in enumerate(detected_faces):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        if name is not "Unknown":
            box_colour = box_colours[name]
        else:
            box_colour = (255,255,255)

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), box_colour, 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), box_colour, cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (0, 0, 0), 2)

    return frame

def draw_overlay(mode, frame):
    if mode == 'READY':
        pass
    elif mode == 'CALENDAR':
        pass
    elif mode == 'TRAFFIC':
        pass

    return frame