from db_main import db
from db_main import User

db.create_all()

admin = User('admin', 'admin@example.com')
guest = User('guest', 'guest@example.com')

db.session.add(admin)
db.session.add(guest)
db.session.commit()

users = User.query.all()
print(users)