from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from urllib.parse import unquote
import os
import json
import requests
from urllib.parse import urlencode
import base64
from datetime import datetime, timedelta
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import secrets


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Google OAuth Configuration
GOOGLE_CLIENT_ID = "your_google_client_id_here"  # Replace with your actual Google Client ID
GOOGLE_CLIENT_SECRET = "your_google_client_secret_here"  # Replace with your actual Google Client Secret
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid_connect_json_web_keyset"

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Only for development

db = SQLAlchemy(app)

SPOTIFY_CLIENT_ID = '6b770d2f043948dc9515d3a5f65a5113'
SPOTIFY_CLIENT_SECRET = 'bbf02678958948eda30ff6bc0e616058'
SPOTIFY_REDIRECT_URI = 'http://localhost:5000/callback'
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE = 'https://api.spotify.com/v1'

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    survey_completed = db.Column(db.Boolean, default=False)
    cycle_length = db.Column(db.Integer, default=28)  # Added to store user's cycle length
    period_length = db.Column(db.Integer, default=5)  # Added to store user's period length

    # Relationship to track history
    entries = db.relationship('PainEntry', backref='user', lazy=True)
    routines = db.relationship('CustomRoutine', backref='user', lazy=True)

class PainEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    pain_level = db.Column(db.String(20))
    flow_level = db.Column(db.String(20))
    mood = db.Column(db.String(20))
    symptoms = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class CustomRoutine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    poses = db.Column(db.Text, nullable=False)  # JSON string of pose names
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class SurveyResponse(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    q1_age = db.Column(db.Integer)
    q2_last_period = db.Column(db.Date)
    q3_period_duration = db.Column(db.String(30))
    q4_cycle_length = db.Column(db.String(30))
    q5_period_regularity = db.Column(db.String(30))
    q6_hair_growth = db.Column(db.String(10))
    q7_acne = db.Column(db.String(10))
    q8_hair_thinning = db.Column(db.String(10))
    q9_weight_gain = db.Column(db.String(30))
    q10_sugar_craving = db.Column(db.String(10))
    q11_family_history = db.Column(db.String(30))
    q12_fertility = db.Column(db.String(30))
    q13_mood_swings = db.Column(db.String(30))

class DailyCheckIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    check_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    login_time = db.Column(db.Time, default=datetime.utcnow().time())
    checkin_time = db.Column(db.Time, nullable=True)
    is_checked_in = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship back to user
    user = db.relationship('User', backref=db.backref('checkins', lazy=True))
    
    # Ensure one check-in per user per day
    __table_args__ = (db.UniqueConstraint('user_id', 'check_date', name='_user_date_checkin'),)

with app.app_context():
    db.create_all()

# Spotify configuration
SPOTIFY_CLIENT_ID = '6b770d2f043948dc9515d3a5f65a5113'
SPOTIFY_CLIENT_SECRET = 'bbf02678958948eda30ff6bc0e616058'
SPOTIFY_REDIRECT_URI = 'http://localhost:5000/callback'
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
    
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.full_name
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        is_new_signup = 'is_new_signup' in request.form  # Check for new signup

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(full_name=full_name, email=email, password=hashed_password, survey_completed=False)

        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Log the user in automatically
            session['user_id'] = new_user.id
            session['user_name'] = new_user.full_name
            
            # Redirect to survey for new signups, dashboard otherwise
            if is_new_signup:
                flash('Account created! Please complete our quick survey.', 'success')
                return redirect(url_for('survey'))
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('Email already registered!', 'danger')
            return redirect(url_for('signup'))

    return render_template('signup.html')

# Google OAuth Routes
@app.route('/auth/google')
def google_login():
    """Initiate Google OAuth login"""
    try:
        # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost:5000/auth/google/callback"]
                }
            },
            scopes=["openid", "email", "profile"]
        )
        
        flow.redirect_uri = url_for('google_callback', _external=True)
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        # Store state in session for verification
        session['state'] = state
        
        return redirect(authorization_url)
        
    except Exception as e:
        flash(f'Error initiating Google login: {str(e)}', 'danger')
        return redirect(url_for('login'))

@app.route('/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        # Verify state parameter
        if request.args.get('state') != session.get('state'):
            flash('Invalid state parameter', 'danger')
            return redirect(url_for('login'))
        
        # Create flow instance
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost:5000/auth/google/callback"]
                }
            },
            scopes=["openid", "email", "profile"],
            state=session['state']
        )
        
        flow.redirect_uri = url_for('google_callback', _external=True)
        
        # Get authorization response
        authorization_response = request.url
        flow.fetch_token(authorization_response=authorization_response)
        
        # Get user info from Google
        credentials = flow.credentials
        request_session = google_requests.Request()
        
        # Verify the token and get user info
        idinfo = id_token.verify_oauth2_token(
            credentials.id_token, request_session, GOOGLE_CLIENT_ID
        )
        
        # Extract user information
        google_id = idinfo.get('sub')
        email = idinfo.get('email')
        name = idinfo.get('name')
        picture = idinfo.get('picture')
        
        if not email:
            flash('Unable to get email from Google account', 'danger')
            return redirect(url_for('login'))
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if user:
            # User exists, log them in
            session['user_id'] = user.id
            session['user_name'] = user.full_name
            flash('Successfully logged in with Google!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Create new user
            new_user = User(
                full_name=name or 'Google User',
                email=email,
                password=generate_password_hash(secrets.token_urlsafe(32), method='pbkdf2:sha256'),  # Random password
                survey_completed=False
            )
            
            try:
                db.session.add(new_user)
                db.session.commit()
                
                # Log the user in automatically
                session['user_id'] = new_user.id
                session['user_name'] = new_user.full_name
                
                flash('Account created successfully with Google! Please complete our quick survey.', 'success')
                return redirect(url_for('survey'))
                
            except Exception as e:
                db.session.rollback()
                flash('Error creating account. Email might already be registered.', 'danger')
                return redirect(url_for('login'))
        
    except Exception as e:
        flash(f'Error during Google authentication: {str(e)}', 'danger')
        return redirect(url_for('login'))

@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            # Get the date string from the form (format: "d MMM yyyy" like "15 Jun 2023")
            last_period_str = request.form.get('q2')
            
            # Parse the date string into a date object
            try:
                last_period = datetime.strptime(last_period_str, '%d %b %Y').date()
            except ValueError:
                # Try alternative format if the first one fails
                try:
                    last_period = datetime.strptime(last_period_str, '%Y-%m-%d').date()
                except ValueError as e:
                    flash(f'Invalid date format: {last_period_str}. Please use the calendar picker.', 'danger')
                    return redirect(url_for('survey'))            # Debug print all form data
            print("Form data received:", request.form)
            
            new_response = SurveyResponse(
                user_id=session['user_id'],
                q1_age=request.form.get('q1', type=int),
                q2_last_period=last_period,
                q3_period_duration=request.form.get('q3'),
                q4_cycle_length=request.form.get('q4'),
                q5_period_regularity=request.form.get('q5'),
                q6_hair_growth=request.form.get('q6'),
                q7_acne=request.form.get('q7'),
                q8_hair_thinning=request.form.get('q8'),
                q9_weight_gain=request.form.get('q9'),
                q10_sugar_craving=request.form.get('q10'),
                q11_family_history=request.form.get('q11'),
                q12_fertility=request.form.get('q12'),
                q13_mood_swings=request.form.get('q13')
            )

            user.survey_completed = True
            db.session.add(new_response)
            db.session.commit()

            flash('Thank you for completing the survey!', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error saving survey responses: {str(e)}. Please check all fields and try again.', 'danger')
            print("Error details:", str(e))
            return redirect(url_for('survey'))

    return render_template('survey.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if not user.survey_completed:
        flash('Please complete the survey first!', 'warning')
        return redirect(url_for('survey'))

    # ⬇️ Fetch latest survey response
    survey = SurveyResponse.query.filter_by(user_id=user.id).order_by(SurveyResponse.timestamp.desc()).first()

    if not survey or not survey.q2_last_period:
        flash('Survey data is missing or incomplete.', 'warning')
        return redirect(url_for('survey'))

    # Calculate cycle day and phase
    today = datetime.utcnow().date()
    days_since_period = (today - survey.q2_last_period).days
    current_day = (days_since_period % user.cycle_length) + 1 if days_since_period >= 0 else 0

    if current_day <= user.period_length:
        current_phase = "Menstrual"
    elif current_day <= (user.cycle_length - 14):
        current_phase = "Follicular"
    elif current_day <= (user.cycle_length - 9):
        current_phase = "Ovulation"
    else:
        current_phase = "Luteal"    # Generate survey stats for the chart
    survey_stats = {}
    if survey:
        survey_stats = {
            "Irregular Periods": 70 if survey.q5_period_regularity == 'No' else 0,
            "Excessive Hair": 60 if survey.q6_hair_growth == 'Yes' else 0,
            "Acne": 55 if survey.q7_acne == 'Yes' else 0,
            "Hair Thinning": 45 if survey.q8_hair_thinning == 'Yes' else 0,
            "Weight Gain": 50 if survey.q9_weight_gain == 'Yes' else 0,
            "Sugar Cravings": 65 if survey.q10_sugar_craving == 'Yes' else 0,
            "Family History": 40 if survey.q11_family_history == 'Yes' else 0,
            "Fertility Issues": 35 if survey.q12_fertility == 'Yes' else 0,
            "Mood Swings": 75 if survey.q13_mood_swings == 'Yes' else 0
        }

    return render_template(
        'index.html',
        user_name=session['user_name'],
        current_day=current_day,
        current_phase=current_phase,
        cycle_length=user.cycle_length,
        period_length=user.period_length,
        survey_stats=survey_stats
    )    
# Period Tracker Page (Only for logged-in users)
pain_mapping = {'No Pain': 0, 'Mild': 3, 'Moderate': 5, 'Severe': 10}
flow_mapping = {'None': 0, 'Light': 2, 'Medium': 5, 'Heavy': 8}

try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "menstrualcyclelen.json")
    print("Loading JSON from:", json_path)

    with open(json_path, "r") as f:
        data = json.load(f)
except FileNotFoundError as e:
    print("File not found:", e)
    data = {}  # Or maybe you want to crash intentionally with raise e
except Exception as e:
    print("Unexpected error loading JSON:", e)
    data = {}


# ------------------------ Helper: Predict Cycle ------------------------
def predict_cycle(start_date_str, cycle_length):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    next_period = start_date + timedelta(days=cycle_length)
    ovulation_start = next_period - timedelta(days=14)
    ovulation_end = ovulation_start + timedelta(days=5)

    return {
        "next_period": next_period.strftime("%Y-%m-%d"),
        "ovulation_window": [
            ovulation_start.strftime("%Y-%m-%d"),
            ovulation_end.strftime("%Y-%m-%d")
        ]
    }

# ------------------------ Main Route ------------------------

@app.route('/period_tracker', methods=['GET', 'POST'])
def period_tracker():
    if request.method == 'POST':
        start_date_str = request.form.get('start_date')  # This should now be a valid string
        if not start_date_str:
            return "Start date is required", 400

        # Convert string to datetime object
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

        # Get other form data
        flow = request.form.get('flow')
        symptoms = request.form.getlist('symptoms')
        emotions = request.form.getlist('emotions')
        notes = request.form.get('notes')

        # Calculate next period date (example logic: 28-day cycle)
        next_period_date = start_date + timedelta(days=28)

        return render_template('tracker_result.html',
                               start_date=start_date_str,
                               next_period_date=next_period_date.strftime('%Y-%m-%d'),
                               flow=flow,
                               symptoms=symptoms,
                               emotions=emotions,
                               notes=notes)

    return render_template('period_tracker.html')


# ------------------------ Separate API Route (Optional) ------------------------
@app.route('/predict_cycle', methods=['POST'])
def cycle_predict():
    start_date = request.form['start_date']
    cycle_length = int(request.form['cycle_length'])
    prediction = predict_cycle(start_date, cycle_length)
    return jsonify(prediction)


@app.route('/nutrition')
def nutrition():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('Nutrition.html')


@app.route('/index')
def index():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('index (1).html')

@app.route('/about')
def about():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('about.html')



@app.route('/yoga')
def yoga():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('yoga.html', user_name=session['user_name'])

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('admin.html', user_name=session['user_name'])

@app.route('/consultation')
def consultation():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('consultation.html', user_name=session['user_name'])

@app.route('/store')
def store():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('store.html', user_name=session['user_name'])
#===========================================================================================================


@app.route('/mood')
def mood():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('mood.html', user_name=session['user_name'])

@app.route('/education')
def education():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('education.html', user_name=session['user_name'])

# Add this function to check Spotify token status
def is_spotify_token_valid():
    if 'spotify_token_expiry' not in session:
        return False
    return datetime.now() < session['spotify_token_expiry']

# Update the spotify_login route
@app.route('/spotify_login')
def spotify_login():
    """Redirect user to Spotify authorization page"""
    scope = 'user-read-private user-read-email playlist-read-private playlist-modify-public playlist-modify-private'
    
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': scope,
        'show_dialog': True
    }
    
    auth_url = f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"
    return redirect(auth_url)

# Update the callback route
@app.route('/callback')
def spotify_callback():
    if 'error' in request.args:
        flash('Spotify authorization failed: ' + request.args['error'], 'error')
        return redirect(url_for('dashboard'))
    
    if 'code' in request.args:
        code = request.args['code']
        
        # Prepare the authorization header
        auth_header = base64.b64encode(
            f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Exchange code for access token
        auth_response = requests.post(SPOTIFY_TOKEN_URL, data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': SPOTIFY_REDIRECT_URI,
        }, headers=headers)
        
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            
            # Store tokens in session with expiry time
            session['spotify_access_token'] = auth_data['access_token']
            if 'refresh_token' in auth_data:
                session['spotify_refresh_token'] = auth_data['refresh_token']
            
            # Set token expiry time (1 hour from now)
            session['spotify_token_expiry'] = datetime.now() + timedelta(seconds=auth_data.get('expires_in', 3600))
            
            # Get user profile to store display name
            profile_response = requests.get(
                f"{SPOTIFY_API_BASE}/me",
                headers={'Authorization': f"Bearer {auth_data['access_token']}"}
            )
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                session['spotify_display_name'] = profile_data.get('display_name', 'Spotify User')
            
            flash('Successfully connected with Spotify!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Failed to connect with Spotify. Please try again.', 'error')
            return redirect(url_for('dashboard'))
    
    return redirect(url_for('dashboard'))

# Update the refresh token route
@app.route('/refresh_token')
def refresh_token():
    if 'spotify_refresh_token' not in session:
        return jsonify({"error": "No refresh token"}), 401
    
    # Prepare the authorization header
    auth_header = base64.b64encode(
        f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()
    
    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    refresh_response = requests.post(SPOTIFY_TOKEN_URL, data={
        'grant_type': 'refresh_token',
        'refresh_token': session['spotify_refresh_token'],
    }, headers=headers)
    
    if refresh_response.status_code == 200:
        refresh_data = refresh_response.json()
        session['spotify_access_token'] = refresh_data['access_token']
        session['spotify_token_expiry'] = datetime.now() + timedelta(seconds=refresh_data.get('expires_in', 3600))
        
        # Spotify may not return a new refresh token, so we keep the existing one
        if 'refresh_token' in refresh_data:
            session['spotify_refresh_token'] = refresh_data['refresh_token']
        
        return jsonify({"access_token": refresh_data['access_token']})
    else:
        return jsonify({"error": "Failed to refresh token"}), 400

# Enhanced get_mood_playlist route
@app.route('/get_mood_playlist', methods=['POST'])
def get_mood_playlist():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401
    
    # Check if we need to refresh the token
    if not is_spotify_token_valid() and 'spotify_refresh_token' in session:
        refresh_response = refresh_token()
        if refresh_response.status_code != 200:
            session.pop('spotify_access_token', None)
            session.pop('spotify_refresh_token', None)
            session.pop('spotify_token_expiry', None)
            return jsonify({'error': 'Spotify session expired. Please reconnect.'}), 401
    
    if 'spotify_access_token' not in session:
        return jsonify({'error': 'Spotify not connected'}), 401
    
    data = request.get_json()
    mood = data.get('mood')
    intensity = data.get('intensity', 3)  # Default to medium intensity
    
    if not mood:
        return jsonify({'error': 'Mood not specified'}), 400
    
    # Enhanced mood to playlist mapping
    mood_playlists = {
        'happy': {
            1: {'id': '37i9dQZF1DXdPec7aLTmlC', 'name': 'Happy Hits', 'description': 'Light and cheerful tunes'},
            2: {'id': '37i9dQZF1DX3rxVfibe1L0', 'name': 'Mood Booster', 'description': 'Songs to lift your spirits'},
            3: {'id': '37i9dQZF1DX0XUsuxWHRQd', 'name': 'RapCaviar', 'description': 'High-energy hip-hop'},
            4: {'id': '37i9dQZF1DX4dyzvuaRJ0n', 'name': 'mint', 'description': 'Fresh dance and electronic'},
            5: {'id': '37i9dQZF1DX4SBhb3fqCJd', 'name': 'Are & Be', 'description': 'The best in R&B right now'}
        },
        'sad': {
            1: {'id': '37i9dQZF1DX7qK8ma5wgG1', 'name': 'Sad Songs', 'description': 'Gentle melancholic melodies'},
            2: {'id': '37i9dQZF1DWVV27DiNWxkR', 'name': 'Sad Indie', 'description': 'Indie songs for rainy days'},
            3: {'id': '37i9dQZF1DX3YSRoSdA634', 'name': 'Life Sucks', 'description': 'Emo and alternative for tough times'},
            4: {'id': '37i9dQZF1DX3YSRoSdA634', 'name': 'Life Sucks', 'description': 'Emo and alternative for tough times'},
            5: {'id': '37i9dQZF1DX3YSRoSdA634', 'name': 'Life Sucks', 'description': 'Emo and alternative for tough times'}
        },
        'angry': {
            1: {'id': '37i9dQZF1DX0vHZ8elq0UK', 'name': 'Rock This', 'description': 'Classic rock anthems'},
            2: {'id': '37i9dQZF1DX1s9knjP51Oa', 'name': 'Calm Vibes', 'description': 'Soothing instrumental music'},
            3: {'id': '37i9dQZF1DX4sWSpwq3LiO', 'name': 'Rock Classics', 'description': 'Legendary rock tracks'},
            4: {'id': '37i9dQZF1DX5wgkQjaJeZO', 'name': 'Thrash Metal', 'description': 'High-intensity metal'},
            5: {'id': '37i9dQZF1DX5wgkQjaJeZO', 'name': 'Thrash Metal', 'description': 'High-intensity metal'}
        },
        'energetic': {
            1: {'id': '37i9dQZF1DX9tPFwDMOaN1', 'name': 'Energy Booster', 'description': 'Upbeat tracks to get you moving'},
            2: {'id': '37i9dQZF1DX76Wlfdnj7AP', 'name': 'Beast Mode', 'description': 'High-energy workout music'},
            3: {'id': '37i9dQZF1DX0XUsuxWHRQd', 'name': 'RapCaviar', 'description': 'The hottest hip-hop tracks'},
            4: {'id': '37i9dQZF1DX8f6LHxMjnzD', 'name': 'Punk Rock', 'description': 'Fast and furious punk anthems'},
            5: {'id': '37i9dQZF1DX8f6LHxMjnzD', 'name': 'Punk Rock', 'description': 'Fast and furious punk anthems'}
        },
        'content': {
            1: {'id': '37i9dQZF1DX4WYpdgoIcn6', 'name': 'Chill Hits', 'description': 'Relaxed vibes for easy listening'},
            2: {'id': '37i9dQZF1DX4WYpdgoIcn6', 'name': 'Chill Hits', 'description': 'Relaxed vibes for easy listening'},
            3: {'id': '37i9dQZF1DWU0ScTcjJBdj', 'name': 'Relax & Unwind', 'description': 'Soothing sounds to calm your mind'},
            4: {'id': '37i9dQZF1DWU0ScTcjJBdj', 'name': 'Relax & Unwind', 'description': 'Soothing sounds to calm your mind'},
            5: {'id': '37i9dQZF1DWU0ScTcjJBdj', 'name': 'Relax & Unwind', 'description': 'Soothing sounds to calm your mind'}
        }
    }
    
    # Get the appropriate playlist based on mood and intensity
    playlist_info = mood_playlists.get(mood.lower(), {}).get(int(intensity), None)
    
    if not playlist_info:
        return jsonify({'error': 'No playlist found for this mood'}), 404
    
    # Get playlist details from Spotify
    headers = {
        'Authorization': f"Bearer {session['spotify_access_token']}"
    }
    
    try:
        # Get playlist details
        playlist_url = f"{SPOTIFY_API_BASE}/playlists/{playlist_info['id']}"
        response = requests.get(playlist_url, headers=headers)
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to get playlist from Spotify'}), 500
        
        playlist_data = response.json()
        
        # Get a few sample tracks
        tracks_url = f"{SPOTIFY_API_BASE}/playlists/{playlist_info['id']}/tracks?limit=5"
        tracks_response = requests.get(tracks_url, headers=headers)
        tracks_data = tracks_response.json() if tracks_response.status_code == 200 else {'items': []}
        
        sample_tracks = []
        for item in tracks_data.get('items', [])[:3]:
            track = item.get('track', {})
            artists = ", ".join([artist['name'] for artist in track.get('artists', [])])
            sample_tracks.append({
                'name': track.get('name', 'Unknown Track'),
                'artists': artists,
                'preview_url': track.get('preview_url')
            })
        
        return jsonify({
            'playlist_id': playlist_info['id'],
            'playlist_name': playlist_info['name'],
            'playlist_description': playlist_info['description'],
            'playlist_url': playlist_data.get('external_urls', {}).get('spotify', ''),
            'playlist_image': playlist_data.get('images', [{}])[0].get('url', ''),
            'tracks': playlist_data.get('tracks', {}).get('total', 0),
            'sample_tracks': sample_tracks,
            'owner': playlist_data.get('owner', {}).get('display_name', 'Spotify')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add this route to check Spotify connection status
@app.route('/check_spotify_status')
def check_spotify_status():
    if 'spotify_access_token' in session and is_spotify_token_valid():
        return jsonify({
            'connected': True,
            'display_name': session.get('spotify_display_name', 'Spotify User')
        })
    return jsonify({'connected': False})
#=======================================================================================================================



@app.route('/chatbot')
def chatbot():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('chatbot.html')

@app.route('/api/get-api-key')
def get_api_key():
    print("GEMINI KEY:", os.getenv("GEMINI_API_KEY"))
    api_key = os.getenv('GEMINI_API_KEY')
    print("DEBUG: Loaded API Key =", api_key)  # Add this for verification
    if not api_key:
        abort(500, description="API key not configured on server")
    return jsonify({'apiKey': api_key})

    
@app.route('/api/get-prompt-template')
def get_prompt_template():
    try:
        with open('templates/prompt_template.txt', 'r') as file:
            return file.read()
    except FileNotFoundError:
        abort(404, description="Prompt template not found")
    except Exception as e:
        abort(500, description=str(e))
        
@app.route('/settings')
def settings():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    survey = SurveyResponse.query.filter_by(user_id=user.id).order_by(SurveyResponse.timestamp.desc()).first()
    
    return render_template('settings.html', 
                         user_name=user.full_name,
                         email=user.email,
                         cycle_length=user.cycle_length,
                         period_length=user.period_length,
                         survey=survey)

# Add these new routes to app.py

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        user.full_name = request.form.get('full_name', user.full_name)
        db.session.commit()
        session['user_name'] = user.full_name  # Update session name
        return jsonify({'success': True, 'message': 'Profile updated'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/update_cycle_settings', methods=['POST'])
def update_cycle_settings():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        cycle_length = request.form.get('cycle_length', type=int)
        period_length = request.form.get('period_length', type=int)
        
        if cycle_length and 20 <= cycle_length <= 45:  # Validate reasonable range
            user.cycle_length = cycle_length
        if period_length and 1 <= period_length <= 14:  # Validate reasonable range
            user.period_length = period_length
            
        db.session.commit()
        return jsonify({'success': True, 'message': 'Cycle settings updated'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/update_period_dates', methods=['POST'])
def update_period_dates():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        
        # Find or create a survey response for this user
        survey = SurveyResponse.query.filter_by(user_id=session['user_id']).order_by(SurveyResponse.timestamp.desc()).first()
        if not survey:
            survey = SurveyResponse(user_id=session['user_id'])
            db.session.add(survey)
        
        survey.q2_last_period = start_date
        survey.q3_period_duration = f"{(end_date - start_date).days + 1} days"
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Period dates updated'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/get_user_settings')
def get_user_settings():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    survey = SurveyResponse.query.filter_by(user_id=user.id).order_by(SurveyResponse.timestamp.desc()).first()
    
    return jsonify({
        'full_name': user.full_name,
        'email': user.email,
        'cycle_length': user.cycle_length,
        'period_length': user.period_length,
        'last_period': survey.q2_last_period.strftime('%Y-%m-%d') if survey and survey.q2_last_period else None,
        'period_duration': survey.q3_period_duration if survey else None,
        'cycle_regularity': survey.q5_period_regularity if survey else None,
        'symptoms': survey.q13_mood_swings if survey else None,
        'hormonal_conditions': survey.q11_family_history if survey else None  # Using this field as example
    })
    
@app.route('/update_survey_answers', methods=['POST'])
def update_survey_answers():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        survey = SurveyResponse.query.filter_by(user_id=user.id).order_by(SurveyResponse.timestamp.desc()).first()
        if not survey:
            survey = SurveyResponse(user_id=user.id)
            db.session.add(survey)
        
        # Update fields based on form data
        if 'cycle_regularity' in request.form:
            survey.q5_period_regularity = request.form['cycle_regularity']
        
        if 'cycle_length' in request.form:
            try:
                cycle_length = int(request.form['cycle_length'])
                if 20 <= cycle_length <= 45:  # Validate range
                    user.cycle_length = cycle_length
                else:
                    return jsonify({'error': 'Cycle length must be between 20-45 days'}), 400
            except ValueError:
                return jsonify({'error': 'Invalid cycle length'}), 400
        
        if 'symptoms' in request.form:
            survey.q13_mood_swings = request.form['symptoms']
        
        if 'hormonal_conditions' in request.form:
            # Add this field to your SurveyResponse model if needed
            pass
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Survey answers updated'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'message': 'Failed to save changes'}), 500

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('home'))

#=====================================================================================
def load_recipes():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, 'static', 'data', 'recipes.json')
        
        with open(json_path) as f:
            data = json.load(f)
            return {recipe['name'].lower(): recipe for recipe in data['remedies']}
    except Exception as e:
        print(f"Error loading recipes: {str(e)}")
        return {}

recipes = load_recipes()

@app.route('/remedy/<path:remedy_name>')
def remedy_details(remedy_name):
    try:
        # Load recipes data from the correct path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, 'static', 'data', 'recipes.json')
        
        with open(json_path, 'r') as f:
            data = json.load(f)
            remedies = data.get('remedies', [])
            
        # Normalize the remedy name for comparison
        decoded_name = unquote(remedy_name).strip().lower()
        
        # Find the matching remedy
        found_remedy = None
        for remedy in remedies:
            if remedy.get('name', '').strip().lower() == decoded_name:
                found_remedy = remedy
                break
        
        if not found_remedy:
            # Try alternative matching if exact match not found
            for remedy in remedies:
                if decoded_name in remedy.get('name', '').strip().lower():
                    found_remedy = remedy
                    break
        
        if found_remedy:
            return render_template('remedy.html', remedy=found_remedy)
        else:
            # Render a user-friendly fallback
            return render_template('remedy.html', remedy={
                "name": remedy_name,
                "description": "Sorry, this remedy was not found.",
                "ingredients": [],
                "steps": [],
                "benefits": [],
                "image": url_for('static', filename='images/default-remedy.png')
            })
            
    except Exception as e:
        print(f"Error loading remedy: {str(e)}")
        return render_template('remedy.html', remedy={
            "name": "Error",
            "description": "An error occurred while loading this remedy.",
            "ingredients": [],
            "steps": [],
            "benefits": [],
            "image": url_for('static', filename='images/default-remedy.png')
        })

@app.route('/remedies')
def all_remedies():
    try:
        # Load recipes data from the correct path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, 'static', 'data', 'recipes.json')
        
        with open(json_path, 'r') as f:
            data = json.load(f)
            remedies = data.get('remedies', [])
            
        return render_template('remedy.html', remedies=remedies)
        
    except Exception as e:
        print(f"Error loading all remedies: {str(e)}")
        return render_template('remedy.html', remedies=[])

@app.route('/api/get-yoga-recommendations', methods=['POST'])
def get_yoga_recommendations():
    try:
        data = request.get_json()
        symptoms = data.get('symptoms', [])
        yoga_data = data.get('yogaData', [])
        
        # yoga_data should be an array directly
        asanas = yoga_data if isinstance(yoga_data, list) else []
        
        # Normalize symptoms for robust matching
        normalized_symptoms = [s.strip().lower() for s in symptoms]
        recommendations = []
        
        print(f"Yoga symptoms: {symptoms}")
        print(f"Normalized symptoms: {normalized_symptoms}")
        
        for asana in asanas:
            relieves = asana.get('relievesSymptoms', [])
            normalized_relieves = [r.strip().lower() for r in relieves]
            
            print(f"Asana: {asana.get('name', 'Unknown')} | Relieves: {normalized_relieves}")
            
            if any(symptom in normalized_relieves for symptom in normalized_symptoms):
                recommendations.append(asana)
                print(f"MATCHED: {asana.get('name', 'Unknown')}")
        
        print(f"Total yoga recommendations: {len(recommendations)}")
        
        return jsonify({
            'success': True,
            'recommendations': {
                'yogaAsanas': recommendations
            }
        })
    except Exception as e:
        print(f"Error in get_yoga_recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/get-ayurvedic-recommendations', methods=['POST'])
def get_ayurvedic_recommendations():
    try:
        data = request.get_json()
        symptoms = data.get('symptoms', [])
        recipes_data = data.get('recipesData', {})
        
        # Extract the remedies array from the data structure
        remedies = recipes_data.get('remedies', []) if isinstance(recipes_data, dict) else recipes_data
        
        # Normalize symptoms for robust matching
        normalized_symptoms = [s.strip().lower() for s in symptoms]
        recommendations = []
        
        print(f"Symptoms: {symptoms}")
        print(f"Normalized symptoms: {normalized_symptoms}")
        
        for remedy in remedies:
            # Check both 'category' (list or string) and 'badge' (string)
            categories = remedy.get('category', [])
            badge = remedy.get('badge', '')
              # Normalize
            if isinstance(categories, str):
                categories = [categories]
            normalized_categories = [c.strip().lower() for c in categories]
            normalized_badge = badge.strip().lower()
            print(f"Remedy: {remedy.get('name', 'Unknown')} | Badge: {normalized_badge} | Categories: {normalized_categories}")
              # Match if any symptom matches category or badge
            if any(symptom in normalized_categories for symptom in normalized_symptoms) or \
               any(symptom == normalized_badge for symptom in normalized_symptoms):
                recommendations.append(remedy)
                print(f"MATCHED: {remedy.get('name', 'Unknown')}")
        
        print(f"Total recommendations: {len(recommendations)}")
        
        return jsonify({
            'success': True,
            'recommendations': {
                'ayurvedicRemedies': recommendations
            }
        })
    except Exception as e:
        print(f"Error in get_ayurvedic_recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/get-recommendations', methods=['POST'])
def get_gemini_recommendations():
    try:
        # Debug: Check if API key exists
        api_key = os.getenv('GEMINI_API_KEY')
        print(f"API Key exists: {'Yes' if api_key else 'No'}")
        
        if not api_key:
            print("ERROR: GEMINI_API_KEY environment variable not found")
            return jsonify({
                'success': False,
                'message': 'API key not configured. Please check your GEMINI_API_KEY environment variable in Render.'
            }), 500
            
        data = request.get_json()
        prompt = data.get('prompt', '')
        symptoms = data.get('symptoms', [])
        
        if not prompt:
            return jsonify({
                'success': False,
                'message': 'No prompt provided'
            }), 400
            
        # Gemini API URL
        url = f'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={api_key}'
        
        # Request payload
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature': 0.7,
                'topK': 40,
                'topP': 0.95,
                'maxOutputTokens': 2048,
            }
        }
        
        # Make request to Gemini API
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'message': f'Gemini API error: {response.status_code} - {response.text}'
            }), 500
            
        result = response.json()
        
        if not result.get('candidates') or not result['candidates'][0].get('content'):
            return jsonify({
                'success': False,
                'message': 'Invalid response from Gemini API'
            }), 500
            
        gemini_response = result['candidates'][0]['content']['parts'][0]['text']
          # Try to parse as JSON
        try:
            parsed_response = json.loads(gemini_response)
            return jsonify({
                'success': True,
                'recommendations': parsed_response
            })
        except json.JSONDecodeError:
            # If not valid JSON, return as text
            return jsonify({
                'success': True,
                'recommendations': {
                    'text': gemini_response
                }
            })
            
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'message': 'API request timed out. Please try again.'
        }), 500
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'message': f'Network error: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

# Static file routes for JSON data
@app.route('/data/yoga.json')
def serve_yoga_data():
    try:
        yoga_file_path = os.path.join(app.static_folder, 'data', 'yoga.json')
        with open(yoga_file_path, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({'error': 'Yoga data not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/recipes.json')
def serve_recipes_data():
    try:
        recipes_file_path = os.path.join(app.static_folder, 'data', 'recipes.json')
        with open(recipes_file_path, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({'error': 'Recipes data not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ======================= YOGA ROUTINES API ROUTES =======================

@app.route('/api/routines', methods=['GET'])
def get_routines():
    """Get all routines (from routines.json + user's custom routines)"""
    try:
        # Load routines from routines.json
        base_dir = os.path.dirname(os.path.abspath(__file__))
        routines_path = os.path.join(base_dir, 'routines.json')
        
        featured_routines = []
        if os.path.exists(routines_path):
            with open(routines_path, 'r') as f:
                featured_routines = json.load(f)
          # Load user's custom routines (use default user if not logged in for testing)
        custom_routines = []
        user_id = session.get('user_id', 1)  # Default to user_id=1 for testing
        if user_id:
            user_custom_routines = CustomRoutine.query.filter_by(user_id=user_id).all()
            custom_routines = [
                {
                    'name': routine.name,
                    'description': routine.description or 'Custom routine',
                    'poses': json.loads(routine.poses),
                    'custom': True,
                    'created_at': routine.created_at.isoformat()
                }
                for routine in user_custom_routines
            ]
        
        # Combine featured and custom routines
        all_routines = featured_routines + custom_routines
        return jsonify(all_routines)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/routines', methods=['POST'])
def create_custom_routine():
    """Create a new custom routine"""
    # For testing: use a default user if not logged in
    user_id = session.get('user_id', 1)  # Default to user_id=1 for testing
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Routine name is required'}), 400
        if not data.get('poses') or len(data['poses']) == 0:
            return jsonify({'error': 'At least one pose is required'}), 400
        
        # Create new custom routine
        new_routine = CustomRoutine(
            name=data['name'],
            description=data.get('description', 'Custom routine'),
            poses=json.dumps(data['poses']),  # Store poses as JSON string
            user_id=user_id
        )
        
        db.session.add(new_routine)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Routine "{data["name"]}" created successfully!',
            'routine': {
                'name': new_routine.name,
                'description': new_routine.description,
                'poses': json.loads(new_routine.poses),
                'custom': True,
                'created_at': new_routine.created_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/routines/<routine_name>', methods=['DELETE'])
def delete_custom_routine(routine_name):
    """Delete a custom routine"""
    # For testing: use a default user if not logged in
    user_id = session.get('user_id', 1)  # Default to user_id=1 for testing
    
    try:
        # Find the custom routine by name and user_id
        routine = CustomRoutine.query.filter_by(name=routine_name, user_id=user_id).first()
        
        if not routine:
            return jsonify({'error': 'Routine not found or you do not have permission to delete it'}), 404
        
        # Delete the routine
        db.session.delete(routine)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Routine "{routine_name}" deleted successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/exercises', methods=['GET'])
def get_exercises():
    """Get all available exercises from exercise.json"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        exercises_path = os.path.join(base_dir, 'exercise.json')
        
        if os.path.exists(exercises_path):
            with open(exercises_path, 'r') as f:
                exercises = json.load(f)
            return jsonify(exercises)
        else:
            return jsonify({'error': 'Exercises file not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/exercise')
def exercise():
    """Render the exercise page"""
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('exercise.html', user_name=session['user_name'])

# ======================= DAILY CHECK-IN API ROUTES =======================

@app.route('/api/checkin/data', methods=['GET'])
def get_checkin_data():
    """Get user's check-in data for the current week"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        user_id = session['user_id']
        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday())  # Monday of current week
        week_end = week_start + timedelta(days=6)  # Sunday of current week
        
        # Get all check-ins for the current week
        checkins = DailyCheckIn.query.filter(
            DailyCheckIn.user_id == user_id,
            DailyCheckIn.check_date >= week_start,
            DailyCheckIn.check_date <= week_end
        ).all()
        
        # Get total login count
        total_logins = DailyCheckIn.query.filter_by(user_id=user_id).count()
        
        # Calculate current streak
        current_streak = 0
        check_date = today
        while True:
            daily_checkin = DailyCheckIn.query.filter_by(
                user_id=user_id,
                check_date=check_date
            ).first()
            
            if daily_checkin and daily_checkin.is_checked_in:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        
        # Format check-in data
        checkin_data = {}
        for checkin in checkins:
            date_str = checkin.check_date.strftime('%Y-%m-%d')
            checkin_data[date_str] = {
                'date': date_str,
                'loginTime': checkin.login_time.strftime('%H:%M:%S') if checkin.login_time else None,
                'checkinTime': checkin.checkin_time.strftime('%H:%M:%S') if checkin.checkin_time else None,
                'checkedIn': checkin.is_checked_in
            }
        
        return jsonify({
            'checkins': checkin_data,
            'totalLogins': total_logins,
            'currentStreak': current_streak
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/checkin/login', methods=['POST'])
def record_login():
    """Record user login for today"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        user_id = session['user_id']
        today = datetime.utcnow().date()
        current_time = datetime.utcnow().time()
        
        # Check if login already recorded for today
        existing_checkin = DailyCheckIn.query.filter_by(
            user_id=user_id,
            check_date=today
        ).first()
        
        if not existing_checkin:
            # Create new check-in record
            new_checkin = DailyCheckIn(
                user_id=user_id,
                check_date=today,
                login_time=current_time,
                is_checked_in=False
            )
            db.session.add(new_checkin)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Login recorded',
                'isNewLogin': True
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Login already recorded',
                'isNewLogin': False
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/checkin/daily', methods=['POST'])
def daily_checkin():
    """Record daily check-in"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        user_id = session['user_id']
        today = datetime.utcnow().date()
        current_time = datetime.utcnow().time()
        
        # Find or create today's check-in record
        checkin_record = DailyCheckIn.query.filter_by(
            user_id=user_id,
            check_date=today
        ).first()
        
        if not checkin_record:
            # Create new record if doesn't exist
            checkin_record = DailyCheckIn(
                user_id=user_id,
                check_date=today,
                login_time=current_time,
                is_checked_in=False
            )
            db.session.add(checkin_record)
        
        # Update check-in status
        if not checkin_record.is_checked_in:
            checkin_record.is_checked_in = True
            checkin_record.checkin_time = current_time
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Daily check-in completed!',
                'checkinTime': current_time.strftime('%H:%M:%S')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Already checked in today',
                'checkinTime': checkin_record.checkin_time.strftime('%H:%M:%S')
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ======================= END YOGA ROUTINES API ROUTES =======================


            
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
