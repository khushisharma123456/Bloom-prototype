# 🚀 Secure Production Deployment Guide

## Quick Start for Different Platforms

### 🔷 Render.com (Recommended for beginners)
```powershell
# 1. Push your code to GitHub
git add .
git commit -m "Add AI doctor image generation"
git push origin main

# 2. Go to render.com and create new Web Service
# 3. Connect your GitHub repository
# 4. Set these environment variables in Render dashboard:
```
- `GOOGLE_CLOUD_PROJECT_ID` = `your-actual-project-id`
- `GOOGLE_APPLICATION_CREDENTIALS` = Upload your service-account-key.json
- `FLASK_ENV` = `production`
- `FLASK_DEBUG` = `False`

### 🔷 Vercel (Good for static + serverless)
```powershell
# 1. Install Vercel CLI
npm i -g vercel

# 2. Deploy
vercel

# 3. Set environment variables
vercel env add GOOGLE_CLOUD_PROJECT_ID
vercel env add GOOGLE_APPLICATION_CREDENTIALS
```

### 🔷 Railway (Simple and fast)
```powershell
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and deploy
railway login
railway init
railway up

# 3. Set environment variables in Railway dashboard
```

### 🔷 Google Cloud Run (Most secure for GCP)
```powershell
# 1. Set your project ID in deploy-cloudrun.ps1
# 2. Run deployment script
./deploy-cloudrun.ps1
```

## 🔐 Security Configuration Steps

### Step 1: Create Google Cloud Service Account
```powershell
# Install Google Cloud CLI first: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Create service account
gcloud iam service-accounts create bloom-ai-service --display-name="Bloom AI Service"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:bloom-ai-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:bloom-ai-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/storage.admin"

# Create and download key
gcloud iam service-accounts keys create service-account-key.json --iam-account=bloom-ai-service@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Step 2: Enable Required APIs
```powershell
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Enable Cloud Storage API  
gcloud services enable storage-api.googleapis.com

# Enable Cloud Resource Manager API
gcloud services enable cloudresourcemanager.googleapis.com
```

### Step 3: Validate Your Setup
```powershell
# Run the validator script
python validate_production_config.py

# Test authentication
gcloud auth application-default print-access-token

# Test Vertex AI access
gcloud ai models list --region=us-central1
```

## 🌐 Platform-Specific Instructions

### Render.com Setup
1. **Connect Repository**: Link your GitHub repository
2. **Build Settings**: 
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
3. **Environment Variables**:
   ```
   GOOGLE_CLOUD_PROJECT_ID = your-actual-project-id
   FLASK_ENV = production
   FLASK_DEBUG = False
   ```
4. **Upload Service Account Key**: Use the file upload feature in environment variables
5. **Set Credentials Path**: `GOOGLE_APPLICATION_CREDENTIALS = /opt/render/project/service-account-key.json`

### Vercel Setup
1. **Install CLI**: `npm i -g vercel`
2. **Deploy**: `vercel`
3. **Set Environment Variables**:
   ```bash
   vercel env add GOOGLE_CLOUD_PROJECT_ID
   # Paste your project ID when prompted
   
   vercel env add GOOGLE_APPLICATION_CREDENTIALS  
   # Paste your entire service-account-key.json content when prompted
   ```

### Railway Setup
1. **Install CLI**: `npm install -g @railway/cli`
2. **Deploy**: `railway login && railway init && railway up`
3. **Set Variables**: Go to Railway dashboard → Variables tab
4. **Add Variables**:
   - `GOOGLE_CLOUD_PROJECT_ID` = your project ID
   - `GOOGLE_APPLICATION_CREDENTIALS` = full JSON content of service account key

### Google Cloud Run Setup
1. **Edit Script**: Update `PROJECT_ID` in `deploy-cloudrun.ps1`
2. **Run Script**: `./deploy-cloudrun.ps1`
3. **Benefits**: Uses default service account, no credential management needed

## ⚠️ Security Checklist

### Before Deployment
- [ ] **Never commit real credentials** to Git
- [ ] **Set environment variables** on hosting platform
- [ ] **Use service accounts** with minimal permissions
- [ ] **Enable APIs** in Google Cloud Console
- [ ] **Test authentication** locally first
- [ ] **Add .env to .gitignore**
- [ ] **Set FLASK_ENV=production**
- [ ] **Set FLASK_DEBUG=False**

### After Deployment
- [ ] **Test /api/test-config** endpoint
- [ ] **Generate a test doctor image**
- [ ] **Monitor API usage** in Google Cloud Console
- [ ] **Set up billing alerts**
- [ ] **Enable Cloud Logging**
- [ ] **Document your setup**

## 🔍 Testing Your Deployment

### Test Configuration Endpoint
```bash
# Replace YOUR_DOMAIN with your actual domain
curl https://YOUR_DOMAIN.com/api/test-config
```

Expected response:
```json
{
  "project_id_set": true,
  "credentials_set": true,
  "environment": "production"
}
```

### Test Image Generation
```bash
curl -X POST https://YOUR_DOMAIN.com/api/generate-doctor-image \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Sarah Johnson",
    "specialty": "Cardiology", 
    "gender": "female"
  }'
```

### Test Doctor Images API
```bash
curl https://YOUR_DOMAIN.com/api/doctor-images
```

## 🚨 Troubleshooting Common Issues

### Authentication Errors
```
Error: Could not automatically determine credentials
```
**Solution**: Check that `GOOGLE_APPLICATION_CREDENTIALS` is set correctly

### Permission Errors
```
Error: The caller does not have permission
```
**Solution**: Verify service account has `aiplatform.user` and `storage.admin` roles

### Quota Exceeded
```
Error: Quota exceeded for aiplatform.googleapis.com
```
**Solution**: Check quotas in Google Cloud Console, request increases if needed

### Image Generation Timeouts
```
Error: Request timeout
```
**Solution**: Increase timeout settings, check network connectivity

## 📊 Monitoring and Maintenance

### Monitor API Usage
- Go to Google Cloud Console → APIs & Services → Dashboard
- Check Vertex AI API usage
- Monitor Cloud Storage costs

### Set Up Alerts
```powershell
# Set billing alert
gcloud alpha billing budgets create --billing-account=BILLING_ACCOUNT_ID --display-name="Bloom AI Budget" --budget-amount=50USD --threshold-rule=percent=0.8
```

### Logging
- Check Cloud Logging for errors
- Monitor application performance
- Set up uptime monitoring

## 🎯 Production Optimization Tips

1. **Caching**: Cache generated images to avoid regeneration
2. **CDN**: Use Cloud CDN for faster image delivery  
3. **Scaling**: Configure auto-scaling based on usage
4. **Monitoring**: Set up comprehensive monitoring and alerting
5. **Backup**: Regular backups of generated images
6. **Updates**: Plan for model updates and API changes

---

## 🆘 Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Run `python validate_production_config.py` to diagnose problems
3. Check Google Cloud Console for API errors
4. Review platform-specific documentation
5. Monitor application logs for detailed error messages

Remember: **Security first!** Never commit real credentials to version control.
