from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login


class User(UserMixin, db.Model):
    id = db.Column(
        db.Integer, primary_key=True
    )  # primary keys are required by SQLAlchemy
    username = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(1000))

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class BookingCantine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    booked = db.Column(db.String(5000))


class BookingGarderieMatin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    booked = db.Column(db.String(5000))


class BookingGarderieSoir(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    booked = db.Column(db.String(5000))


class Configuration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True)
    config_text = db.Column(db.String(100))
    value = db.Column(db.String(100))
    config_order = db.Column(db.Integer)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
