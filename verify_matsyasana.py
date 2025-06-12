#!/usr/bin/env python3
"""
Quick verification for matsyasana image accessibility
"""

import requests
import json

def verify_matsyasana_image():
    """Check if matsyasana image is accessible"""
    try:
        # Load yoga.json to get the matsyasana image URL
        with open('static/data/yoga.json', 'r', encoding='utf-8') as f:
            yoga_poses = json.load(f)
        
        # Find matsyasana
        matsyasana_url = None
        for pose in yoga_poses:
            if 'matsyasana' in pose.get('name', '').lower():
                matsyasana_url = pose.get('image')
                break
        
        if not matsyasana_url:
            print("❌ Matsyasana not found in yoga.json")
            return False
            
        print(f"🔍 Testing URL: {matsyasana_url}")
        
        # Test the URL
        response = requests.get(matsyasana_url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📷 Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"📦 Content Size: {len(response.content):,} bytes")
        
        if response.status_code == 200:
            print("✅ Matsyasana image is accessible!")
            return True
        else:
            print(f"❌ Error accessing image: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    verify_matsyasana_image()
