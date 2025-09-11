from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yoursecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ambulance.db'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'ambulance_login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='client')

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(255))
    condition = db.Column(db.String(255))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return redirect(url_for('client_page'))

@app.route('/client')
def client_page():
    return render_template('client/index.html')

@app.route('/request_ambulance', methods=['POST'])
def request_ambulance():
    data = request.get_json(force=True)
    address = data.get('address')
    condition = data.get('condition')
    lat = data.get('lat')
    lon = data.get('lon')
    if not address or not condition or lat is None or lon is None:
        return jsonify({"message": "Missing data"}), 400

    new_req = Request(
        address=address,
        condition=condition,
        lat=lat,
        lon=lon
    )
    db.session.add(new_req)
    db.session.commit()

    return jsonify({"message": "Request saved successfully"})

@app.route('/get_locations')
def get_locations():
    # to-do Replace with real ambulance tracking logic#
    # For now, just return the latest requests as "ambulance locations"
    requests = Request.query.order_by(Request.timestamp.desc()).limit(5).all()
    ambulances = {}
    for r in requests:
        ambulances[r.id] = {
            "lat": r.lat,
            "lon": r.lon
        }
    return jsonify({"ambulances": ambulances})


@app.route('/ambulance')
@login_required
def ambulance_page():
    if current_user.role != "ambulance":
        return redirect(url_for('client_page'))
    requests = Request.query.order_by(Request.timestamp.desc()).all()
    return render_template('ambulance/index.html', requests=requests)

@app.route('/ambulance/login', methods=['GET', 'POST'])
def ambulance_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user and user.role == 'ambulance':
            login_user(user)
            return redirect(url_for('ambulance_page'))
        flash('Invalid credentials or not ambulance role')
    return render_template('ambulance/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('client_page'))

@app.route('/api/requests')
@login_required
def api_requests():
    if current_user.role != 'ambulance':
        return jsonify([])
    reqs = Request.query.order_by(Request.timestamp.desc()).all()
    data = []
    for r in reqs:
        data.append({
            "id": r.id,
            "address": r.address,
            "condition": r.condition,
            "lat": r.lat,
            "lon": r.lon,
            "timestamp": r.timestamp.isoformat()
        })
    return jsonify(data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default ambulance user if not exists
        if not User.query.filter_by(username='ambulance1').first():
            db.session.add(User(username='ambulance1', password='1234', role='ambulance'))
            db.session.commit()
    app.run(debug=True)
