import os
import json
import base64
import flask
import datetime
import cStringIO
import flask_login
import numpy as np
import hashlib, uuid
from PIL import Image
from termcolor import cprint
from flask import Flask, session, request, flash, url_for, redirect, render_template, abort, g, Response, send_file, jsonify

VIDEO_STREAMING_ENABLED = True

UPLOAD_FOLDER = os.path.join(os.path.abspath('..'), 'data/uploads')

if VIDEO_STREAMING_ENABLED:
    from camera_handler import MagicMirrorCameraHandler

# FIXME
DATASTORE_ENABLED = VIDEO_STREAMING_ENABLED

if DATASTORE_ENABLED:
    from google.cloud import datastore
    import vision_utils

app = flask.Flask(__name__, static_url_path='')

# config
app.config.update(
    DEBUG = True,
    SECRET_KEY = 'secret_xxx',
    #SQLALCHEMY_DATABASE_URI = 'postgresql://tester:test_password@localhost:5432/magicmirror',
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format('db/test.db'),
    # SQLALCHEMY_TRACK_MODIFICATIONS = False,
    template_folder = 'template'
)

@app.route('/preferences')
def preferences():
    return render_template('preferences.html')

@app.route('/adduserpanel')
def add_user_panel():
    return render_template('adduserpanel.html')

@app.route('/person_sightings')
def person_sightings(methods=['GET', 'POST']):
    if not DATASTORE_ENABLED:
        raise Exception('Datastore not enabled, enable it in webserver.py')

    if request.method == 'GET':
        client = datastore.Client()

        name = request.args.get('name').lower()

        query = client.query(kind='Interaction')
        query.add_filter('people', '=', name)

        num_results = int(request.args.get('num_results', 10))
        
        output = []
        
        for item in query.fetch():
            temp = {}
            temp['timestamp'] = item.key.id,
            temp['seen_with'] = item['people'].remove(name),
            temp['conversation_session_id'] = None,
            temp['conversation'] = {'intents' : [], 'contexts' : [], 'actions' : []},
            temp['emotion_probabillites'] = {}
            output.append(temp)

        return jsonify(output)

@app.route('/')
def magicmirror():
    return render_template('index.html')

def gen(camera):
    while True:
        frame = camera.get_frame()

        # could put a zmq request in here, send image, request processing from other node

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():

    if VIDEO_STREAMING_ENABLED:
        return Response(gen(MagicMirrorCameraHandler()), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return send_file('static/images/camera_disabled.png', mimetype='image/png')
    
@app.route('/person', methods=['GET', 'POST'])
def person():
    if request.method == 'GET':
        person = Person.query.filter_by(id=request.args.get('id')).first()

        if person is not None:
            outdata['firstname'] = person.firstname
            outdata['lastname'] = person.lastname
            outdata['datetime_added'] = person.datetime_added
        else:
            outdata = {}

    elif request.method == 'POST':
        person_name = request.form.get('person_name').lower()

        file = request.files['profile_photo']
        print(file)

        ext = os.path.splitext(file.filename)[-1].lower()

        if ext in ['.png', '.jpg', '.jpeg']:
            image = Image.open(file.stream)
            img = np.array(image)
            
            try:
                # Generate the face recognition embedding vector
                embedding = vision_utils.get_face_embedding(img)
                
                print(person_name, img.shape, embedding.shape)

                # Save the face recognition embedding vector
                np.save(os.path.join(UPLOAD_FOLDER, person_name + '.npy'), embedding)
                # Save the image                    
                image.save(os.path.join(UPLOAD_FOLDER, person_name + '.jpg'))

            except IndexError:
                print('No face found')
                flash('Error, no face found in image. Please try again!' , 'error')
                return redirect(url_for('preferences'))                                         

        else:
            flash('Invalid Filetype! Ignoring' , 'error')
            return redirect(url_for('preferences'))                         

        return redirect(url_for('preferences'))

if __name__ == "__main__":
    app.run(debug=True, threaded=True, host='0.0.0.0')
