from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    current_user,
    login_required,
    UserMixin,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ambulance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "ambulance_login"

# ---------------------- MODELS ---------------------- #
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20))  # 'ambulance' or 'client'


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(200), nullable=False)
    condition = db.Column(db.String(200), nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------- LOGIN LOADER ---------------------- #
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------- CLIENT ROUTES ---------------------- #
@app.route("/client/request", methods=["GET", "POST"])
def client_request():
    if request.method == "POST":
        address = request.form.get("address")
        condition = request.form.get("condition")
        lat = request.form.get("lat")
        lon = request.form.get("lon")
        if address and condition:
            new_req = Request(
                address=address,
                condition=condition,
                lat=float(lat) if lat else None,
                lon=float(lon) if lon else None,
            )
            db.session.add(new_req)
            db.session.commit()
            flash("Request submitted successfully!", "success")
            return redirect(url_for("client_request"))
        else:
            flash("Please fill out all fields.", "error")
    return render_template("client/index.html")


# ---------------------- AMBULANCE LOGIN/REGISTER ---------------------- #
@app.route("/ambulance/login", methods=["GET", "POST"])
def ambulance_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username, role="ambulance").first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("ambulance_page"))
        flash("Invalid credentials", "error")
    return render_template("ambulance/login.html")


@app.route("/ambulance/register", methods=["GET", "POST"])
def ambulance_register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username, role="ambulance").first():
            flash("Username already exists", "error")
            return redirect(url_for("ambulance_register"))
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role="ambulance")
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("ambulance_login"))
    return render_template("ambulance/register.html")


@app.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("client_request"))


# ---------------------- AMBULANCE MAP ---------------------- #
@app.route("/ambulance")
@login_required
def ambulance_page():
    if current_user.role != "ambulance":
        flash("Unauthorized access", "error")
        return redirect(url_for("client_request"))
    requests_list = Request.query.order_by(Request.timestamp.desc()).all()
    return render_template("ambulance/index.html", requests=requests_list)


# ---------------------- LOCATION UPDATE ---------------------- #
@app.route("/location_update", methods=["POST"])
@login_required
def location_update():
    data = request.get_json()
    if not data:
        return "", 400
    lat = data.get("lat")
    lon = data.get("lon")
    loc = Location.query.filter_by(user_id=current_user.id).first()
    if loc:
        loc.lat = lat
        loc.lon = lon
        loc.timestamp = datetime.utcnow()
    else:
        loc = Location(user_id=current_user.id, lat=lat, lon=lon)
        db.session.add(loc)
    db.session.commit()
    return "", 204


# ---------------------- GET LOCATIONS ---------------------- #
@app.route("/get_locations")
def get_locations():
    ambulances = {}
    for loc in Location.query.all():
        ambulances[loc.user_id] = {"lat": loc.lat, "lon": loc.lon}
    return jsonify({"ambulances": ambulances})


# ---------------------- HOME ---------------------- #
@app.route("/")
def home():
    return redirect(url_for("client_request"))


# ---------------------- INIT DB COMMAND ---------------------- #
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
