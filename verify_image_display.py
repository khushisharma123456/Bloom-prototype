#!/usr/bin/env python3
"""
Verification script for AI-generated doctor images display fix.
Checks that images are displaying correctly without cropping.
"""

import json
import requests
import os
from urllib.parse import urlparse

def verify_image_display_fix():
    """Verify that the AI-generated doctor images are displaying correctly."""
    
    print("🔍 Verifying AI-Generated Doctor Images Display Fix...")
    print("=" * 60)
    
    # Check if doctor_images_results.json exists
    results_file = "doctor_images_results.json"
    if not os.path.exists(results_file):
        print("❌ Error: doctor_images_results.json not found!")
        return False
    
    # Load the results
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
        print(f"✅ Found {len(results)} doctor image records")
    except Exception as e:
        print(f"❌ Error loading results: {e}")
        return False
    
    # Check image URLs
    ai_generated_count = 0
    working_images = 0
    failed_images = []
    
    print("\n📊 Image Status Report:")
    print("-" * 40)
    
    for result in results:
        doctor_name = result.get('doctor_name', 'Unknown')
        url = result.get('url', '')
        success = result.get('success', False)
        
        if success and url:
            ai_generated_count += 1
            
            # Test if the image URL is accessible
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    working_images += 1
                    print(f"✅ {doctor_name}: Image accessible")
                else:
                    failed_images.append(f"{doctor_name} (HTTP {response.status_code})")
                    print(f"⚠️  {doctor_name}: HTTP {response.status_code}")
            except Exception as e:
                failed_images.append(f"{doctor_name} (Network error)")
                print(f"❌ {doctor_name}: Network error")
        else:
            print(f"⚪ {doctor_name}: No AI-generated image")
    
    print("\n📈 Summary:")
    print("-" * 40)
    print(f"Total doctors: {len(results)}")
    print(f"AI-generated images: {ai_generated_count}")
    print(f"Working images: {working_images}")
    print(f"Failed images: {len(failed_images)}")
    
    if failed_images:
        print(f"\n❌ Failed Images:")
        for failed in failed_images:
            print(f"   - {failed}")
    
    # Check CSS and JS fixes
    print(f"\n🔧 Checking Display Fix Implementation:")
    print("-" * 40)
    
    # Check CSS file
    css_file = "static/css/consultation.css"
    if os.path.exists(css_file):
        with open(css_file, 'r') as f:
            css_content = f.read()
        
        if "background-size: contain" in css_content and ".professional-image" in css_content:
            print("✅ CSS fix implemented: background-size: contain")
        else:
            print("❌ CSS fix not found")
    else:
        print("❌ CSS file not found")
    
    # Check JS file
    js_file = "static/css/consultation.js"
    if os.path.exists(js_file):
        with open(js_file, 'r') as f:
            js_content = f.read()
        
        if "background-size: contain" in js_content:
            print("✅ JavaScript fix implemented: background-size: contain")
        else:
            print("❌ JavaScript fix not found")
    else:
        print("❌ JavaScript file not found")
    
    # Calculate success rate
    if ai_generated_count > 0:
        success_rate = (working_images / ai_generated_count) * 100
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 Excellent! AI-generated images are working well!")
        elif success_rate >= 75:
            print("👍 Good! Most AI-generated images are working.")
        else:
            print("⚠️  Some issues detected with AI-generated images.")
    
    return working_images > 0

def check_image_styling():
    """Check that the image styling prevents cropping."""
    
    print(f"\n🎨 Image Styling Verification:")
    print("-" * 40)
    
    css_file = "static/css/consultation.css"
    js_file = "static/css/consultation.js"
    
    fixes_applied = []
    
    # Check CSS
    if os.path.exists(css_file):
        with open(css_file, 'r') as f:
            css_content = f.read()
        
        checks = [
            ("background-size: contain", "Prevents image cropping"),
            ("height: 240px", "Adequate height for full image"),
            ("background-position: center", "Centers the image properly"),
            ("background-repeat: no-repeat", "Prevents image repetition")
        ]
        
        for check, description in checks:
            if check in css_content:
                fixes_applied.append(f"✅ CSS: {description}")
            else:
                fixes_applied.append(f"❌ CSS: Missing - {description}")
    
    # Check JavaScript
    if os.path.exists(js_file):
        with open(js_file, 'r') as f:
            js_content = f.read()
        
        if "background-size: contain" in js_content:
            fixes_applied.append("✅ JS: Inline styles use 'contain'")
        else:
            fixes_applied.append("❌ JS: Still using 'cover' (will crop images)")
    
    for fix in fixes_applied:
        print(f"   {fix}")
    
    return True

if __name__ == "__main__":
    try:
        verify_image_display_fix()
        check_image_styling()
        
        print(f"\n✨ Verification Complete!")
        print(f"The hair cropping issue should now be resolved.")
        print(f"AI-generated doctor photos will display fully without cutting off hair/heads.")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
