from flask_sqlalchemy import SQLAlchemy
#
db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

#####
class books(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)

class reviews(db.Model):
    __tablename__= "reviews"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    id_book = db.Column(db.String, nullable=False)
    text = db.Column(db.String, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
