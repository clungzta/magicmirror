import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# db_dir = os.path.join(BASE_DIR, 'data/db')
# db_path = os.path.join(db_dir, 'app.db')
db_uri = 'sqlite:///{}'.format('test.db')

print(db_uri)

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username