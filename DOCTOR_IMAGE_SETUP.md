# Doctor Image Generation Setup Guide

This guide explains how to set up and use the AI-powered doctor image generation feature for your consultation system.

## Prerequisites

1. **Google Cloud Project with Vertex AI enabled**
   - Imagen model access (imagegeneration@006)
   - Google Cloud Storage API enabled
   - Service account with necessary permissions

2. **Google Cloud Authentication**
   - Service account JSON key file
   - Or Google Cloud SDK installed and authenticated

## Setup Instructions

### 1. Environment Configuration

Update your `.env` file:
```bash
GOOGLE_CLOUD_PROJECT_ID=your-actual-project-id
```

### 2. Google Cloud Authentication

**Option A: Service Account Key (Recommended for production)**
```bash
# Set the environment variable to point to your service account key
set GOOGLE_APPLICATION_CREDENTIALS=path\to\your\service-account-key.json
```

**Option B: Google Cloud SDK (For development)**
```bash
# Install Google Cloud SDK and authenticate
gcloud auth login
gcloud config set project your-project-id
gcloud auth application-default login
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate Doctor Images

**Single Image Generation:**
```bash
python generate_doctor_images.py
```

**Or use the Flask API:**
```bash
# Start the Flask app
python app.py

# Generate images via API
curl -X POST http://localhost:5000/api/generate-doctor-image \
  -H "Content-Type: application/json" \
  -d '{"name": "Dr. Priya Sharma", "specialty": "Gynecologist", "gender": "female"}'
```

### 5. Verify Setup

1. Start your Flask application: `python app.py`
2. Visit: `http://localhost:5000/consultation`
3. Check browser console for image loading logs
4. Visit: `http://localhost:5000/api/doctor-images` to see generated images

## File Structure

```
Bloom-prototype/
├── imagen_generator.py          # Image generation class
├── generate_doctor_images.py    # Batch generation script
├── app.py                      # Flask routes for image generation
├── static/css/consultation.js  # Updated to use generated images
├── doctor_images_results.json  # Generated images metadata
└── .env                        # Environment configuration
```

## API Endpoints

### Generate Single Doctor Image
```
POST /api/generate-doctor-image
Content-Type: application/json

{
  "name": "Dr. Priya Sharma",
  "specialty": "Gynecologist",
  "gender": "female"
}
```

### Get All Generated Images
```
GET /api/doctor-images
```

### Regenerate All Images (Admin)
```
GET /admin/regenerate-images
```

## How It Works

1. **Image Generation**: Uses Vertex AI's Imagen model to create professional doctor headshots
2. **Cloud Storage**: Images are stored in Google Cloud Storage with public URLs
3. **Frontend Integration**: consultation.js loads generated images and uses them as fallbacks
4. **Dynamic Loading**: Images are loaded asynchronously when the consultation page loads

## Customization

### Modify Doctor Prompts
Edit the `generate_doctor_prompt()` method in `imagen_generator.py`:

```python
def generate_doctor_prompt(self, name, specialty, gender, ethnicity="diverse"):
    # Customize your prompt here
    prompt = f"Professional headshot of a {gender} {specialty}..."
    return prompt
```

### Add New Doctors
Update the `doctors_data` array in `generate_doctor_images.py`:

```python
doctors_data = [
    {
        "id": 25,
        "name": "Dr. New Doctor",
        "specialty": "Cardiologist",
        "gender": "female"
    }
]
```

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```
   Error: Could not automatically determine credentials
   ```
   **Solution**: Set up Google Cloud authentication properly

2. **Project Not Found**
   ```
   Error: Project not found or Vertex AI not enabled
   ```
   **Solution**: Enable Vertex AI API in your Google Cloud Console

3. **Storage Permission Error**
   ```
   Error: Insufficient permissions for Cloud Storage
   ```
   **Solution**: Add Storage Admin role to your service account

4. **Imagen Access Denied**
   ```
   Error: Model not found or access denied
   ```
   **Solution**: Request access to Imagen model in Vertex AI

### Debug Steps

1. Check environment variables:
   ```bash
   echo $GOOGLE_CLOUD_PROJECT_ID
   echo $GOOGLE_APPLICATION_CREDENTIALS
   ```

2. Test Google Cloud connection:
   ```python
   from google.cloud import storage
   client = storage.Client()
   print("Connected successfully!")
   ```

3. Check Flask logs for detailed error messages

## Performance Notes

- Image generation takes 10-30 seconds per image
- Generated images are cached in Cloud Storage
- Frontend uses fallback images if generation fails
- Consider running batch generation during off-peak hours

## Security

- Store service account keys securely
- Use environment variables for sensitive data
- Implement proper authentication for admin endpoints
- Consider image content filtering if needed
