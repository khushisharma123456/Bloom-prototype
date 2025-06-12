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

# Load environment variables (prioritize system env vars over .env file)
try:
    from dotenv import load_dotenv
    # Only load .env if we're in development (not on Render)
    if not os.getenv('RENDER'):  # Render sets this environment variable
        load_dotenv()
except ImportError:
    # If python-dotenv is not installed, environment variables should be set manually
    pass


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

class SymptomEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    entry_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    flow_level = db.Column(db.String(20))  # light, medium, heavy
    mood = db.Column(db.String(20))  # happy, neutral, sad, anxious, irritable
    pain_level = db.Column(db.Integer)  # 0-10 scale
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship back to user
    user = db.relationship('User', backref=db.backref('symptom_entries', lazy=True))
    
    # Ensure one symptom entry per user per day
    __table_args__ = (db.UniqueConstraint('user_id', 'entry_date', name='_user_date_symptom'),)

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
        current_phase = "Luteal"

    # Generate survey stats for the chart
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

@app.route('/personalised-yoga')
def personalised_yoga():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('personalised-yoga.html', user_name=session['user_name'])

@app.route('/personalised-remdy')
def personalised_remdy():
    if 'user_id' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('login'))
    return render_template('personalised-remdy.html', user_name=session['user_name'])

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
    
    user = User.query.get(session['user_id'])
    survey = SurveyResponse.query.filter_by(user_id=user.id).order_by(SurveyResponse.timestamp.desc()).first()
    
    # Generate survey stats for the chart
    survey_stats = {}
    has_survey_data = False
    if survey:
        has_survey_data = True
        survey_stats = {
            "Irregular Periods": 70 if survey.q5_period_regularity == 'Irregular' or survey.q5_period_regularity == 'Missed' else 0,
            "Excessive Hair": 60 if survey.q6_hair_growth == 'Yes' else 0,
            "Acne": 55 if survey.q7_acne == 'Yes' else 0,
            "Hair Thinning": 45 if survey.q8_hair_thinning == 'Yes' else 0,
            "Weight Gain": 50 if survey.q9_weight_gain == 'Yes' else 0,
            "Sugar Cravings": 65 if survey.q10_sugar_craving == 'Yes' else 0,
            "Family History": 40 if survey.q11_family_history == 'Yes' else 0,
            "Fertility Issues": 35 if survey.q12_fertility == 'Yes' else 0,
            "Mood Swings": 75 if survey.q13_mood_swings == 'Yes' else 0
        }
    
    return render_template('education.html', 
                         user_name=session['user_name'],
                         survey_stats=survey_stats,
                         has_survey_data=has_survey_data,
                         survey=survey)

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

@app.route('/save_symptom_entry', methods=['POST'])
def save_symptom_entry():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        data = request.get_json()
        user_id = session['user_id']
        today = datetime.utcnow().date()
        
        # Check if entry already exists for today
        existing_entry = SymptomEntry.query.filter_by(
            user_id=user_id, 
            entry_date=today
        ).first()
        
        if existing_entry:
            # Update existing entry
            existing_entry.flow_level = data.get('flow_level')
            existing_entry.mood = data.get('mood')
            existing_entry.pain_level = data.get('pain_level')
            existing_entry.notes = data.get('notes', '')
            existing_entry.updated_at = datetime.utcnow()
        else:
            # Create new entry
            new_entry = SymptomEntry(
                user_id=user_id,
                entry_date=today,
                flow_level=data.get('flow_level'),
                mood=data.get('mood'),
                pain_level=data.get('pain_level'),
                notes=data.get('notes', '')
            )
            db.session.add(new_entry)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Symptoms saved successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'message': 'Failed to save symptoms'}), 500

@app.route('/get_symptom_entry')
def get_symptom_entry():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        user_id = session['user_id']
        today = datetime.utcnow().date()
        
        entry = SymptomEntry.query.filter_by(
            user_id=user_id, 
            entry_date=today
        ).first()
        
        if entry:
            return jsonify({
                'success': True,
                'data': {
                    'flow_level': entry.flow_level,
                    'mood': entry.mood,
                    'pain_level': entry.pain_level,
                    'notes': entry.notes,
                    'date': entry.entry_date.isoformat()
                }
            })
        else:
            return jsonify({'success': True, 'data': None})
            
    except Exception as e:
        return jsonify({'error': str(e), 'message': 'Failed to get symptoms'}), 500

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
        # Decode URL-encoded name
        decoded_name = unquote(remedy_name)
        
        # Load recipes
        json_path = os.path.join(app.static_folder, 'data', 'recipes.json')
        if not os.path.exists(json_path):
            abort(404, description="Recipes data not found")
            
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Find matching remedy (case-insensitive)
        found_remedy = None
        for remedy in data.get('remedies', []):
            if remedy.get('name', '').lower() == decoded_name.lower():
                found_remedy = remedy
                break
        
        if not found_remedy:
            abort(404, description=f"Remedy '{decoded_name}' not found")
            
        # Ensure image path is correct
        if 'image' in found_remedy and found_remedy['image'].startswith('/static/'):
            found_remedy['image'] = found_remedy['image'][7:]  # Remove '/static' prefix
            
        return render_template('remedy.html', remedy=found_remedy)
        
    except json.JSONDecodeError:
        abort(500, description="Invalid recipes data format")
    except Exception as e:
        abort(500, description=str(e))
        
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
        
        # If no recommendations found from JSON data, use the symptom-specific database
        if len(recommendations) == 0:
            print("No matches in JSON data, using symptom-specific database...")
            fallback_recommendations = get_symptom_specific_yoga(symptoms)
            recommendations = fallback_recommendations.get('yogaAsanas', [])
            print(f"Fallback recommendations: {len(recommendations)}")
        
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
        if api_key:
            print(f"API Key (first 20 chars): {api_key[:20]}...")
        
        if not api_key:
            print("ERROR: GEMINI_API_KEY environment variable not found")
            is_render = os.getenv('RENDER')
            error_message = (
                'API key not configured. Please check your GEMINI_API_KEY environment variable in Render.'
                if is_render else
                'API key not configured. Please set GEMINI_API_KEY in your .env file or environment variables.'
            )
            return jsonify({
                'success': False,
                'message': error_message
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
        print(f"Making request to Gemini API...")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 400:
            error_data = response.json().get('error', {})
            if 'API Key' in error_data.get('message', ''):
                # If in development and API key is invalid, return mock data
                if not os.getenv('RENDER'):
                    print("Using mock data for development...")
                    # Check if this is an Ayurvedic request based on prompt content
                    if 'ayurvedic' in prompt.lower() or 'ayurveda' in prompt.lower():
                        mock_response = get_symptom_specific_ayurveda(symptoms)
                    else:
                        mock_response = get_symptom_specific_yoga(symptoms)
                    return jsonify({
                        'success': True,
                        'recommendations': mock_response
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid API key. Please check your GEMINI_API_KEY in Render environment variables.'
                    }), 400
                
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
        
        # Debug: Print the raw Gemini response
        print("=== RAW GEMINI RESPONSE ===")
        print(gemini_response)
        print("=== END RAW RESPONSE ===")
        
        # Try to parse as JSON
        try:
            parsed_response = json.loads(gemini_response)
            print("=== PARSED JSON RESPONSE ===")
            print(json.dumps(parsed_response, indent=2))
            print("=== END PARSED RESPONSE ===")
            return jsonify({
                'success': True,
                'recommendations': parsed_response
            })
        except json.JSONDecodeError as e:
            print(f"=== JSON DECODE ERROR ===")
            print(f"Error: {e}")
            print("=== USING MOCK DATA INSTEAD ===")
            # If JSON parsing fails, use mock data
            if 'ayurvedic' in prompt.lower() or 'ayurveda' in prompt.lower():
                mock_response = get_symptom_specific_ayurveda(symptoms)
            else:
                mock_response = get_symptom_specific_yoga(symptoms)
            return jsonify({
                'success': True,
                'recommendations': mock_response
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

# ======================= YOUTUBE SHORTS FETCH API =======================

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')  # Set this in your environment variables
YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'

def fetch_youtube_short(exercise_name):
    if not YOUTUBE_API_KEY:
        return None
    params = {
        'part': 'snippet',
        'q': f"{exercise_name} exercise short",
        'type': 'video',
        'maxResults': 1,
        'videoDuration': 'short',
        'key': YOUTUBE_API_KEY
    }
    try:
        resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)
        if resp.status_code == 200:
            items = resp.json().get('items', [])
            if items:
                return items[0]['id']['videoId']
        return None
    except Exception as e:
        print(f"YouTube fetch error: {e}")
        return None

@app.route('/api/exercise_videos', methods=['GET'])
def get_exercise_videos():
    """Return exercise list with YouTube Shorts video IDs"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        exercises_path = os.path.join(base_dir, 'exercise.json')
        with open(exercises_path, 'r') as f:
            exercises = json.load(f)  # This is a list

        result = []
        for ex in exercises:
            video_id = fetch_youtube_short(ex.get('name', ''))
            ex['youtube_video_id'] = video_id
            result.append(ex)

        return jsonify({'exercises': result})
    except Exception as e:
        print("Error in /api/exercise_videos:", e)
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

# Helper function to generate symptom-specific yoga poses for development
def get_symptom_specific_yoga(symptoms):
    """Generate yoga poses based on specific symptoms"""
    
    # Define yoga poses for different symptoms
    poses_db = {
        "cramps": [
            {
                "name": "Child's Pose (Balasana)",
                "duration": "5-10 minutes",
                "steps": [
                    "Kneel on the floor with your big toes touching",
                    "Sit back on your heels and separate knees hip-width apart",
                    "Fold forward, extending your arms in front of you",
                    "Rest your forehead on the mat and breathe deeply"
                ],
                "benefits": ["Relieves menstrual cramps", "Calms the nervous system", "Reduces stress"],
                "relievesSymptoms": ["cramps", "stress", "anxiety"],
                "precautions": ["Avoid if you have knee injuries", "Use a pillow under your head if needed"]
            },
            {
                "name": "Supine Spinal Twist",
                "duration": "3-5 minutes each side",
                "steps": [
                    "Lie on your back with arms stretched out",
                    "Bring knees to chest, then drop them to one side",
                    "Keep shoulders grounded and breathe deeply",
                    "Switch sides after 3-5 minutes"
                ],
                "benefits": ["Relieves lower back tension", "Eases menstrual cramps", "Improves digestion"],
                "relievesSymptoms": ["cramps", "back pain", "bloating"],
                "precautions": ["Move slowly", "Don't force the twist"]
            }
        ],
        "bloating": [
            {
                "name": "Wind-Relieving Pose (Pawanmuktasana)",
                "duration": "2-3 minutes each leg",
                "steps": [
                    "Lie on your back with legs extended",
                    "Bring one knee to chest and hug it",
                    "Rock gently side to side",
                    "Switch legs and repeat"
                ],
                "benefits": ["Relieves gas and bloating", "Improves digestion", "Massages abdominal organs"],
                "relievesSymptoms": ["bloating", "gas", "digestive issues"],
                "precautions": ["Avoid if you have recent abdominal surgery"]
            },
            {
                "name": "Seated Forward Bend",
                "duration": "5-8 minutes",
                "steps": [
                    "Sit with legs extended straight",
                    "Inhale and lengthen your spine",
                    "Exhale and fold forward from the hips",
                    "Rest hands on legs or feet"
                ],
                "benefits": ["Stimulates digestion", "Relieves bloating", "Calms the mind"],
                "relievesSymptoms": ["bloating", "stress", "fatigue"],
                "precautions": ["Don't force the forward fold", "Keep knees slightly bent if tight hamstrings"]
            }
        ],
        "back pain": [
            {
                "name": "Cat-Cow Stretch",
                "duration": "5-10 repetitions",
                "steps": [
                    "Start on hands and knees in tabletop position",
                    "Inhale, arch your back and look up (Cow)",
                    "Exhale, round your spine and tuck chin (Cat)",
                    "Continue flowing between positions"
                ],
                "benefits": ["Increases spinal flexibility", "Relieves back tension", "Improves posture"],
                "relievesSymptoms": ["back pain", "stiffness", "tension"],
                "precautions": ["Move slowly and smoothly", "Stop if you feel sharp pain"]
            },
            {
                "name": "Knee-to-Chest Pose",
                "duration": "3-5 minutes",
                "steps": [
                    "Lie on your back with knees bent",
                    "Bring both knees to chest",
                    "Wrap arms around knees and rock gently",
                    "Breathe deeply and hold"
                ],
                "benefits": ["Stretches lower back", "Relieves tension", "Improves circulation"],
                "relievesSymptoms": ["back pain", "tension", "stiffness"],
                "precautions": ["Move gently", "Avoid if you have knee problems"]
            }
        ],
        "headache": [
            {
                "name": "Legs-Up-The-Wall Pose",
                "duration": "10-15 minutes",
                "steps": [
                    "Lie on your back near a wall",
                    "Extend legs up the wall",
                    "Rest arms by your sides",
                    "Close eyes and breathe deeply"
                ],
                "benefits": ["Relieves headaches", "Reduces stress", "Improves circulation"],
                "relievesSymptoms": ["headache", "stress", "fatigue"],
                "precautions": ["Come out slowly", "Use a pillow under your head if needed"]
            },
            {
                "name": "Gentle Neck Rolls",
                "duration": "2-3 minutes",
                "steps": [
                    "Sit comfortably with spine straight",
                    "Slowly drop chin to chest",
                    "Gently roll head to one side, then the other",
                    "Complete 5-8 slow circles in each direction"
                ],
                "benefits": ["Relieves neck tension", "Reduces headaches", "Improves mobility"],
                "relievesSymptoms": ["headache", "neck tension", "stress"],
                "precautions": ["Move very slowly", "Stop if you feel dizzy"]
            }
        ],
        "fatigue": [
            {
                "name": "Supported Bridge Pose",
                "duration": "5-10 minutes",
                "steps": [
                    "Lie on your back with knees bent",
                    "Place a yoga block or pillow under your sacrum",
                    "Let your body rest on the support",
                    "Breathe deeply and relax"
                ],
                "benefits": ["Energizes the body", "Opens the chest", "Improves mood"],
                "relievesSymptoms": ["fatigue", "low energy", "depression"],
                "precautions": ["Remove support slowly", "Avoid if you have neck issues"]
            },
            {
                "name": "Gentle Backbend",
                "duration": "3-5 minutes",
                "steps": [
                    "Sit cross-legged with hands behind you",
                    "Lean back slightly and open your chest",
                    "Breathe deeply into your chest",
                    "Return to center slowly"
                ],
                "benefits": ["Increases energy", "Opens heart chakra", "Improves posture"],
                "relievesSymptoms": ["fatigue", "low mood", "shallow breathing"],
                "precautions": ["Don't overarch", "Support yourself with hands"]
            }
        ],
        "anxiety": [
            {
                "name": "Corpse Pose (Savasana)",
                "duration": "10-20 minutes",
                "steps": [
                    "Lie flat on your back with arms by your sides",
                    "Let your feet fall open naturally",
                    "Close your eyes and focus on your breath",
                    "Allow your body to completely relax"
                ],
                "benefits": ["Reduces anxiety", "Calms the nervous system", "Promotes deep relaxation"],
                "relievesSymptoms": ["anxiety", "stress", "insomnia"],
                "precautions": ["Use a blanket to stay warm", "Place pillow under knees if back is sensitive"]
            },
            {
                "name": "Extended Puppy Pose",
                "duration": "5-8 minutes",
                "steps": [
                    "Start in tabletop position",
                    "Walk hands forward while keeping hips over knees",
                    "Lower forehead to the mat",
                    "Breathe deeply and hold"
                ],
                "benefits": ["Calms anxiety", "Stretches spine", "Promotes introspection"],
                "relievesSymptoms": ["anxiety", "stress", "tension"],
                "precautions": ["Use a blanket under knees", "Don't force the stretch"]
            }
        ],
        "mood swings": [
            {
                "name": "Heart Opening Camel Pose (Modified)",
                "duration": "3-5 minutes",
                "steps": [
                    "Kneel with shins on the floor",
                    "Place hands on lower back",
                    "Gently arch back and lift chest",
                    "Keep head neutral or slightly back"
                ],
                "benefits": ["Balances emotions", "Opens heart chakra", "Increases confidence"],
                "relievesSymptoms": ["mood swings", "depression", "low self-esteem"],
                "precautions": ["Come up slowly", "Avoid if you have neck problems"]
            },
            {
                "name": "Warrior II Pose",
                "duration": "3-5 minutes each side",
                "steps": [
                    "Stand with feet wide apart",
                    "Turn right foot out 90 degrees",
                    "Bend right knee over ankle",
                    "Extend arms parallel to floor"
                ],
                "benefits": ["Builds inner strength", "Improves focus", "Balances emotions"],
                "relievesSymptoms": ["mood swings", "low confidence", "emotional instability"],
                "precautions": ["Don't let knee go past ankle", "Keep front thigh parallel to floor"]
            }
        ]
    }
    
    # Extract symptoms from the prompt if it's a string
    if isinstance(symptoms, str):
        symptoms_list = [s.strip().lower() for s in symptoms.split(',')]
    elif isinstance(symptoms, list):
        symptoms_list = [s.lower() for s in symptoms]
    else:
        symptoms_list = ['cramps']  # default
    
    # Collect relevant poses based on symptoms
    recommended_poses = []
    used_poses = set()
    
    for symptom in symptoms_list:
        if symptom in poses_db:
            for pose in poses_db[symptom]:
                pose_name = pose['name']
                if pose_name not in used_poses:
                    recommended_poses.append(pose)
                    used_poses.add(pose_name)
    
    # If no specific poses found, add some general menstrual health poses
    if not recommended_poses:
        recommended_poses = poses_db['cramps'] + poses_db['bloating'][:1]
      # Limit to 6 poses maximum
    recommended_poses = recommended_poses[:6]
    
    return {
        "yogaAsanas": recommended_poses
    }

# Helper function to generate symptom-specific ayurvedic remedies for development
def get_symptom_specific_ayurveda(symptoms):
    """Generate ayurvedic remedies based on specific symptoms"""
    
    # Define ayurvedic remedies for different symptoms
    remedies_db = {
        "cramps": [
            {
                "title": "अजवाइन काढ़ा (Ajwain Kadha) - Carom Seed Decoction",
                "description": "A traditional Ayurvedic remedy that balances Vata dosha and provides quick relief from menstrual cramps through its antispasmodic properties.",
                "ingredients": [
                    "1 teaspoon carom seeds (ajwain)",
                    "1 cup water",
                    "1/2 teaspoon jaggery (optional)",
                    "Pinch of black salt"
                ],
                "steps": [
                    "Step 1: Boil 1 cup water in a small saucepan",
                    "Step 2: Add 1 teaspoon carom seeds and simmer for 5 minutes",
                    "Step 3: Strain the decoction into a cup",
                    "Step 4: Add jaggery and black salt to taste",
                    "Step 5: Drink warm, twice daily during menstruation"
                ],
                "benefits": "Relieves menstrual cramps, improves digestion, balances Vata dosha, reduces bloating, and has anti-inflammatory properties",
                "bestTimeToConsume": "Morning on empty stomach and evening before dinner",
                "precautions": [
                    "Avoid during pregnancy",
                    "Reduce quantity if you have acidity",
                    "Not recommended for those with high blood pressure"
                ],
                "storageInstructions": "Prepare fresh each time for best results",
                "shelfLife": "Consume immediately after preparation",
                "time": "10 minutes preparation, 3-day treatment cycle",
                "image": "static/Images/default-remedy.jpg"
            },
            {
                "title": "शतावरी चूर्ण (Shatavari Churna) - Asparagus Root Powder",
                "description": "A powerful Rasayana (rejuvenative) herb that specifically supports women's reproductive health and hormonal balance.",
                "ingredients": [
                    "1 teaspoon Shatavari powder",
                    "1 cup warm milk",
                    "1/2 teaspoon ghee",
                    "Honey to taste"
                ],
                "steps": [
                    "Step 1: Warm 1 cup of milk without boiling",
                    "Step 2: Add 1 teaspoon Shatavari powder and mix well",
                    "Step 3: Add ghee and stir until dissolved",
                    "Step 4: Let it cool slightly, then add honey",
                    "Step 5: Drink daily during menstrual cycle"
                ],
                "benefits": "Balances hormones, strengthens reproductive system, reduces menstrual irregularities, supports Ojas (vitality)",
                "bestTimeToConsume": "Before bedtime for better absorption",
                "precautions": [
                    "Start with small quantities",
                    "Avoid if allergic to asparagus",
                    "Consult Ayurvedic practitioner for dosage"
                ],
                "storageInstructions": "Store powder in airtight container in cool, dry place",
                "shelfLife": "Powder: 1 year, Prepared milk: consume immediately",
                "time": "5 minutes preparation, use throughout menstrual cycle",
                "image": "static/Images/default-remedy.jpg"
            }
        ],
        "bloating": [
            {
                "title": "हींग पानी (Hing Pani) - Asafoetida Water",
                "description": "An effective Ayurvedic remedy for digestive issues that helps balance Vata and Kapha doshas, particularly beneficial for abdominal bloating.",
                "ingredients": [
                    "Pinch of pure asafoetida (hing)",
                    "1 glass warm water",
                    "1/2 teaspoon lemon juice",
                    "Rock salt to taste"
                ],
                "steps": [
                    "Step 1: Take a pinch of pure asafoetida in a glass",
                    "Step 2: Add warm water and stir until dissolved",
                    "Step 3: Add lemon juice and rock salt",
                    "Step 4: Mix well and drink immediately",
                    "Step 5: Take 2-3 times daily for relief"
                ],
                "benefits": "Reduces bloating and gas, improves digestion, balances Vata dosha, relieves abdominal discomfort",
                "bestTimeToConsume": "30 minutes before meals",
                "precautions": [
                    "Use only pure asafoetida",
                    "Avoid if pregnant or breastfeeding",
                    "May cause allergic reactions in some"
                ],
                "storageInstructions": "Prepare fresh each time",
                "shelfLife": "Consume immediately",
                "time": "2 minutes preparation, immediate relief",
                "image": "static/Images/default-remedy.jpg"
            }
        ],
        "fatigue": [
            {
                "title": "अश्वगंधा रसायन (Ashwagandha Rasayana) - Energy Tonic",
                "description": "A revitalizing Ayurvedic formulation that builds Ojas (vital energy) and strengthens the nervous system.",
                "ingredients": [
                    "1 teaspoon Ashwagandha powder",
                    "1 cup warm milk",
                    "1/4 teaspoon cardamom powder",
                    "1 teaspoon ghee",
                    "Dates for sweetening"
                ],
                "steps": [
                    "Step 1: Soak 2-3 dates and make a paste",
                    "Step 2: Warm milk and add Ashwagandha powder",
                    "Step 3: Add cardamom powder and date paste",
                    "Step 4: Stir in ghee until well mixed",
                    "Step 5: Drink before bedtime for best results"
                ],
                "benefits": "Increases energy and stamina, reduces fatigue, balances stress hormones, improves sleep quality",
                "bestTimeToConsume": "Before bedtime or early morning",
                "precautions": [
                    "Not recommended during acute illness",
                    "Avoid with sedative medications",
                    "Start with smaller doses"
                ],
                "storageInstructions": "Store in refrigerator for up to 24 hours",
                "shelfLife": "Best consumed fresh",
                "time": "10 minutes preparation, 2-week course recommended",
                "image": "static/Images/default-remedy.jpg"
            }
        ],
        "headache": [
            {
                "title": "त्रिफला नस्य (Triphala Nasya) - Herbal Nasal Treatment",
                "description": "A gentle Ayurvedic nasal therapy using Triphala that helps clear blocked channels and relieves headaches.",
                "ingredients": [
                    "1/2 teaspoon Triphala powder",
                    "2 tablespoons warm water",
                    "1 drop sesame oil",
                    "Cotton swabs"
                ],
                "steps": [
                    "Step 1: Mix Triphala powder with warm water to make paste",
                    "Step 2: Strain the liquid and let it cool to room temperature",
                    "Step 3: Add one drop of sesame oil",
                    "Step 4: Using cotton swab, apply gently inside nostrils",
                    "Step 5: Lie down for 5 minutes after application"
                ],
                "benefits": "Clears nasal passages, relieves tension headaches, balances Prana Vata, improves mental clarity",
                "bestTimeToConsume": "Morning before sunrise or evening",
                "precautions": [
                    "Use only pharmaceutical grade Triphala",
                    "Avoid if you have nasal infections",
                    "Stop if irritation occurs"
                ],
                "storageInstructions": "Prepare fresh each time",
                "shelfLife": "Use immediately after preparation",
                "time": "15 minutes preparation and application",
                "image": "static/Images/default-remedy.jpg"
            }
        ]
    }
    
    # Extract symptoms from the input
    if isinstance(symptoms, str):
        symptoms_list = [s.strip().lower() for s in symptoms.split(',')]
    elif isinstance(symptoms, list):
        symptoms_list = [s.lower() for s in symptoms]
    else:
        symptoms_list = ['cramps']  # default
    
    # Collect relevant remedies based on symptoms
    recommended_remedies = []
    used_remedies = set()
    
    for symptom in symptoms_list:
        if symptom in remedies_db:
            for remedy in remedies_db[symptom]:
                remedy_title = remedy['title']
                if remedy_title not in used_remedies:
                    recommended_remedies.append(remedy)
                    used_remedies.add(remedy_title)
    
    # If no specific remedies found, add some general menstrual health remedies
    if not recommended_remedies:
        recommended_remedies = remedies_db['cramps'][:2]
    
    # Limit to 4 remedies maximum
    recommended_remedies = recommended_remedies[:4]
    
    return {
        "ayurvedicRemedies": recommended_remedies
    }

@app.route('/api/symptom-logs')
def get_symptom_logs():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    try:
        user_id = session['user_id']
        # Get all symptom entries for this user, order by date ascending
        entries = SymptomEntry.query.filter_by(user_id=user_id).order_by(SymptomEntry.entry_date.asc()).all()
        data = []
        for entry in entries:
            data.append({
                'date': entry.entry_date.isoformat(),
                'flow_level': entry.flow_level,
                'mood': entry.mood,
                'pain_level': entry.pain_level,
                'notes': entry.notes
            })
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
