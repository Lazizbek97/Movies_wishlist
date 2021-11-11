from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
import sqlite3
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

# API, URLs for search movie
MY_API = "1acae7818c7a2dd20a5839febd1f4904"
API_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

# CREATE FLASK APP WITH BOOTSTRAP
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

# CREATE WTForms
class EditForm(FlaskForm):
    rating = StringField('Update rating', validators=[DataRequired()])
    review = StringField('Update review', validators=[DataRequired()])
    submit = SubmitField("submit")

class AddMovie(FlaskForm):
    movie_name = StringField("Movie name", validators=[DataRequired()])
    submit = SubmitField("submit")


# CREATE DataBase
db = sqlite3.connect("best_movies_data.db", check_same_thread=False)
cursor = db.cursor()
# CREATEE Table
cursor.execute("CREATE TABLE IF NOT EXISTS movies("
               "id INT,"
               "title varchar(250) NOT NULL UNIQUE,"
               "year varchar(50) NOT NULL,"
               "description varchar(500) NOT NULL,"
               "rating FLOAT NOT NULL,"
               "ranking INT NOT NULL,"
               "review varchar(250) NOT NULL UNIQUE,"
               "img_url varchar(1000) NOT NULL)")
db.commit()

# ADD DATA TO DATABASE
def add_data(id, title,year,description,rating,ranking,review,img_url):
    cursor.execute("INSERT INTO movies VALUES (?,?,?,?,?,?,?,?)",(id, title,year,description,rating,ranking,review,img_url))
    db.commit()

# ROUTE TO HOME PAGE
@app.route("/")
def home():
    cursor.execute("SELECT * FROM movies")
    data = cursor.fetchall()
    if data != []:
        data = sorted(data, key=lambda film: float(film[4]))
    return render_template("index.html",data = data, lenght = len(data))

# ROUTE TO UPDATE RATING AND REVIEW PAGE
@app.route('/update/<title>', methods = ['GET', 'POST'])
def update_data_page(title):
    form = EditForm()
    if form.validate_on_submit():
        cursor.execute("UPDATE movies SET rating=? WHERE title =?",(form.rating.data, title))
        db.commit()
        cursor.execute("UPDATE movies SET review=? WHERE title =?", (form.review.data, title))
        db.commit()
        # after submit redirect to homepage again
        return redirect(url_for('home'))

    return render_template("edit.html", form = form)

# ROUTE TO DELETE DATA FROM DATABASE
@app.route('/delete/<title>')
def delete_data(title):
    cursor.execute("DELETE FROM movies WHERE title =?", (title,))
    db.commit()
    return redirect(url_for('home'))

# ROUTE TO ADD MOVIE TO LIST
@app.route('/add', methods = ['GET', 'POST'])
def add_movie():
    form = AddMovie()
    if form.validate_on_submit():
        search_movie = form.movie_name.data
        response = requests.get(url=API_URL, params={"api_key": MY_API,
                                                     "language": "en-US",
                                                     "query": search_movie})
        movies_list = response.json()
        # route to select the movie from list which is recommended according to searched name
        return render_template("select.html", movies_list = movies_list["results"], find_movie = search_movie)
    return render_template("add.html", form = form)

# ROUTE TO SAVING DATA FROM RECOMMENDED LIST
@app.route('/save/<save_this>/<find_movie>', methods = ['GET', 'POST'])
def save_to_data_base(save_this, find_movie):
    form = EditForm()
    # click qilingan film ga yangi rating va review berilgandan so'ng submit qilinsa
    if form.validate_on_submit():
        # so'ralgan nomga ko'ra ismlar listini chiqarib beradi
        response = requests.get(url=API_URL, params={"api_key": MY_API,
                                                     "language": "en-US",
                                                     "query": find_movie})
        movies_list = response.json()
        # ular ichidan biz click qilgan filmning ID si bilan bir xilini ajratib oladi
        for i in movies_list["results"]:
            if int(save_this) == i['id']:

                add_data(i['id'],i['title'], i['release_date'],i['overview'], f"{form.rating.data}", "1",f"{form.review.data}", f"{MOVIE_DB_IMAGE_URL}{i['poster_path']}")

        return redirect(url_for('home'))
    # yangi film uchun hali review va rating ball berilmagani uchun, editpage ga borib usha malumotlarni olib keladi
    return render_template("edit.html", form = form)

if __name__ == '__main__':
    app.run(debug=True)
