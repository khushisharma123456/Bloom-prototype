#!/usr/bin/env python3
"""
Quick Fix for Specific Yoga Poses
Regenerates individual poses with better prompts
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

class QuickYogaFixer:
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
            
            # Generate image
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="block_only_high",
                person_generation="allow_adult",
                language="en",
                guidance_scale=15,
                negative_prompt="inappropriate, dark, distorted, low quality, blurry, text, watermarks"
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
            filename = f"yoga_pose_{safe_name.split('_')[0]}.jpg"
            
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
    """Fix the most critical poses"""
    try:
        fixer = QuickYogaFixer()
          # Define ALL the poses to fix with improved prompts
        poses_to_fix = [
            {
                "name": "Apanasana (Knees-to-Chest Pose)",
                "prompt": """Professional yoga photography of a peaceful woman lying on her back on a yoga mat, gently hugging both knees to her chest with her arms wrapped around her shins. Her head is relaxed on the mat with eyes closed. The pose shows perfect Apanasana technique - lying supine with knees drawn to chest for digestive relief.

Visual: Woman on her back, both knees bent and pulled to chest, arms embracing shins, head on mat, serene expression
Setting: Clean yoga studio, warm natural lighting, minimal background
Style: Therapeutic, calming, professional yoga instruction photography
Quality: High resolution, soft lighting, peaceful mood""",
                "category": "restorative"
            },
            {
                "name": "Viparita Karani (Legs-up-the-Wall Pose)",
                "prompt": """Professional yoga photography of a relaxed woman in therapeutic pose, lying on her back with legs extended straight up against a wall. Her body forms an L-shape with torso on the floor and legs vertical against the wall. Arms rest comfortably by her sides. Perfect Viparita Karani for circulation.

Visual: Woman lying on back near wall, legs straight up wall, arms relaxed at sides, peaceful expression
Setting: Clean yoga space with neutral wall, soft lighting
Style: Therapeutic, restorative, professional wellness photography  
Quality: Clear pose demonstration, calming atmosphere""",
                "category": "restorative"
            },
            {
                "name": "Setu Bandhasana (Bridge Pose)",
                "prompt": """Professional yoga photography of a strong woman in Bridge Pose, lying on her back with knees bent and feet flat on the floor. Her hips are lifted high creating a bridge arch, with upper back and shoulders on the mat. Arms are alongside her body pressing down for support.

Visual: Woman with hips lifted high, knees bent, feet planted, shoulders on mat, strong bridge shape
Setting: Bright yoga studio with natural lighting
Style: Energizing, strengthening, professional yoga instruction
Quality: Clear bridge position, uplifting mood, proper alignment shown""",
                "category": "backbend"
            },
            {
                "name": "Bhujangasana (Cobra Pose)",
                "prompt": """Professional yoga photography of a graceful woman in Cobra Pose, lying face down with palms planted under her shoulders, gently lifting her chest and head upward. The pose shows a gentle backbend with the lower body remaining grounded on the mat. Arms are straight, chest open, looking slightly forward.

Visual: Woman prone position, palms under shoulders, chest lifted, gentle arch, lower body on mat
Setting: Warm yoga studio with golden lighting
Style: Heart-opening, strengthening, professional instruction
Quality: Clear backbend demonstration, energizing mood""",
                "category": "backbend"
            },
            {
                "name": "Parivrtta Janu Sirsasana (Revolved Head-to-Knee Pose)",
                "prompt": """Professional yoga photography of a flexible woman in a seated spinal twist, sitting with one leg extended and the other bent. She is gently twisting her torso over the extended leg, reaching one arm over to create a gentle side stretch and twist. Peaceful expression showing mindful movement.

Visual: Woman seated, one leg straight, one bent, gentle twist over extended leg, arm reaching
Setting: Peaceful yoga studio with soft lighting
Style: Meditative, stretching, professional wellness
Quality: Clear twist demonstration, calm centering energy""",
                "category": "twist"
            },
            {
                "name": "Parivrtta Trikonasana (Revolved Triangle Pose)",
                "prompt": """Professional yoga photography of a balanced woman in a standing twist pose, with legs in a wide stance and one hand reaching toward the floor while the other extends upward, creating a gentle spinal twist and triangle shape with the body. Strong grounded legs.

Visual: Woman wide stance, one hand down, one up, spinal twist, triangle shape
Setting: Spacious yoga studio with natural lighting
Style: Balancing, twisting, professional instruction
Quality: Clear triangle twist position, grounded strength""",
                "category": "twist"
            },
            {
                "name": "Paschimottanasana (Seated Forward Bend)",
                "prompt": """Professional yoga photography of a serene woman in a seated forward fold, sitting with legs extended straight in front, gently folding forward from the hips over her legs. Her hands rest comfortably on her legs, spine in gentle curve. Eyes closed in meditation.

Visual: Woman seated, legs straight, forward fold from hips, hands on legs, peaceful expression
Setting: Calm yoga space with soft lighting
Style: Introspective, meditative, professional wellness
Quality: Clear forward fold position, peaceful introspective mood""",
                "category": "forward_fold"
            },
            {
                "name": "Matsyasana (Fish Pose)",
                "prompt": """Professional yoga photography of a graceful woman in a gentle heart-opening pose, lying on her back with her chest lifted and supported by her elbows. Her head is gently tilted back in a comfortable position, creating a gentle arch in the upper back and opening the chest area.

Visual: Woman on back, chest lifted, elbows supporting, head back, gentle upper back arch
Setting: Bright airy yoga studio with uplifting lighting
Style: Heart-opening, expansive, professional instruction
Quality: Clear heart opening demonstration, uplifting energy""",
                "category": "backbend"
            },
            {
                "name": "Supta Virasana (Reclining Hero Pose)",
                "prompt": """Professional yoga photography of a peaceful woman in a reclining position, sitting with her legs folded beneath her and then gently leaning back to rest on her elbows. The pose demonstrates a gentle hip and thigh stretch in a restful position with comfortable support.

Visual: Woman kneeling position, reclining back on elbows, legs folded under, peaceful rest
Setting: Calm supportive yoga environment with soft lighting
Style: Restful, therapeutic, professional wellness
Quality: Clear reclining position, comfortable supportive mood""",
                "category": "restorative"
            },
            {
                "name": "Salamba Sarvangasana (Supported Shoulderstand)",
                "prompt": """Professional yoga photography of a skilled woman in a supported inversion, lying with her shoulders on a folded blanket and her legs extending straight upward. Her body weight is supported by her shoulders and upper arms, with hands supporting the middle back for stability.

Visual: Woman shoulders on blanket, legs straight up, hands supporting back, stable inversion
Setting: Safe supportive yoga environment with proper props
Style: Therapeutic, balancing, professional instruction
Quality: Clear supported inversion, safe therapeutic energy""",
                "category": "inversion"
            }
        ]
        
        print(f"🔧 Starting to fix {len(poses_to_fix)} critical poses...")
        
        success_count = 0
        
        for i, pose_info in enumerate(poses_to_fix, 1):
            print(f"\n📊 Progress: {i}/{len(poses_to_fix)}")
            
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
            if i < len(poses_to_fix):
                print("⏱️  Waiting 3 seconds...")
                time.sleep(3)
        
        print(f"\n🎉 QUICK FIX COMPLETE!")
        print(f"✅ Successfully fixed: {success_count}/{len(poses_to_fix)}")
        
        if success_count > 0:
            print(f"🌐 Images available at: https://storage.googleapis.com/{fixer.bucket_name}/poses/")
            print(f"📝 yoga.json has been updated with new images")
        
    except Exception as e:
        print(f"❌ Error in quick fix: {str(e)}")

if __name__ == "__main__":
    main()
