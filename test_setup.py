#!/usr/bin/env python3
"""
Test script to check Google Cloud authentication and Vertex AI setup
"""

import os
from dotenv import load_dotenv

def test_setup():
    # Load environment variables
    load_dotenv()
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    print(f"✅ Project ID loaded: {project_id}")
    
    if not project_id or project_id == 'your-imagen4-project-id':
        print("❌ Error: GOOGLE_CLOUD_PROJECT_ID not set or using placeholder value")
        return False
    
    try:
        print("🔍 Testing Vertex AI import...")
        import vertexai
        print("✅ Vertex AI imported successfully")
        
        print("🔍 Testing Vertex AI initialization...")
        vertexai.init(project=project_id, location="us-central1")
        print("✅ Vertex AI initialized successfully")
        
        print("🔍 Testing ImageGenerationModel import...")
        from vertexai.preview.vision_models import ImageGenerationModel
        print("✅ ImageGenerationModel imported successfully")
        
        print("🔍 Testing model loading...")
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        print("✅ Model loaded successfully")
        
        print("🔍 Loading recipes...")
        import json
        recipes_path = os.path.join('static', 'data', 'recipes.json')
        with open(recipes_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        recipes = data.get('remedies', [])
        print(f"✅ Loaded {len(recipes)} recipes")
        
        print("\n🎉 All checks passed! Ready to generate images.")
        return True
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Bloom Recipe Image Generator Setup")
    print("=" * 50)
    test_setup()
