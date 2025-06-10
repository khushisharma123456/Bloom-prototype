# Google OAuth Setup Instructions

## What I've implemented:

1. **Added Google OAuth dependencies** to `requirements.txt`:
   - google-auth
   - google-auth-oauthlib
   - google-auth-httplib2

2. **Added Google OAuth routes** to `app.py`:
   - `/auth/google` - Initiates Google login
   - `/auth/google/callback` - Handles Google OAuth callback

3. **Updated login and signup pages**:
   - Made "Continue with Google" buttons functional
   - Both now redirect to `/auth/google` when clicked

## To complete the setup:

### 1. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API
4. Go to "Credentials" > "Create Credentials" > "OAuth 2.0 Client IDs"
5. Set Application type to "Web application"
6. Add these to "Authorized redirect URIs":
   - `http://localhost:5000/auth/google/callback`
   - `http://127.0.0.1:5000/auth/google/callback`

### 2. Update app.py with your credentials

Replace these lines in `app.py`:

```python
GOOGLE_CLIENT_ID = "your_google_client_id_here"  # Replace with your actual Google Client ID
GOOGLE_CLIENT_SECRET = "your_google_client_secret_here"  # Replace with your actual Google Client Secret
```

With your actual credentials from Google Cloud Console.

### 3. How it works:

1. **User clicks "Continue with Google"** → Redirects to `/auth/google`
2. **App redirects to Google** → User authorizes the app
3. **Google redirects back** → To `/auth/google/callback` with authorization code
4. **App exchanges code for user info** → Gets email, name, picture
5. **User login/signup**:
   - If email exists → Log them in
   - If new user → Create account and redirect to survey
6. **User is logged in** → Redirected to dashboard

### 4. Security Features:

- Uses state parameter to prevent CSRF attacks
- Generates random password for Google users
- Proper error handling with user-friendly messages
- Secure token verification

### 5. Testing:

1. Set up Google OAuth credentials
2. Update the credentials in app.py
3. Run the Flask app: `python app.py`
4. Go to `http://localhost:5000/login`
5. Click "Continue with Google"

The Google OAuth login is now fully functional and will work once you add your Google OAuth credentials!
