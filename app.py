import random
import string
from datetime import datetime
from flask import Flask, render_template, request, jsonify, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
import os
from functools import wraps

# Initialize the Flask app
app = Flask(__name__)

# Configurations for the application and database
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://bastian:18222053@localhost:5432/pawm?options=-csearch_path%3dpublic"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "supersecretkey")
app.config["SESSION_TYPE"] = "filesystem"

# Initialize session and database
db = SQLAlchemy(app)
Session(app)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# User model remains the same
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)

# Define materials
MATERIALS = [
    "muatan_dan_gaya_listrik", "medan_listrik", "energi_potensial_listrik",
    "kapasitor", "medan_magnetik", "biot_savart",
    "ampere_law", "rangkaian_rlc", "interferensi_gelombang", "teori_relativity"
]

class UserState(db.Model):
    __tablename__ = 'user_states'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    material = db.Column(db.String(50), nullable=False)  # Added material field
    quiz_score = db.Column(db.Integer, nullable=True)
    simulation_results = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to user
    user = db.relationship('User', backref='user_states', lazy=True)

# Dynamic model creation for Latihan and Praktikum
for material in MATERIALS:
    latihan_table_name = f"Latihan_{material}"
    praktikum_table_name = f"Praktikum_{material}"

    # Define Latihan model
    LatihanModel = type(
        latihan_table_name,
        (db.Model, ),
        {
            "__tablename__": latihan_table_name.lower(),
            "id": db.Column(db.String(4), primary_key=True, default=lambda: ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))),
            "user_id": db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False),
            "material": db.Column(db.String(50), nullable=False),
            "score": db.Column(db.Integer, default=0),
            "timestamp": db.Column(db.DateTime, default=datetime.utcnow),
            "__table_args__": ({'extend_existing': True},)
        }
    )
    globals()[latihan_table_name] = LatihanModel

    # Define Praktikum model
    PraktikumModel = type(
        praktikum_table_name,
        (db.Model, ),
        {
            "__tablename__": praktikum_table_name.lower(),
            "id": db.Column(db.String(4), primary_key=True, default=lambda: ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))),
            "user_id": db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False),
            "material": db.Column(db.String(50), nullable=False),
            "conclusion": db.Column(db.Text, nullable=True),
            "timestamp": db.Column(db.DateTime, default=datetime.utcnow),
            "__table_args__": ({'extend_existing': True},)
        }
    )
    globals()[praktikum_table_name] = PraktikumModel

# Function to sync data between tables
def sync_user_state(user_id, material):
    """
    Sync data from Latihan and Praktikum tables to UserState
    """
    # Get the appropriate model classes
    latihan_class = globals().get(f"Latihan_{material}")
    praktikum_class = globals().get(f"Praktikum_{material}")
    
    # Get the latest entries
    latihan = latihan_class.query.filter_by(user_id=user_id, material=material).first()
    praktikum = praktikum_class.query.filter_by(user_id=user_id, material=material).first()
    
    # Get or create UserState entry
    user_state = UserState.query.filter_by(user_id=user_id, material=material).first()
    if not user_state:
        user_state = UserState(user_id=user_id, material=material)
        db.session.add(user_state)
    
    # Update UserState
    if latihan:
        user_state.quiz_score = latihan.score
    if praktikum:
        user_state.simulation_results = praktikum.conclusion
    
    # Check if both latihan and praktikum are completed
    user_state.completed = bool(latihan and praktikum and 
                              latihan.score is not None and 
                              praktikum.conclusion is not None)
    
    db.session.commit()
    return user_state

# Modified submit_material_progress function
@app.route('/submit_material_progress', methods=['POST'])
@login_required
def submit_material_progress():
    data = request.get_json()
    
    if not data or 'material' not in data:
        return jsonify({"error": "No material specified"}), 400
        
    material = data['material']
    is_praktikum = data.get('is_praktikum', False)
    user_id = session['user_id']
    
    try:
        if is_praktikum:
            # Handle praktikum submission
            conclusion = data.get('conclusion')
            if conclusion:
                praktikum_class = globals().get(f"Praktikum_{material}")
                praktikum = praktikum_class.query.filter_by(user_id=user_id, material=material).first()
                if not praktikum:
                    praktikum = praktikum_class(user_id=user_id, material=material)
                    db.session.add(praktikum)
                praktikum.conclusion = conclusion
        else:
            # Handle latihan submission
            score = data.get('score')
            if score is not None:
                latihan_class = globals().get(f"Latihan_{material}")
                latihan = latihan_class.query.filter_by(user_id=user_id, material=material).first()
                if not latihan:
                    latihan = latihan_class(user_id=user_id, material=material)
                    db.session.add(latihan)
                latihan.score = score
        
        db.session.commit()
        
        # Sync the data to UserState
        user_state = sync_user_state(user_id, material)
        
        return jsonify({
            "message": "Progress updated successfully",
            "quiz_score": user_state.quiz_score,
            "simulation_results": user_state.simulation_results,
            "completed": user_state.completed
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/progress_data', methods=['GET'])
@login_required
def progress_data():
    user_id = session['user_id']
    progress, overall_progress = get_user_progress(user_id)
    return jsonify({
        "progress": progress,
        "overall_progress": overall_progress
    })

# Function to get user progress for all materials
def get_user_progress(user_id):
    progress = {}
    total_completed = 0
    
    for material in MATERIALS:
        user_state = UserState.query.filter_by(user_id=user_id, material=material).first()
        if user_state:
            progress[material] = {
                "completed": user_state.completed,
                "quiz_score": user_state.quiz_score,
                "simulation_results": user_state.simulation_results
            }
            if user_state.completed:
                total_completed += 1
        else:
            progress[material] = {
                "completed": False,
                "quiz_score": None,
                "simulation_results": None
            }
    
    overall_progress = (total_completed / len(MATERIALS)) * 100 if MATERIALS else 0
    return progress, overall_progress

# Login, sign_up, change_password routes remain unchanged, as you requested

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Both username and password are required"}), 400

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return jsonify({"redirect": url_for('home')})
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    return render_template('login page.html')

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        if not email or not username or len(username) < 3 or not password or len(password) < 6:
            return jsonify({"error": "Invalid input data"}), 400

        if User.query.filter((User.username == username) | (User.email == email)).first():
            return jsonify({"error": "Username or email already exists"}), 400

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User created successfully", "redirect": url_for('login')}), 201

    return render_template('sign in page.html')

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'GET':
        return render_template('change_password.html')

    data = request.get_json() if request.is_json else request.form
    email = data.get("email")
    new_password = data.get("new_password")
    validation_password = data.get("validation_password")

    if not email or not new_password or not validation_password or new_password != validation_password:
        return jsonify({"error": "Invalid input"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
    db.session.commit()
    return jsonify({"message": "Password changed successfully"}), 200

# The rest of the app routes, including sidebar and material pages, remain the same.
@app.route('/home', methods=['GET'])
@login_required
def home():
    user_id = session['user_id']
    progress, overall_progress = get_user_progress(user_id)
    return render_template('home_page.html', progress=progress, overall_progress=overall_progress, MATERIALS=MATERIALS)



@app.route('/sidebar')
@login_required
def sidebar():
    return render_template('sidebar.html')

@app.route('/sidebar_kosong')
@login_required
def sidebar_kosong():
    return render_template('sidebar_kosong.html')

@app.route('/latihan/<material>', methods=['GET'])
@login_required
def latihan(material):
    if material not in MATERIALS:
        return jsonify({"error": "Invalid material"}), 400
    return render_template(f'{material}_latihan.html', material=material)

@app.route('/praktikum/<material>', methods=['GET'])
@login_required
def praktikum(material):
    if material not in MATERIALS:
        return jsonify({"error": "Invalid material"}), 400
    return render_template(f'{material}_praktikum.html', material=material)

@app.route('/')
def index():
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This will create the tables based on the models

    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
