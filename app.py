from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import mimetypes
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yoursecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ambulance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
db = SQLAlchemy(app)

mimetypes.add_type('application/javascript', '.js')

login_manager = LoginManager(app)
login_manager.login_view = 'ambulance_login'


# ---------- MODELS ----------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='client')


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(255))
    condition = db.Column(db.String(255))
    lat = db.Column(db.Float)   # client location
    lon = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    accepted = db.Column(db.Boolean, default=False)
    finished = db.Column(db.Boolean, default=False)
    ambulance_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    amb_lat = db.Column(db.Float)   # ambulance GPS
    amb_lon = db.Column(db.Float)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------- ROUTES ----------
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

    new_req = Request(address=address, condition=condition, lat=lat, lon=lon)
    db.session.add(new_req)
    db.session.commit()

    return jsonify({"message": "Request saved successfully", "request_id": new_req.id})


@app.route('/get_locations')
def get_locations():
    req_id = request.args.get("request_id", type=int)
    if not req_id:
        return jsonify({})

    req = Request.query.get(req_id)
    if req and req.accepted and not req.finished:
        # 🚑 Dummy ambulance location = PGH coords
        amb_lat, amb_lon = 14.578056, 120.985556  
        return jsonify({
            "ambulance": {
                "lat": amb_lat,
                "lon": amb_lon
            },
            "client": {
                "lat": req.lat,
                "lon": req.lon
            },
            "accepted": True
        })
    return jsonify({"accepted": False})


@app.route('/location_update', methods=['POST'])
@login_required
def location_update():
    if current_user.role != "ambulance":
        return jsonify({"error": "Not authorized"}), 403

    data = request.json or {}
    lat = data.get("lat")
    lon = data.get("lon")
    if lat is None or lon is None:
        return jsonify({"error": "Missing lat/lon"}), 400

    # Find the active request assigned to this ambulance
    req = Request.query.filter_by(ambulance_id=current_user.id, finished=False, accepted=True).first()
    if req:
        req.amb_lat = float(lat)
        req.amb_lon = float(lon)
        db.session.commit()

    return jsonify({"status": "ok"})



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


@app.route('/ambulance/sw.js')
def ambulance_sw():
    return send_from_directory('static/ambulance', 'sw.js', mimetype='application/javascript')


@app.route('/client/sw.js')
def client_sw():
    return send_from_directory('static/client', 'sw.js', mimetype='application/javascript')


@app.route('/api/requests')
@login_required
def api_requests():
    if current_user.role != 'ambulance':
        return jsonify([])
    # ❌ old: Request.query.order_by(Request.timestamp.desc()).all()
    reqs = Request.query.filter_by(finished=False).order_by(Request.timestamp.desc()).all()
    data = []
    for r in reqs:
        data.append({
            "id": r.id,
            "address": r.address,
            "condition": r.condition,
            "lat": r.lat,
            "lon": r.lon,
            "timestamp": r.timestamp.isoformat(),
            "accepted": r.accepted
        })
    return jsonify(data)


@app.route('/accept_request/<int:req_id>', methods=['POST'])
@login_required
def accept_request(req_id):
    if current_user.role != "ambulance":
        return jsonify({"error": "Not authorized"}), 403

    req = Request.query.get_or_404(req_id)
    req.accepted = True
    req.ambulance_id = current_user.id

    # DO NOT set req.amb_lat = req.lat  <-- don't do this
    db.session.commit()
    return jsonify({"message": "Request accepted"})


@app.route('/finish_request/<int:req_id>', methods=['POST'])
@login_required
def finish_request(req_id):
    if current_user.role != "ambulance":
        return jsonify({"error": "Not authorized"}), 403

    req = Request.query.get_or_404(req_id)
    req.finished = True
    db.session.commit()
    return jsonify({"message": "Request finished"})


@app.route('/favicon.ico')
def favicon():
    if "ambulance" in request.referrer or "ambulance" in request.headers.get("Referer", ""):
        return send_from_directory(
            os.path.join(app.root_path, "static", "ambulance"),
            "ambulance.ico", mimetype="image/vnd.microsoft.icon"
        )
    else:
        return send_from_directory(
            os.path.join(app.root_path, "static", "client"),
            "client.ico", mimetype="image/vnd.microsoft.icon"
        )


if __name__ == '__main__':
    app.run(debug=True)
