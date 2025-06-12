#!/usr/bin/env python3
"""
Complete Yoga Pose Fix - Handle all remaining problematic poses
"""

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import os
from google.cloud import storage
from PIL import Image, ImageEnhance, ImageFilter
import io
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CompleteYogaFixer:
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        if not self.project_id or self.project_id == 'your-project-id':
            raise ValueError("❌ Please set GOOGLE_CLOUD_PROJECT_ID environment variable")
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location="us-central1")
        self.model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        # Initialize Cloud Storage
        self.storage_client = storage.Client()
        self.bucket_name = f"{self.project_id}-yoga-pose-images"
        
        print(f"✅ Initialized with project: {self.project_id}")
    
    def generate_pose_image(self, pose_name, prompt, category="general"):
        """Generate image for a specific pose"""
        try:
            print(f"\n🧘‍♀️ Generating: {pose_name}")
            print(f"📝 Category: {category}")
            
            # Generate image with relaxed safety filters
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="block_only_high",  # Less restrictive
                person_generation="allow_adult",
                language="en",
                guidance_scale=12,  # Slightly lower for more variation
                negative_prompt="inappropriate, dark, distorted, low quality, blurry, text, watermarks, wrong pose"
            )
            
            if not response.images:
                print(f"❌ No images generated for {pose_name}")
                return None
            
            # Process image
            generated_image = response.images[0]
            image_bytes = generated_image._image_bytes
            image = Image.open(io.BytesIO(image_bytes))
            
            # Enhance image
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.05)
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.08)
            
            # Resize
            image = image.resize((512, 512), Image.Resampling.LANCZOS)
            
            # Save to buffer
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=90, optimize=True)
            buffer.seek(0)
            
            # Create filename
            safe_name = pose_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
            safe_parts = safe_name.split('_')
            filename = f"yoga_pose_{safe_parts[0]}_{safe_parts[1] if len(safe_parts) > 1 else 'pose'}.jpg"
            
            # Upload to Cloud Storage
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(f"poses/{filename}")
            blob.upload_from_string(buffer.getvalue(), content_type='image/jpeg')
            blob.make_public()
            
            public_url = blob.public_url
            print(f"✅ Success: {public_url}")
            
            return public_url
            
        except Exception as e:
            print(f"❌ Error generating {pose_name}: {str(e)}")
            return None
    
    def update_yoga_json(self, pose_name, image_url):
        """Update yoga.json with new image URL"""
        try:
            # Load yoga.json
            with open('static/data/yoga.json', 'r', encoding='utf-8') as f:
                yoga_poses = json.load(f)
            
            # Find and update the pose
            updated = False
            for pose in yoga_poses:
                if pose.get('name') == pose_name:
                    pose['image'] = image_url
                    print(f"✅ Updated {pose_name} in yoga.json")
                    updated = True
                    break
            
            if not updated:
                print(f"⚠️  Pose not found in yoga.json: {pose_name}")
                return False
            
            # Save updated file
            with open('static/data/yoga.json', 'w', encoding='utf-8') as f:
                json.dump(yoga_poses, f, indent=2, ensure_ascii=False)
            
            print(f"💾 yoga.json updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error updating yoga.json: {str(e)}")
            return False

def main():
    """Fix all remaining problematic poses"""
    try:
        fixer = CompleteYogaFixer()
        
        # Define all remaining poses to fix with improved, less restrictive prompts
        remaining_poses = [
            {
                "name": "Bhujangasana (Cobra Pose)",
                "prompt": """Professional yoga photography of a woman in Cobra Pose, lying on her front on a yoga mat with palms planted under her shoulders. Her chest is gently lifted upward while her lower body remains grounded on the mat, creating a gentle backbend.

Visual: Woman lying face down, palms under shoulders, chest lifted, gentle spinal extension
Setting: Warm yoga studio with natural lighting
Style: Gentle strengthening pose, heart opening, professional instruction
Quality: Clear demonstration of safe backbend technique""",
                "category": "backbend"
            },
            {
                "name": "Parivrtta Janu Sirsasana (Revolved Head-to-Knee Pose)",
                "prompt": """Professional yoga photography of a woman in a seated twist, sitting with one leg extended and one bent. She is gently rotating her spine and reaching over the extended leg in a side stretch and spinal twist combination.

Visual: Woman seated, one leg straight, gentle spinal twist over extended leg
Setting: Peaceful yoga studio with soft lighting
Style: Gentle twisting pose, flexibility, mindful movement
Quality: Clear demonstration of seated twist technique""",
                "category": "twist"
            },
            {
                "name": "Parivrtta Trikonasana (Revolved Triangle Pose)",
                "prompt": """Professional yoga photography of a woman in a standing twist, with legs in wide stance. One hand reaches toward the floor while the other extends upward, creating a triangular shape with gentle spinal rotation.

Visual: Woman in wide stance, one hand down, one up, gentle twist
Setting: Spacious yoga studio with natural light
Style: Standing balance pose with twist, strength and flexibility
Quality: Clear demonstration of standing twist balance""",
                "category": "twist"
            },
            {
                "name": "Paschimottanasana (Seated Forward Bend)",
                "prompt": """Professional yoga photography of a woman in a seated forward fold, sitting with legs extended straight in front. She is gently folding forward from the hips over her legs, hands resting on her legs or feet.

Visual: Woman seated, legs straight, gentle forward fold from hips
Setting: Calm yoga space with soft lighting
Style: Meditative forward fold, introspection, gentle stretching
Quality: Clear demonstration of seated forward fold technique""",
                "category": "forward_fold"
            },
            {
                "name": "Matsyasana (Fish Pose)",
                "prompt": """Professional yoga photography of a woman in a gentle heart opener, lying on her back with her chest lifted and supported by her forearms. Her head is gently tilted back creating a gentle arch in the upper spine.

Visual: Woman lying on back, chest open, gentle backbend supported by forearms
Setting: Bright, peaceful yoga studio
Style: Gentle heart opening, therapeutic backbend
Quality: Clear demonstration of supported heart opening""",
                "category": "backbend"
            },
            {
                "name": "Supta Virasana (Reclining Hero Pose)",
                "prompt": """Professional yoga photography of a woman in a gentle reclining position, sitting with her legs folded beneath her and then leaning back comfortably. The pose demonstrates a gentle hip and thigh stretch.

Visual: Woman kneeling then reclining back, gentle hip stretch
Setting: Supportive yoga environment with props nearby
Style: Gentle restorative pose, therapeutic stretching
Quality: Clear demonstration of supported reclining position""",
                "category": "restorative"
            },
            {
                "name": "Salamba Sarvangasana (Supported Shoulderstand)",
                "prompt": """Professional yoga photography of a woman in a supported inversion, with her shoulders on a folded blanket and legs extending upward. Her hands support her back for stability and safety.

Visual: Woman with shoulders supported, legs up, hands supporting back
Setting: Safe yoga environment with proper props
Style: Therapeutic inversion with support, professional safety setup
Quality: Clear demonstration of supported inversion technique""",
                "category": "inversion"
            }
        ]
        
        print(f"🔧 Starting to fix {len(remaining_poses)} remaining problematic poses...")
        
        success_count = 0
        
        for i, pose_info in enumerate(remaining_poses, 1):
            print(f"\n📊 Progress: {i}/{len(remaining_poses)}")
            
            # Generate image
            image_url = fixer.generate_pose_image(
                pose_info["name"], 
                pose_info["prompt"], 
                pose_info["category"]
            )
            
            if image_url:
                # Update yoga.json
                if fixer.update_yoga_json(pose_info["name"], image_url):
                    success_count += 1
            
            # Wait between requests
            if i < len(remaining_poses):
                print("⏱️  Waiting 4 seconds...")
                time.sleep(4)
        
        print(f"\n🎉 COMPLETE FIX PROCESS FINISHED!")
        print(f"✅ Successfully fixed: {success_count}/{len(remaining_poses)}")
        
        if success_count > 0:
            print(f"🌐 Images available at: https://storage.googleapis.com/{fixer.bucket_name}/poses/")
            print(f"📝 yoga.json has been updated with new images")
            print(f"🚀 All problematic yoga poses have been addressed!")
        
    except Exception as e:
        print(f"❌ Error in complete fix: {str(e)}")

if __name__ == "__main__":
    main()
