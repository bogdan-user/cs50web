from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, jsonify
from sqlalchemy import or_, and_
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from tables import *
import requests
import os


app = Flask(__name__)
app.secret_key = os.environ.get('secret_key')

# Set up database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Making a register form using WTFORMS
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=20)])
    username = StringField('Username', [validators.Length(min=1, max=15)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message = "Passwords don't match!")
    ])
    confirm = PasswordField('Confirm Password')
# If user is not in session -> Unauthorized message
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, please login", 'danger')
            return redirect(url_for('login'))
    return wrap

# Home page
@app.route('/')
def index():
    return render_template('home.html')

# Register page
@app.route('/register', methods=["GET","POST"])
def register():
    if 'username' in session: # Check if user is in session
        return redirect(url_for('dashboard'))
    else:
        form = RegisterForm(request.form)
        if request.method == "POST" and form.validate():
            # Getting data from the form
            name = form.name.data
            email = form.email.data
            username = form.username.data
            password = sha256_crypt.encrypt(str(form.password.data)) # Hashing the password
            email_query = Users.query.filter_by(email=email).first()
            user_query = Users.query.filter_by(username=username).first()
            # Checking if email already exits in DB
            if email_query:
                emerror = f"{email} already taken!"
                return render_template("register.html", emerror=emerror, form=form)
            # Checking if username already exists in DB
            if user_query:
                unerror = f"{username} already taken!"
                return render_template("register.html", unerror=unerror, form=form)
            # If not, add to the DB
            else:
                user = Users(name=name, email=email, username=username, password=password)
                db.session.add(user)
                db.session.commit()
                flash("You are now registered and can log in", 'success')
                return render_template('register.html', form=form)
        return render_template('register.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    else:
        if request.method == "POST":
            user = request.form['username']
            password_candidate = request.form['password']
            user_check = Users.query.filter_by(username=user).first()
            # If the user exists -> need to check if password from form == hashed password in DB
            if user_check:
                password = user_check.password
                if sha256_crypt.verify(password_candidate, password):
                    session['logged_in'] = True # If password is correct -> creating a session for the user
                    session['username'] = user
                    flash('You are now logged in', 'success')
                    return redirect(url_for("dashboard"))
                else:
                    error = "Invalid password"
                    return render_template('login.html', error = error)
            else:
                error = "Username doesn't exist"
                return render_template('login.html', error = error)
        else:
            return render_template('login.html')

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard', methods = ["GET", "POST"])
def dashboard():
    if 'username' in session:
        if request.method == "POST":
            search = request.form.get("search")
            book_format = "%{}%".format(search) # For entering only a part of title/author/isbn
            bookDB = books.query.filter(or_(books.author.like(book_format), books.title.like(book_format), books.isbn.like(book_format))).all()
            if bookDB:
                return render_template('dashboard.html', bookDB=bookDB)
            else:
                return render_template('dashboard.html', error=f"'{search}' does not exist.")
            return render_template('dashboard.html', bookDB=bookDB)
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))

@app.route('/dashboard/<int:book_id>', methods = ["GET", "POST"])
def bookid(book_id):
    if 'username' in session:
        book = books.query.filter_by(id = book_id).first()
        revs = reviews.query.filter_by(id_book = book_id).all()
        if request.method == "GET":
            if book is None:
                return render_template('dashboard.html', error = f"'{book_id}' not found! ")
            else:
                # GETTING REVIEWS USING GOODREADS API
                res = requests.get(f'https://www.goodreads.com/book/review_counts.json?isbns={book.isbn}&key=AhYnunncR1YdMeRsaEkzw')
                data = res.json()
                book_rate = float(data['books'][0]['average_rating'])
                book_ratings = int(data['books'][0]['work_ratings_count'])

                # MAKING OWN AVERAGE RATE FROM USERS
                site_rate = db.session.query(reviews.rating).filter_by(id_book=book_id).all() # Query all ratings at a specific book
                book_rates = [value for value, in site_rate] # Unpack list of values beacuse site_rate returns list of tuples
                sum = 0
                for i in range(len(book_rates)):
                    sum += book_rates[i]
                len_book_rates = len(book_rates)
                if len_book_rates != 0:
                    average_site_rate = float(sum/len_book_rates)
                    return render_template('bookid.html', book=book, revs=revs, book_rate=book_rate, book_ratings=book_ratings, average_site_rate=average_site_rate)
                else:
                    return render_template('bookid.html', book=book, revs=revs, book_rate=book_rate, book_ratings=book_ratings, average_site_rate=0.00)
        else:
            review = request.form.get("review")
            rating = request.form.get("options")
            review_check = reviews.query.filter_by(username=session['username']).filter_by(id_book=book_id).first() # Check if username already written a review
            if review_check:
                return render_template("bookid.html", error="Review already written", book=book, revs=revs)
            else:
                rev = reviews(username=session['username'], id_book=book_id, text=review, rating=rating)
                db.session.add(rev)
                db.session.commit()
                return redirect(url_for('bookid', book_id=book_id))
    return redirect(url_for('login'))

@app.route("/api/<isbn>", methods = ["GET"])
def api(isbn):
    if 'username' in session:
        if request.method == "GET":
            book_check = db.session.execute("SELECT * FROM books where isbn = :isbn", {"isbn":isbn}).fetchone()
            row = db.session.execute("SELECT isbn, title, author, year, \
                    COUNT(id_book) as review_count, \
                    AVG(reviews.rating) as average_score\
                    FROM books \
                    INNER JOIN reviews \
                    ON books.id = reviews.id_book \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                    {"isbn": isbn})
            if book_check:
                if row.rowcount != 1:
                    return jsonify({"Error": "Book has no average_score"}), 422

                # Fetch result from RowProxy
                fet = row.fetchone()

                # Convert to dict
                result = dict(fet.items())

                # Json doesn's support float numbers so I needed this trick
                result['average_score'] = float('%.2f'%(result['average_score']))
                return jsonify(result)
            else:
                return jsonify({"Error": "Book invalid isbn"}), 422
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
