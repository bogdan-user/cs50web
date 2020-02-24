import csv
import os

from flask import Flask, render_template, request
from tables import *

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgres://raqxmtydoxefpl:9e702a8b4b0b1576b2bc14e0e9a20cac2154e5cc9d6a71d14775470f51b4270b@ec2-54-247-82-14.eu-west-1.compute.amazonaws.com:5432/dduuh49ajp0ahi'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        books = Books(isbn=isbn, title=title, author=author, year=year)
        db.session.add(books)
        print(f"{isbn}, {title}, {author}, {year}")
    db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        main()
