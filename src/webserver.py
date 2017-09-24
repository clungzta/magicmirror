import flask
import datetime
import flask_login
import hashlib, uuid
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, session, request, flash, url_for, redirect, render_template, abort, g, Response, send_file, jsonify
from flask_login import login_user , logout_user , current_user , login_required

VIDEO_STREAMING_ENABLED = True

if VIDEO_STREAMING_ENABLED:
    from camera_handler import MagicMirrorCameraHandler

app = flask.Flask(__name__, static_url_path='')

# config
app.config.update(
    DEBUG = True,
    SECRET_KEY = 'secret_xxx',
    SQLALCHEMY_DATABASE_URI = 'postgresql://tester:test_password@localhost:5432/magicmirror',
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format('db/test.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    template_folder = 'template'
)
db = SQLAlchemy(app)

# flask_login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(20), unique=True , index=True)
    password = db.Column('password' , db.String(150))
    email = db.Column('email',db.String(50),unique=True , index=True)
    registered_on = db.Column('registered_on' , db.DateTime)
 
    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email
        self.registered_on = datetime.datetime.utcnow()
 
    def is_authenticated(self):
        return True
 
    def is_active(self):
        return True
 
    def is_anonymous(self):
        return False
 
    def get_id(self):
        return unicode(self.id)
 
    def __repr__(self):
        return '<User %r>' % (self.username)

class Person(db.Model):
    __tablename__ = "person"
    id = db.Column('person_id', db.Integer , primary_key=True)
    firstname = db.Column('firstname', db.String(20))
    lastname = db.Column('lastname' , db.String(20))
    height = db.Column('height' , db.Float(20))
    # hair_colour_histogram = db.Column('hair_colour_histogram' , db.Array(64))
    # face_embedding = db.Column('face_embedding' , db.Array(64))
    datetime_added = db.Column('datetime_added' , db.DateTime)
 
    def __init__(self, firstname, lastname, face_embedding, height):
        self.firstname = firstname
        self.lastname = lastname
        self.height = height
        self.face_embedding = face_embedding
        self.datetime_added = datetime.datetime.utcnow()
 
    def get_id(self):
        return unicode(self.id)
 
    def __repr__(self):
        return '<User %r>' % (self.username)

class Interaction(db.Model):
    __tablename__ = "interaction"
    id = db.Column('interaction_id', db.Integer , primary_key=True)
    person_id = db.Column('person_id', db.Integer)
    conversation_id = db.Column('conversation_id' , db.Integer)
    detected_activity = db.Column('detected_activity_id' , db.String(20)) # e.g. brushing teeth
    timestamp = db.Column('timestamp' , db.DateTime)
 
    def __init__(self, person_id, conversation_id, detected_activity=None):
        self.person_id = person_id
        self.conversation_id = conversation_id
        self.detected_activity = detected_activity
        self.timestamp = datetime.datetime.utcnow()
 
    def get_id(self):
        return unicode(self.id)
 
    def __repr__(self):
        return '<User %r>' % (self.username)

# db.create_all()

def hash_password(password):
    # uuid is used to generate a random number
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

def check_password(hashed_password, user_password):
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/register' , methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    username_taken = User.query.filter_by(username=request.form['username']).first()
    email_taken = User.query.filter_by(email=request.form['email']).first()
    
    if username_taken:
        flash('Cannot create account. Username is already taken' , 'error')
        return redirect(url_for('register'))
    elif email_taken:
        flash('Cannot create account. Email is already taken' , 'error')
        return redirect(url_for('register'))

    user = User(request.form['username'] , hash_password(request.form['password']),request.form['email'])
    db.session.add(user)
    db.session.commit()
    flash('User successfully registered')
    return redirect(url_for('login'))
 
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return(render_template('login.html'))

    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True

    registered_user = User.query.filter_by(username=request.form['username']).first()

    if registered_user is None:
        flash('Username is invalid' , 'error')
        return redirect(url_for('login'))
    
    if not(check_password(registered_user.password, request.form['password'])):
        flash('Password is invalid' , 'error')
        return redirect(url_for('login'))

    login_user(registered_user, remember = remember_me)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or '/')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

@app.before_request
def before_request():
    g.user = current_user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect('/login')

@app.route('/preferences')
@flask_login.login_required
def preferences():
    return render_template('preferences.html')

@app.route('/adduserpanel')
@flask_login.login_required
def add_user_panel():
    return render_template('adduserpanel.html')

@app.route('/')
@flask_login.login_required
def magicmirror():
    return render_template('index.html')
    # return 'Logged in as: {}'.format(flask_login.current_user.username)

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
@flask_login.login_required
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

        if person:
            db.session.add(person)
            db.session.commit()
        
        return jsonify({})

if __name__ == "__main__":
    app.run(debug=True, threaded=True, host='0.0.0.0')
    # db.create_all()

    # admin = User('admin', 'test123', 'admin@example.com')
    # guest = User('guest', 'test123', 'guest@example.com')

    # db.session.add(admin)
    # db.session.add(guest)
    # db.session.commit()