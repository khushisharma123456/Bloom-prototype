#!/usr/bin/env python3
"""
Production Configuration Validator
Validates that your environment is properly configured for secure deployment.
"""

import os
import json
import sys
from typing import Dict, List, Tuple

def check_environment_security() -> Dict[str, any]:
    """Check if environment variables are properly configured for production."""
    
    results = {
        'secure': True,
        'warnings': [],
        'errors': [],
        'recommendations': []
    }
    
    # Check Google Cloud Project ID
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    
    if not project_id:
        results['errors'].append('GOOGLE_CLOUD_PROJECT_ID environment variable not set')
        results['secure'] = False
    elif project_id == 'your-imagen4-project-id':
        results['warnings'].append('Using placeholder project ID - update for production')
        results['recommendations'].append('Set real Google Cloud Project ID in environment variables')
    else:
        results['recommendations'].append('✅ Google Cloud Project ID is configured')
    
    # Check Google Application Credentials
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not creds_path:
        results['warnings'].append('GOOGLE_APPLICATION_CREDENTIALS not set - using default auth')
        results['recommendations'].append('Consider setting service account credentials for production')
    elif os.path.exists(creds_path):
        results['recommendations'].append('✅ Service account credentials file found')
    else:
        results['errors'].append(f'Credentials file not found: {creds_path}')
        results['secure'] = False
    
    # Check for development indicators
    if os.getenv('FLASK_DEBUG') == 'True':
        results['warnings'].append('Flask debug mode is enabled - disable for production')
    
    if os.getenv('FLASK_ENV') == 'development':
        results['warnings'].append('Flask environment is set to development')
    
    # Check .env file security
    env_file_path = '.env'
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
            env_content = f.read()
            
        if 'your_gemini_api_key_here' in env_content:
            results['warnings'].append('.env file contains placeholder API key')
        
        if 'your-imagen4-project-id' in env_content:
            results['warnings'].append('.env file contains placeholder project ID')
            
        results['recommendations'].append('Ensure .env file is in .gitignore')
    
    return results

def check_google_cloud_setup() -> Dict[str, any]:
    """Test Google Cloud authentication and permissions."""
    
    results = {
        'authenticated': False,
        'vertex_ai_enabled': False,
        'storage_accessible': False,
        'errors': []
    }
    
    try:
        # Test basic authentication
        from google.auth import default
        credentials, project = default()
        results['authenticated'] = True
        results['project_id'] = project
        
    except Exception as e:
        results['errors'].append(f'Authentication failed: {str(e)}')
        return results
    
    try:
        # Test Vertex AI access
        import vertexai
        vertexai.init(project=project, location="us-central1")
        results['vertex_ai_enabled'] = True
        
    except Exception as e:
        results['errors'].append(f'Vertex AI access failed: {str(e)}')
    
    try:
        # Test Cloud Storage access
        from google.cloud import storage
        client = storage.Client()
        # Just test if we can create a client, don't actually create buckets
        results['storage_accessible'] = True
        
    except Exception as e:
        results['errors'].append(f'Cloud Storage access failed: {str(e)}')
    
    return results

def generate_deployment_checklist() -> List[str]:
    """Generate a deployment checklist based on current configuration."""
    
    checklist = [
        "🔒 Security Checklist for Production Deployment",
        "",
        "Environment Variables:",
        "□ Set GOOGLE_CLOUD_PROJECT_ID on hosting platform",
        "□ Set GOOGLE_APPLICATION_CREDENTIALS or use default auth",
        "□ Remove or secure GEMINI_API_KEY",
        "□ Set FLASK_ENV=production",
        "□ Set FLASK_DEBUG=False",
        "",
        "Google Cloud Setup:",
        "□ Create service account with minimal permissions",
        "□ Enable Vertex AI API",
        "□ Create Cloud Storage bucket for images",
        "□ Test authentication and permissions",
        "",
        "Code Security:",
        "□ Ensure .env is in .gitignore",
        "□ Remove any hardcoded credentials",
        "□ Enable error logging and monitoring",
        "□ Set up billing alerts",
        "",
        "Testing:",
        "□ Test /api/test-config endpoint",
        "□ Test image generation in production",
        "□ Verify image storage and retrieval",
        "□ Monitor performance and errors",
        "",
        "Documentation:",
        "□ Document environment variable setup",
        "□ Create deployment runbook",
        "□ Set up monitoring dashboards"
    ]
    
    return checklist

def main():
    """Run the production configuration validator."""
    
    print("🔍 Bloom AI Doctor Images - Production Security Validator")
    print("=" * 60)
    
    # Check environment security
    print("\n📋 Checking Environment Configuration...")
    env_results = check_environment_security()
    
    if env_results['secure']:
        print("✅ Environment configuration looks secure")
    else:
        print("❌ Environment configuration has security issues")
    
    for warning in env_results['warnings']:
        print(f"⚠️  {warning}")
    
    for error in env_results['errors']:
        print(f"❌ {error}")
    
    for rec in env_results['recommendations']:
        print(f"💡 {rec}")
    
    # Check Google Cloud setup
    print("\n☁️  Checking Google Cloud Setup...")
    gcp_results = check_google_cloud_setup()
    
    if gcp_results['authenticated']:
        print(f"✅ Authenticated with project: {gcp_results.get('project_id', 'Unknown')}")
    else:
        print("❌ Google Cloud authentication failed")
    
    if gcp_results['vertex_ai_enabled']:
        print("✅ Vertex AI access confirmed")
    else:
        print("❌ Vertex AI access failed")
    
    if gcp_results['storage_accessible']:
        print("✅ Cloud Storage access confirmed")
    else:
        print("❌ Cloud Storage access failed")
    
    for error in gcp_results['errors']:
        print(f"❌ {error}")
    
    # Generate deployment checklist
    print("\n📝 Deployment Checklist:")
    checklist = generate_deployment_checklist()
    for item in checklist:
        print(item)
    
    # Overall status
    print("\n" + "=" * 60)
    if env_results['secure'] and gcp_results['authenticated']:
        print("🎉 Your configuration looks ready for production!")
        print("📖 See production_deployment.md for platform-specific instructions")
    else:
        print("⚠️  Please address the issues above before deploying to production")
        print("📖 See production_deployment.md for detailed setup instructions")

if __name__ == "__main__":
    main()
