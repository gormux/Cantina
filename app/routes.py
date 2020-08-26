import random
import string
from pprint import pprint as pp  # noqa
import arrow

from flask import flash, redirect, render_template, request, url_for, send_file
from flask_login import current_user, login_required, login_user, logout_user

from app import app, db
from app.forms import LoginForm, UserAddForm
from app.models import (
    User,
    BookingCantine,
    BookingGarderieMatin,
    BookingGarderieSoir,
    Configuration,
)
from app.calendar import Calendar, getBookedData
from app.export import create_xls
from docx import Document

calendar = Calendar(2020)

CATEGORIES = {
    "cantine": BookingCantine,
    "garderie_matin": BookingGarderieMatin,
    "garderie_soir": BookingGarderieSoir,
}


@app.context_processor
def import_app_config():
    app_config = {}
    for i in db.session.query(Configuration).order_by("config_order"):
        app_config[i.config_key] = {
            "order": i.config_order,
            "text": i.config_text,
            "value": i.value,
        }
    return dict(app_config=app_config)


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", current_user=current_user)


@app.route("/menu")
def menu():
    return render_template("menu.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Utilisateur ou mot de passe invalide")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for("index"))
    return render_template("login.html", title="Connexion", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if current_user.username != "admin":
        return redirect(url_for("logout"))
    if "cat" in request.args.keys():
        category = request.args["cat"]
    else:
        category = None
    if category == "users_add":
        form = UserAddForm()
        if form.validate_on_submit():
            userlist = form.userlist.data
            userlist = userlist.splitlines()
            document = Document()
            for user in userlist:
                u = User()
                u.name = user.replace("\n\r", "").strip()
                u.username = user.strip().replace(" ", "_").replace("\n\r", "")
                letters = string.ascii_lowercase
                password = "".join(random.choice(letters) for i in range(10))
                u.set_password(password)
                document.add_paragraph(f"{u.username} : {password}")
                db.session.add(u)
                db.session.commit()
            document.save("/tmp/Liste.docx")
            return send_file(
                "/tmp/Liste.docx",
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                attachment_filename="Liste.docx",
                as_attachment=True,
            )
        return render_template("admin.html", category=category, form=form)
    elif category == "users_del":
        if request.method == "POST":
            for user in request.form:
                to_delete = db.session.query(User).filter(User.username == user).first()
                db.session.delete(to_delete)
            db.session.commit()
        userlist = [u for u in User.query.filter(User.username != "admin").all()]
        return render_template("admin.html", category=category, userlist=userlist)
    elif category == "export":
        if request.method == "GET":
            return render_template(
                "admin.html", category=category, periods=calendar.periods
            )
        else:
            if "period" not in request.form.keys():
                flash("Veuillez sélectionner une période")
                return render_template(
                    "admin.html", category=category, periods=calendar.periods
                )
            if "booking_type" not in request.form.keys():
                flash("Veuillez sélectionner un type de réservation")
                return render_template(
                    "admin.html", category=category, periods=calendar.periods
                )
            period = int(request.form.get("period"))
            date_begin = arrow.get(calendar.periods[period]["begin"], "YYYYMMDD")
            date_end = arrow.get(calendar.periods[period]["end"], "YYYYMMDD")
            data = {}
            booking = CATEGORIES[request.form.get("booking_type")].query.all()
            for db_line in booking:
                for date_str in db_line.booked.split():
                    date = arrow.get(date_str, "YYYYMMDD")
                    if date_begin < date < date_end:
                        date_string = date.format("YYYY-MM-DD")
                        if date_string not in data.keys():
                            data[date_string] = []
                        data[date_string].append(db_line.username)
            if data == {}:
                flash("Aucune donnée pour la période demandée")
                return render_template(
                    "admin.html", category=category, periods=calendar.periods
                )
            create_xls(data)
            return send_file("/tmp/workbook.xlsx")
    elif category == "configuration":
        if request.method == "GET":
            data = db.session.query(Configuration).order_by("config_order")
            return render_template("admin.html", category=category, data=data)
        elif request.method == "POST":
            for item in request.form:
                c = (
                    db.session.query(Configuration)
                    .filter(Configuration.config_key == item)
                    .first()
                )
                c.value = request.form.get(item)
                db.session.commit()
                if item in ["mail_cantine_time", "mail_garderie_time"]:
                    hour, minute = c.value.split(":")
                    conf_name = c.config_key.replace("_time", "")
                    m = (
                        db.session.query(Configuration)
                        .filter(Configuration.config_key == conf_name)
                        .first()
                    )
                    args = {}
                    args["mail_list"] = m.value.split()
                    if arrow.now().isoweekday() == 5:
                        day = arrow.now().shift(days=+3).format("YYYYMMDD")
                    else:
                        day = arrow.now().shift(days=+1).format("YYYYMMDD")
                    args["day"] = day
                    if "cantine" in item:
                        booked = []
                        data = db.session.query(BookingCantine)
                        for d in data.all():
                            if day in d.booked:
                                booked.append(d.username)
                        args["book_cantine"] = booked
                    elif "garderie" in item:
                        booked = {}
                        data = db.session.query(BookingGarderieMatin)
                        book = []
                        for d in data.all():
                            if day in d.booked:
                                book.append(d.username)
                        booked["Garderie Matin"] = book
                        data = db.session.query(BookingGarderieSoir)
                        book = []
                        for d in data.all():
                            if day in d.booked:
                                book.append(d.username)
                        booked["Garderie Soir"] = book
                        args["book_garderie"] = booked

    return render_template("admin.html")


@app.route("/booking", methods=["GET"])
@login_required
def booking():
    category = request.args["cat"]
    booking_type = CATEGORIES[category]
    booked = getBookedData(booking_type, current_user.name)
    current_week = arrow.utcnow().isocalendar()[1]
    if "garderie" in category:
        category = "garderie"
    return render_template(
        "booking.html",
        name=current_user.name,
        calendar=calendar.calendar,
        booked=booked,
        booking_type=category,
        current_week=current_week,
    )


@app.route("/booking", methods=["POST"])
@login_required
def savebooking():
    today = int(arrow.now().strftime("%Y%m%d"))
    category = request.args["cat"]
    booking_type = CATEGORIES[category]
    booked = getBookedData(booking_type, current_user.name)
    if "selectall" in request.form.keys():
        data = []
        for week in calendar.calendar:
            for day in calendar.calendar[week]:
                print(day)
                if category == "cantine":
                    if day["bookable_cantine"]:
                        print("ajouter cantine", day["date"])
                        data.append(day["date"])
                elif category == "garderie_matin" or category == "garderie_soir":
                    if day["bookable_garderie"]:
                        print("ajouter garderie", category, day["date"])
                        data.append(day["date"])
    elif "selectnone" in request.form.keys():
        data = []
    else:
        data = [k for k in request.form.keys()]
    if "garderie" in category:
        delay = 1
    else:
        delay = 2
    for day in booked:
        if int(day) < today + delay:
            data.append(day)
    data = " ".join(sorted(data))
    if category == "cantine":
        new_data = BookingCantine(username=current_user.name, booked=data)
    elif category == "garderie_matin":
        new_data = BookingGarderieMatin(username=current_user.name, booked=data)
    elif category == "garderie_soir":
        new_data = BookingGarderieSoir(username=current_user.name, booked=data)
    q = db.session.execute(
        f'SELECT * FROM booking_{category} WHERE username = "{current_user.name}";'
    )
    results = [v for v in q.fetchall()]
    if len(results) != 0:
        update_data = f'UPDATE booking_{category} SET booked = "{data}" WHERE username = "{current_user.name}"'
        db.session.execute(update_data)
    else:
        db.session.add(new_data)
    db.session.commit()
    return redirect("/booking?cat=%s" % category)


@app.route("/booking_admin", methods=["GET"])
@login_required
def booking_admin():
    if current_user != "admin":
        redirect("/logout")
    userlist = [u.name for u in User.query.filter(User.username != "admin").all()]
    if "user" not in request.args.keys():
        selected_user = None
    else:
        selected_user = request.args["user"]
    if "cat" not in request.args.keys():
        category = "cantine"
    else:
        category = request.args["cat"]
    if not selected_user:
        return render_template(
            "booking_admin.html",
            selected_user=selected_user,
            booking_type=category,
            userlist=userlist,
        )
    else:
        booked = getBookedData(CATEGORIES[category], selected_user)
        current_week = arrow.utcnow().isocalendar()[1]
        return render_template(
            "booking_admin.html",
            selected_user=selected_user,
            calendar=calendar.calendar,
            booking_type=category,
            current_week=current_week,
            booked=booked,
            userlist=userlist,
        )


@app.route("/booking_admin", methods=["POST"])
@login_required
def savebooking_admin():
    if current_user != "admin":
        redirect("/logout")
    category = request.args["cat"]
    user = request.args["user"]
    booking_type = CATEGORIES[category]
    data = [k for k in request.form.keys()]
    data = " ".join(sorted(data))
    new_data = booking_type(username=user, booked=data)
    q = db.session.execute(
        f'SELECT * FROM booking_{category} WHERE username = "{user}";'
    )
    results = [v for v in q.fetchall()]
    if len(results) != 0:
        update_data = (
            f'UPDATE booking_{category} SET booked = "{data}" WHERE username = "{user}"'
        )
        db.session.execute(update_data)
    else:
        db.session.add(new_data)
    db.session.commit()
    return redirect("/booking_admin?cat=%s&user=%s" % (category, user))
