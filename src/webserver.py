import flask
import datetime
import flask_login
import hashlib, uuid
# from flask_sqlalchemy import SQLAlchemy
from flask import Flask, session, request, flash, url_for, redirect, render_template, abort, g, Response, send_file, jsonify

VIDEO_STREAMING_ENABLED = False

if VIDEO_STREAMING_ENABLED:
    from camera_handler import MagicMirrorCameraHandler

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
        person_id = int(request.form.get('id'))
        print(request.form.get('fileToUpload'))
        print(request.form.items())
        
        # person_id = 1
        print('updating person {} details...'.format(person_id))
        person = Person.query.get(person_id)
        print(person)

        # if person:
        #     db.session.add(person)
        #     db.session.commit()
        
        return jsonify({})

if __name__ == "__main__":
    app.run(debug=True, threaded=True, host='0.0.0.0')
