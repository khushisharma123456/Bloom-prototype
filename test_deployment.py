#!/usr/bin/env python3
"""
Quick Deployment Check
Run this script to verify your production deployment is working correctly.
"""

import requests
import json
import sys
import time
from typing import Dict, Any

def test_endpoint(url: str, method: str = 'GET', data: Dict = None, timeout: int = 30) -> Dict[str, Any]:
    """Test an API endpoint and return results."""
    try:
        if method == 'GET':
            response = requests.get(url, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=timeout, 
                                   headers={'Content-Type': 'application/json'})
        
        return {
            'success': response.status_code == 200,
            'status_code': response.status_code,
            'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            'response_time': response.elapsed.total_seconds()
        }
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timeout'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': str(e)}
    except Exception as e:
        return {'success': False, 'error': f'Unexpected error: {str(e)}'}

def main():
    """Run deployment checks."""
    
    # Get the base URL from user
    print("🔍 Bloom AI Deployment Checker")
    print("=" * 40)
    
    base_url = input("Enter your deployment URL (e.g., https://your-app.render.com): ").strip()
    if not base_url:
        print("❌ No URL provided. Exiting.")
        return
    
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    print(f"\n🌐 Testing deployment at: {base_url}")
    print("-" * 50)
    
    # Test 1: Basic connectivity
    print("1. Testing basic connectivity...")
    result = test_endpoint(base_url)
    if result.get('success'):
        print(f"   ✅ Site is accessible ({result.get('response_time', 0):.2f}s)")
    else:
        print(f"   ❌ Site not accessible: {result.get('error', 'Unknown error')}")
        return
    
    # Test 2: Configuration endpoint
    print("\n2. Testing configuration...")
    config_url = f"{base_url}/api/test-config"
    result = test_endpoint(config_url)
    if result.get('success'):
        data = result.get('data', {})
        print(f"   ✅ Configuration endpoint working")
        print(f"   📊 Project ID set: {data.get('project_id_set', False)}")
        print(f"   📊 Credentials set: {data.get('credentials_set', False)}")
        print(f"   📊 Environment: {data.get('environment', 'unknown')}")
        
        if not data.get('project_id_set'):
            print("   ⚠️  Warning: Google Cloud Project ID not set")
        if not data.get('credentials_set'):
            print("   ⚠️  Warning: Google Cloud credentials not configured")
    else:
        print(f"   ❌ Configuration check failed: {result.get('error', 'Unknown error')}")
    
    # Test 3: Doctor images API
    print("\n3. Testing doctor images API...")
    images_url = f"{base_url}/api/doctor-images"
    result = test_endpoint(images_url)
    if result.get('success'):
        data = result.get('data', {})
        image_count = len(data) if isinstance(data, dict) else 0
        print(f"   ✅ Doctor images API working")
        print(f"   📊 Images available: {image_count}")
    else:
        print(f"   ❌ Doctor images API failed: {result.get('error', 'Unknown error')}")
    
    # Test 4: Image generation (only if credentials are set)
    print("\n4. Testing image generation...")
    if 'data' in locals() and isinstance(data, dict) and data.get('project_id_set') and data.get('credentials_set'):
        gen_url = f"{base_url}/api/generate-doctor-image"
        test_data = {
            "name": "Dr. Test User",
            "specialty": "General Medicine",
            "gender": "female"
        }
        
        print("   🎨 Attempting to generate test image (this may take 30+ seconds)...")
        result = test_endpoint(gen_url, method='POST', data=test_data, timeout=60)
        
        if result.get('success'):
            print("   ✅ Image generation working!")
            print(f"   📊 Response time: {result.get('response_time', 0):.2f}s")
        else:
            print(f"   ❌ Image generation failed: {result.get('error', 'Unknown error')}")
    else:
        print("   ⚠️  Skipping image generation test (credentials not configured)")
    
    # Test 5: Static files
    print("\n5. Testing static file serving...")
    static_url = f"{base_url}/static/css/consultation.css"
    result = test_endpoint(static_url)
    if result.get('success'):
        print("   ✅ Static files accessible")
    else:
        print(f"   ⚠️  Static files may not be properly configured: {result.get('error', 'Check manually')}")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 DEPLOYMENT CHECK COMPLETE")
    print("=" * 50)
    
    print("\n📋 Next Steps:")
    print("1. If all tests pass: Your deployment is ready! 🎉")
    print("2. If configuration fails: Set environment variables on your platform")
    print("3. If image generation fails: Check Google Cloud setup")
    print("4. Test the full application manually in your browser")
    
    print(f"\n🌐 Visit your application: {base_url}")
    print(f"📊 Test consultation page: {base_url}/consultation")
    
    print("\n📚 For troubleshooting, see:")
    print("- SECURE_DEPLOYMENT_GUIDE.md")
    print("- production_deployment.md")
    print("- Run: python validate_production_config.py")

if __name__ == "__main__":
    main()
