# Google Cloud Run Deployment Script
# Run this script to deploy to Google Cloud Run

# Prerequisites:
# 1. Install Google Cloud CLI: https://cloud.google.com/sdk/docs/install
# 2. Authenticate: gcloud auth login
# 3. Set project: gcloud config set project YOUR_PROJECT_ID

# Build and deploy commands:

# Set your project ID
$PROJECT_ID = "your-actual-project-id"
$SERVICE_NAME = "bloom-consultation"
$REGION = "us-central1"

# Build the container image
Write-Host "Building container image..." -ForegroundColor Green
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Green
gcloud run deploy $SERVICE_NAME `
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --set-env-vars "FLASK_ENV=production,FLASK_DEBUG=False" `
    --memory 1Gi `
    --cpu 1 `
    --timeout 300 `
    --max-instances 10

# The service account will have default permissions for the project
# No need to set GOOGLE_APPLICATION_CREDENTIALS in Cloud Run

Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Your service URL:" -ForegroundColor Yellow
gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)'
