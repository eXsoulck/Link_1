import string
import random

import qrcode
from pathlib import Path
from flask import Flask, render_template, url_for, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///new-user.db"
app.config["SECRET_KEY"] = "hellojeka"
db = SQLAlchemy(app)


class NewUser(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_email = db.Column(db.String(), nullable=False, unique=True)
    user_pass = db.Column(db.String(), nullable=False)
    links = db.relationship("Link", backref="someuser")


class Link(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_link = db.Column(db.String(), nullable=False, unique=True)
    link_title = db.Column(db.String(), nullable=False)
    short_link = db.Column(db.String(), nullable=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("new_user.id"))

with app.app_context():
    db.create_all()

# back half link generator
def link_generator():
    back_half_link = "".join(map(str, random.sample(string.printable, 5)))
    print(back_half_link)
    return back_half_link


@app.route("/")
def hello_world():  # put application's code here

    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    user_email = request.form["u_email"]
    user_pass = request.form["u_pass"]
    get_user = NewUser.query.filter_by(user_email=user_email).first()
    if get_user:
        if check_password_hash(get_user.user_pass, user_pass):
            session["user"] = user_email
            return redirect(url_for("dashboard"))
        else:
            flash("Incorrect password, try again .", "login_error")
            return render_template("index.html")
    else:
        flash("Wrong email", "login_error")
        return redirect(url_for("hello_world"))


@app.route("/register", methods=["POST"])
def register():
    error = None
    user_email = request.form["u_email"]
    user_pass = request.form["u_pass"]
    user_pass2 = request.form["u_pass2"]
    get_user = NewUser.query.filter_by(user_email=user_email).first()
    if get_user == None:
        if user_pass == user_pass2:
            hash_pass = generate_password_hash(user_pass)
            new_user = NewUser(user_email=user_email, user_pass=hash_pass)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("hello_world"))
        else:
            flash("The password doesn't match", "regisret_error")
            return redirect(url_for("hello_world"))
    elif user_email in get_user.user_email:
        flash(f"The email {get_user.user_email} is already in use, try another one !", "regisret_error")
        print(user_email, get_user.user_email)
        return redirect(url_for("hello_world", error=error))


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if request.method == "GET":
        if "user" in session:
            print(session["user"])
            current_user = session["user"]
            get_user = NewUser.query.filter_by(user_email=current_user).first()
            return render_template("dashboard.html", get_user=get_user)
        else:
            flash("You should be authorised", category="authorise")
            return redirect(url_for("hello_world"))
    if request.method == "POST":
        user_link = request.form["u_link"]
        compare = Link.query.filter_by(user_link=user_link).first()
        if compare is None:
            if (request.form["custom_part"] == "") or (request.form["custom_part"] is None):
                short_link = link_generator()
                print(short_link)
            else:
                short_link = request.form["custom_part"]
            # create QRcode
            link_title = request.form["l_title"]
            qr = qrcode.QRCode(version=15, box_size=10, border=5)
            qr.add_data(request.form["u_link"])  # Adding the data to be encoded to the QRCode object
            qr.make(fit=True)  # Making the entire QR Code space utilized
            img = qr.make_image()  # Generating the QR Code
            # Getting the directory where the file has
            # to be sav
            # img.save(f"static/images/{short_link}.png")
            current_user = session["user"]
            get_user = NewUser.query.filter_by(user_email=current_user).first()
            add_link = Link(user_link=user_link, link_title=link_title, short_link=short_link, user_id=get_user.id)
            db.session.add(add_link)
            db.session.commit()
            images_location = Path.cwd() / "static"
            images_location /= "qr_codes"
            if not images_location.exists():
                images_location.mkdir()
            link_id = Link.query.filter_by(user_link=user_link).first()
            img.save(f"{images_location}/{link_id.id}.png")
            return redirect(url_for("dashboard", get_user=get_user))
        elif user_link == compare.user_link:
            flash("This link is already in data base ", category="link_error")
            return redirect(url_for("dashboard"))

@app.route("/update", methods=["POST"])
def update():
    if request.method == "POST":
        my_data = Link.query.get(request.form["id"])
        my_data.user_link = request.form["user_links"]
        my_data.link_title = request.form["user_title"]
        if request.form["back-half"] is None or request.form["back-half"] == "":
            my_data.short_link = link_generator()
            db.session.commit()
        else:
            my_data.short_link = request.form["back-half"]
            db.session.commit()
        return redirect(url_for("dashboard"))


@app.route("/delete/<ids>", methods=["POST", "GET"])
def delete(ids):
    my_data = Link.query.get(ids)
    db.session.delete(my_data)
    db.session.commit()
    return redirect(url_for("dashboard"))


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("hello_world"))


@app.route("/<short>")
def redir(short):
    find_link = Link.query.filter_by(short_link=short)
    finalurl = ""
    for _ in find_link:
        finalurl = _.user_link
    print(finalurl)
    return redirect(finalurl, code=302)


@app.route("/user_search", methods=["POST", "GET"])
def user_search():
    if request.method == "POST":
        user_request = request.form["user_search"]
        current_user = session["user"]
        get_user = NewUser.query.filter_by(user_email=current_user).first()
        search_resalt = Link.query.filter(Link.user_id.like(get_user.id), Link.link_title.like('%' + user_request + '%'))
        return render_template("dashboard.html", search_resalt=search_resalt)
    elif request.method == "GET":
        current_user = session["user"]
        get_user = NewUser.query.filter_by(user_email=current_user).first()

        return redirect(url_for("dashboard", get_user=get_user))


@app.route("/clear_flash_msg", methods=["POST"])
def clear_flash_msg():
    user_url = request.form["current_url"]
    if len(user_url) > 1:
        user_url = request.form["current_url"].replace("/", "")
    else:
        user_url = "hello_world"
    session.pop('_flashes', None)
    return redirect(url_for(user_url))

@app.route("/profile")
def profile():
    current_user = session["user"]
    get_user = NewUser.query.filter_by(user_email=current_user).first()
    link_amount = len(get_user.links)
    return render_template("profile.html", link_amount=link_amount, current_user=current_user)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
