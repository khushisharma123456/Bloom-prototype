#!/usr/bin/env python3
"""
Simple Yoga Pose Image Regenerator - Fix specific poses
"""

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import os
from google.cloud import storage
from PIL import Image
import io
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def regenerate_apanasana():
    """Regenerate just the Apanasana pose with correct prompt"""
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    
    if not PROJECT_ID or PROJECT_ID == 'your-project-id':
        print("❌ Please set GOOGLE_CLOUD_PROJECT_ID environment variable")
        return
    
    print(f"🚀 Regenerating Apanasana image...")
    print(f"📋 Project ID: {PROJECT_ID}")
    
    try:
        # Initialize Vertex AI
        vertexai.init(project=PROJECT_ID, location="us-central1")
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        # Initialize Cloud Storage
        storage_client = storage.Client()
        bucket_name = f"{PROJECT_ID}-yoga-pose-images"
        
        # Specific correct prompt for Apanasana
        prompt = """Professional yoga photography of a peaceful woman lying on her back on a yoga mat, gently hugging both knees to her chest with her arms wrapped around her shins. Her head is relaxed on the mat, eyes closed with a serene expression. The pose demonstrates perfect Apanasana (Knees-to-Chest Pose).

VISUAL DETAILS:
- Woman lying on her back (supine position) on a clean yoga mat
- Both knees bent and drawn up to chest level
- Arms wrapped around shins, gently hugging knees to chest
- Head resting comfortably on the mat
- Peaceful, relaxed facial expression with eyes closed
- Comfortable yoga attire in soft, neutral colors

SETTING:
- Clean, minimalist yoga studio with warm natural lighting
- Neutral background, focus on the pose
- Peaceful, calming atmosphere suitable for therapeutic yoga
- Professional wellness photography lighting

TECHNICAL REQUIREMENTS:
- High quality photography with sharp focus
- Warm, soft lighting from the side creating gentle shadows
- Calm, therapeutic mood emphasizing relaxation
- Suitable for yoga instruction and wellness content
- No text, watermarks, or distracting elements
- Clean composition focusing on proper pose alignment"""
        
        print("🎯 Generating image with corrected prompt...")
        
        # Generate image
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="block_only_high",
            person_generation="allow_adult",
            language="en",
            guidance_scale=15,
            negative_prompt="inappropriate, dark, distorted, low quality, blurry, text, watermarks, wrong pose"
        )
        
        if not response.images:
            print("❌ No images generated")
            return
        
        # Process image
        generated_image = response.images[0]
        image_bytes = generated_image._image_bytes
        image = Image.open(io.BytesIO(image_bytes))
        
        # Resize and save
        image = image.resize((512, 512), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=90, optimize=True)
        buffer.seek(0)
        
        # Upload to Cloud Storage
        filename = "yoga_pose_apanasana_knees_to_chest_pose.jpg"
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"poses/{filename}")
        blob.upload_from_string(buffer.getvalue(), content_type='image/jpeg')
        blob.make_public()
        
        public_url = blob.public_url
        print(f"✅ Successfully regenerated Apanasana: {public_url}")
        
        # Update yoga.json
        update_yoga_json("Apanasana (Knees-to-Chest Pose)", public_url)
        
        return public_url
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def update_yoga_json(pose_name, image_url):
    """Update the yoga.json file with new image URL"""
    try:
        # Load yoga.json
        with open('static/data/yoga.json', 'r', encoding='utf-8') as f:
            yoga_poses = json.load(f)
        
        # Find and update the pose
        for pose in yoga_poses:
            if pose.get('name') == pose_name:
                pose['image'] = image_url
                print(f"✅ Updated {pose_name} in yoga.json")
                break
        
        # Save updated file
        with open('static/data/yoga.json', 'w', encoding='utf-8') as f:
            json.dump(yoga_poses, f, indent=2, ensure_ascii=False)
        
        print(f"💾 yoga.json updated successfully")
        
    except Exception as e:
        print(f"❌ Error updating yoga.json: {str(e)}")

if __name__ == "__main__":
    regenerate_apanasana()
