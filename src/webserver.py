import flask
import datetime
import flask_login
import hashlib, uuid
from flask_sqlalchemy import SQLAlchemy
from flask import Flask,session, request, flash, url_for, redirect, render_template, abort ,g
from flask_login import login_user , logout_user , current_user , login_required

app = flask.Flask(__name__)

# config
app.config.update(
    DEBUG = True,
    SECRET_KEY = 'secret_xxx',
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format('db/test.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    template_folder = 'template'
)

db = SQLAlchemy(app)

# flask_login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# Our mock database.
# users = {'foo@bar.tld': {'pw': 'secret'}}

class User(db.Model):
    __tablename__ = "users"
    id = db.Column('user_id',db.Integer , primary_key=True)
    username = db.Column('username', db.String(20), unique=True , index=True)
    password = db.Column('password' , db.String(10))
    email = db.Column('email',db.String(50),unique=True , index=True)
    registered_on = db.Column('registered_on' , db.DateTime)
 
    def __init__(self , username ,password , email):
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

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/register' , methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    user = User(request.form['username'] , request.form['password'],request.form['email'])
    db.session.add(user)
    db.session.commit()
    flash('User successfully registered')
    return redirect(url_for('login'))
 
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return(render_template('login.html'))
 
    username = request.form['username']
    password = request.form['password']
    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True
    registered_user = User.query.filter_by(username=username,password=password).first()
    if registered_user is None:
        flash('Username or Password is invalid' , 'error')
        return redirect(url_for('login'))
    login_user(registered_user, remember = remember_me)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or '/protected')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/protected')

@app.before_request
def before_request():
    g.user = current_user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'

@app.route('/protected')
@flask_login.login_required
def protected():
    return 'Logged in as: {}'.format(flask_login.current_user.username)
    
if __name__ == "__main__":
    app.run()
    # db.create_all()

    # admin = User('admin', 'test123', 'admin@example.com')
    # guest = User('guest', 'test123', 'guest@example.com')

    # db.session.add(admin)
    # db.session.add(guest)
    # db.session.commit()