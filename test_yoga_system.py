#!/usr/bin/env python3
"""
Test script to verify the symptom-specific yoga recommendation system
"""

import json
import requests
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the function from app.py
from app import get_symptom_specific_yoga

def test_symptom_specific_yoga():
    """Test the get_symptom_specific_yoga function with different symptoms"""
    print("=" * 60)
    print("TESTING SYMPTOM-SPECIFIC YOGA SYSTEM")
    print("=" * 60)
    
    # Test different symptom combinations
    test_cases = [
        ['cramps'],
        ['bloating'],
        ['back pain'],
        ['headache'],
        ['fatigue'],
        ['anxiety'],
        ['mood swings'],
        ['cramps', 'bloating'],
        ['back pain', 'fatigue'],
        ['anxiety', 'mood swings'],
        ['cramps', 'bloating', 'back pain']
    ]
    
    for i, symptoms in enumerate(test_cases, 1):
        print(f"\n{i}. Testing symptoms: {symptoms}")
        print("-" * 40)
        
        result = get_symptom_specific_yoga(symptoms)
        yoga_poses = result.get('yogaAsanas', [])
        
        print(f"   Number of poses returned: {len(yoga_poses)}")
        
        if yoga_poses:
            print("   Poses returned:")
            for pose in yoga_poses:
                relieved_symptoms = pose.get('relievesSymptoms', [])
                print(f"   - {pose['name']} (relieves: {', '.join(relieved_symptoms)})")
                
            # Check if poses are relevant to the symptoms
            relevant_poses = []
            for pose in yoga_poses:
                pose_symptoms = [s.lower() for s in pose.get('relievesSymptoms', [])]
                if any(symptom.lower() in pose_symptoms for symptom in symptoms):
                    relevant_poses.append(pose['name'])
            
            print(f"   Relevant poses for {symptoms}: {len(relevant_poses)}/{len(yoga_poses)}")
            if relevant_poses:
                print(f"   Relevant poses: {', '.join(relevant_poses)}")
        else:
            print("   ❌ No poses returned!")

def test_api_endpoint():
    """Test the Flask API endpoint"""
    print("\n" + "=" * 60)
    print("TESTING FLASK API ENDPOINT")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    endpoint = "/api/get-recommendations"
    
    # Test cases for the API
    test_symptoms = [
        ['cramps'],
        ['bloating', 'back pain'],
        ['anxiety', 'mood swings']
    ]
    
    for symptoms in test_symptoms:
        print(f"\nTesting API with symptoms: {symptoms}")
        print("-" * 40)
        
        # Create a simple prompt
        prompt = f"Please provide yoga poses for these symptoms: {', '.join(symptoms)}"
        
        payload = {
            'prompt': prompt,
            'symptoms': symptoms
        }
        
        try:
            response = requests.post(
                f"{base_url}{endpoint}",
                json=payload,
                timeout=10
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    recommendations = data.get('recommendations', {})
                    yoga_poses = recommendations.get('yogaAsanas', [])
                    print(f"   ✅ Success: {len(yoga_poses)} poses returned")
                    
                    for pose in yoga_poses[:3]:  # Show first 3 poses
                        print(f"   - {pose.get('name', 'Unknown')} (relieves: {', '.join(pose.get('relievesSymptoms', []))})")
                else:
                    print(f"   ❌ API Error: {data.get('message', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                if response.text:
                    print(f"   Error details: {response.text[:200]}...")
                    
        except requests.exceptions.ConnectionError:
            print("   ⚠️  Could not connect to server. Is it running on localhost:5000?")
        except requests.exceptions.Timeout:
            print("   ⚠️  Request timed out")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    # Test the internal function first
    test_symptom_specific_yoga()
    
    # Test the API endpoint
    test_api_endpoint()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
