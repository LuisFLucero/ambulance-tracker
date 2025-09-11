from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'ambulance_login'  # default login for protected routes


# ---------------- MODELS ----------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref=db.backref('locations', lazy=True))


class Request(db.Model):  # for client requests
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(200), nullable=False)
    condition = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())


# ---------------- LOGIN MANAGER ----------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return redirect(url_for('client_redirect'))


# 🚑 Ambulance login/register
@app.route('/ambulance/login', methods=['GET', 'POST'])
def ambulance_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username, role="ambulance").first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('ambulance_home'))

        flash('Invalid credentials', 'error')

    return render_template("ambulance/login.html")


@app.route('/ambulance/register', methods=['GET', 'POST'])
def ambulance_register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username, role="ambulance").first():
            flash('Username already exists', 'error')
            return redirect(url_for('ambulance_register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role="ambulance")
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('ambulance_login'))

    return render_template("ambulance/register.html")


# Logout
@app.route('/logout')
@login_required
def logout():
    role = current_user.role
    logout_user()
    flash("You have been logged out.", "info")
    if role == 'ambulance':
        return redirect(url_for('ambulance_login'))
    return redirect(url_for('client_request'))


# ---------------- CLIENT ROUTES ----------------

@app.route('/client')
def client_redirect():
    """Redirects /client → /client/request"""
    return redirect(url_for('client_request'))


@app.route('/client/request', methods=['GET', 'POST'])
def client_request():
    if request.method == 'POST':
        address = request.form.get('address')
        condition = request.form.get('condition')

        if address and condition:
            new_request = Request(address=address, condition=condition)
            db.session.add(new_request)
            db.session.commit()
            flash("Request submitted successfully!", "success")
            return redirect(url_for('client_request'))
        else:
            flash("Please fill out all fields.", "error")

    return render_template("client/index.html")


# ---------------- AMBULANCE HOME ----------------

@app.route('/ambulance')
@login_required
def ambulance_home():
    if current_user.role != 'ambulance':
        flash('Unauthorized access', 'error')
        return redirect(url_for('client_request'))

    requests = Request.query.order_by(Request.timestamp.desc()).all()
    return render_template("ambulance/index.html", requests=requests)


# ---------------- STATIC/PWA ROUTES ----------------

# Client PWA
@app.route('/client/manifest.json')
def client_manifest():
    return send_from_directory('static/client', 'manifest.json')

@app.route('/client/sw.js')
def client_sw():
    return send_from_directory('static/client', 'sw.js')


# Ambulance PWA
@app.route('/ambulance/manifest.json')
def ambulance_manifest():
    return send_from_directory('static/ambulance', 'manifest.json')

@app.route('/ambulance/sw.js')
def ambulance_sw():
    return send_from_directory('static/ambulance', 'sw.js')


# ---------------- RUN APP ----------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
