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

def get_faces_in_frame(frame, names, known_encodings, scale_factor=0.25):
    
    # Downscale frame resolution for faster processing
    small_frame = cv2.resize(frame.copy(), (0, 0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)

    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(small_frame)
    face_encodings = face_recognition.face_encodings(small_frame, face_locations)

    face_names = []
    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s)
        match = face_recognition.compare_faces(known_encodings, face_encoding)
        name = "Unknown"

        detected_people = np.asarray(names)[np.asarray(match)]
        
        if any(detected_people):
            name = detected_people[0]

        face_names.append(name)

    # Sort face names by area
    return sorted(zip(face_locations, face_names), key=lambda x: abs(x[0][2] - x[0][0]) * abs(x[0][1] - x[0][3]), reverse=True)

def draw_faces_on_frame(frame, detected_faces, box_colours, scale_factor):
    for count, ((top, right, bottom, left), name) in enumerate(detected_faces):
        # Scale back up face locations since the frame we detected in was scaled down

        reciprocal_scale_factor = int(1.0/scale_factor)

        top *= reciprocal_scale_factor
        right *= reciprocal_scale_factor
        bottom *= reciprocal_scale_factor
        left *= reciprocal_scale_factor

        if name is not "Unknown":
            box_colour = box_colours[name]
        else:
            box_colour = (255,255,255)

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), box_colour, 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), box_colour, cv2.FILLED)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (0, 0, 0), 2)

    return frame

def overlay_transparent(background_img, img_to_overlay_t, x, y, overlay_size=None):
    """
    @brief      Overlays a transparant PNG onto another image using CV2
    
    @param      background_img    The background image
    @param      img_to_overlay_t  The transparent image to overlay (has alpha channel)
    @param      x                 x location to place the top-left corner of our overlay
    @param      y                 y location to place the top-left corner of our overlay
    @param      overlay_size      The size to scale our overlay to (tuple), no scaling if None
    
    @return     Background image with overlay on top
    """
    
    bg_img = background_img.copy()
    
    if overlay_size is not None:
        img_to_overlay_t = cv2.resize(img_to_overlay_t.copy(), overlay_size)

    # Extract the alpha mask of the RGBA image, convert to RGB 
    b,g,r,a = cv2.split(img_to_overlay_t)
    overlay_color = cv2.merge((b,g,r))
    print(overlay_color.shape)
    
    # Optional, apply some simple filtering to the mask to remove edge noise
    #mask = cv2.medianBlur(a,5)

    h, w, _ = overlay_color.shape

    x, y = int(x-(float(w)/2.0)), int((y-float(h)/2.0))
    roi = bg_img[y:y+h, x:x+w]

    print(h,w)
    print('x y: ', x,y)
    print(roi.shape, mask.shape)

    # Black-out the area behind the logo in our original ROI
    img1_bg = cv2.bitwise_and(roi,roi,mask = cv2.bitwise_not(mask))
    
    # Mask out the logo from the logo image.
    img2_fg = cv2.bitwise_and(overlay_color,overlay_color,mask = mask)

    # Update the original image with our new ROI
    bg_img[y:y+h, x:x+w] = cv2.add(img1_bg, img2_fg)
    return bg_img

def draw_overlay(mode, frame):
    if mode == 'READY':
        pass
    elif mode == 'CALENDAR':
        pass
    elif mode == 'TRAFFIC':
        pass

    return frame