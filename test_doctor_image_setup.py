#!/usr/bin/env python3
"""
Test script to verify the doctor image generation setup
"""

import os
import sys
from dotenv import load_dotenv

def test_environment():
    """Test environment configuration"""
    print("🔍 Testing Environment Configuration...")
    
    # Load environment variables
    load_dotenv()
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    if not project_id or project_id == 'your-imagen4-project-id':
        print("❌ GOOGLE_CLOUD_PROJECT_ID not set in .env file")
        return False
    else:
        print(f"✅ Project ID: {project_id}")
    
    # Check for Google Cloud credentials
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_path:
        if os.path.exists(creds_path):
            print(f"✅ Service account key found: {creds_path}")
        else:
            print(f"❌ Service account key file not found: {creds_path}")
            return False
    else:
        print("⚠️  GOOGLE_APPLICATION_CREDENTIALS not set (using default credentials)")
    
    return True

def test_imports():
    """Test required imports"""
    print("\n🔍 Testing Required Imports...")
    
    try:
        import vertexai
        print("✅ vertexai imported successfully")
    except ImportError:
        print("❌ vertexai not installed. Run: pip install google-cloud-aiplatform")
        return False
    
    try:
        from google.cloud import storage
        print("✅ google.cloud.storage imported successfully")
    except ImportError:
        print("❌ google-cloud-storage not installed. Run: pip install google-cloud-storage")
        return False
    
    try:
        from PIL import Image
        print("✅ PIL (Pillow) imported successfully")
    except ImportError:
        print("❌ Pillow not installed. Run: pip install Pillow")
        return False
    
    return True

def test_google_cloud_connection():
    """Test Google Cloud connection"""
    print("\n🔍 Testing Google Cloud Connection...")
    
    try:
        from google.cloud import storage
        client = storage.Client()
        # Try to list buckets (this will test authentication)
        buckets = list(client.list_buckets())
        print(f"✅ Connected to Google Cloud successfully")
        print(f"   Found {len(buckets)} buckets in your project")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Google Cloud: {str(e)}")
        print("   Please check your authentication setup")
        return False

def test_imagen_generator():
    """Test the DoctorImageGenerator class"""
    print("\n🔍 Testing DoctorImageGenerator Class...")
    
    try:
        from imagen_generator import DoctorImageGenerator
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        if not project_id:
            print("❌ Project ID not configured")
            return False
        
        # Initialize generator (this tests basic connectivity)
        generator = DoctorImageGenerator(project_id)
        print("✅ DoctorImageGenerator initialized successfully")
        
        # Test prompt generation
        prompt = generator.generate_doctor_prompt("Dr. Test", "Gynecologist", "female")
        if prompt and len(prompt) > 50:
            print("✅ Prompt generation working")
            print(f"   Sample prompt: {prompt[:100]}...")
        else:
            print("❌ Prompt generation failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ DoctorImageGenerator test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Doctor Image Generation Setup Test\n")
    
    tests = [
        test_environment,
        test_imports,
        test_google_cloud_connection,
        test_imagen_generator
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print("\n❌ Test failed. Please fix the issue and try again.")
            break
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your setup is ready for doctor image generation.")
        print("\nNext steps:")
        print("1. Update your .env file with your actual Google Cloud Project ID")
        print("2. Run: python generate_doctor_images.py")
        print("3. Start your Flask app: python app.py")
        print("4. Visit: http://localhost:5000/consultation")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before proceeding.")
        print("\nRefer to DOCTOR_IMAGE_SETUP.md for detailed instructions.")

if __name__ == "__main__":
    main()
