from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import math

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# DB Setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ambulance Driver account
class Driver(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Location data
class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {"lat": self.lat, "lon": self.lon}
    
@login_manager.user_loader
def load_user(user_id):
    return Driver.query.get(int(user_id))


# -------------- Authentication Routes ---------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password, method='sha256')

        if Driver.query.filter_by(username=username).first():
            flash("Username Already Exists", "error")
            return redirect(url_for('register'))
        
        new_driver = Driver(username=username, password=hashed_pw)
        db.session.add(new_driver)
        db.session.commit()
        flash("Account Created. Please Log In.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        driver = Driver.query.filter_by(username=username).first()
        if driver and check_password_hash(driver.password, password):
            login_user(driver)
            flash("Logged In Successfully", "success")
            return redirect(url_for('home'))
        flash('Invalid Credentials', 'danger')
    return render_template('login.html')
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged Out", "info")
    return redirect(url_for('login'))

# ---------------- Core ----------------

@app.route('/location_update', methods=['POST'])
def location_update():
    data = request.json
    user_id = data['user_id']
    role = data['role']

    # Ambulance driver must be logged in
    if role == "ambulance":
        if not current_user.is_authenticated:
            return jsonify({"error": "Login required for ambulance updates"}), 403 
        user_id = f"Driver-{current_user.username}" 

    loc = Location.query.filter_by(user_id=user_id, role=role).first()
    if loc:
        loc.lat = data['lat']
        loc.lon = data['lon']
    else:
        loc = Location(user_id=user_id, role=role, lat=data['lat'], lon=data['lon'])
        db.session.add(loc)
    db.session.commit()
    return ("", 204)

@app.route('/get_locations', methods=['GET'])
def get_locations():
    ambulances = {l.user_id: l.to_dict() for l in Location.query.filter_by(role="ambulance")}
    clients = {l.user_id: l.to_dict() for l in Location.query.filter_by(role="client")}
    return jsonify({"ambulances": ambulances, "clients": clients})

@app.route('/dispatch_message')
def dispatch_message():
    clients = Location.query.filter_by(role='client').all()
    ambulances = Location.query.filter_by(role='ambulance').all()

    messages = []
    for c in clients:
        nearest, min_dist = None, float("inf")
        for a in ambulances:
            dist = math.dist((c.lat, c.lon), (a.lat, a.lon))
            if dist < min_dist:
                min_dist = dist
                nearest = a.user_id
        if nearest:
            messages.append({"message": f"Ambulance {nearest} is nearest to Client {c.user_id} (~{round(min_dist*111,1)} km)."})
    
    return jsonify(messages)

@app.route('/')
def home():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)