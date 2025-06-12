#!/usr/bin/env python3
"""
Fix Yoga Pose Images - Regenerate problematic poses with improved prompts
Focuses on failed generations and incorrect images
"""

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import os
from google.cloud import storage
from PIL import Image, ImageEnhance, ImageFilter
import io
import json
import time
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YogaPoseImageFixer:
    def __init__(self, project_id, location="us-central1"):
        self.project_id = project_id
        self.location = location
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        self.model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        # Initialize Cloud Storage client
        self.storage_client = storage.Client()
        self.bucket_name = f"{project_id}-yoga-pose-images"
        
        # Results storage
        self.results = []
        
        # Specific prompts for problematic poses
        self.pose_specific_prompts = {
            "Apanasana (Knees-to-Chest Pose)": {
                "prompt": """Professional yoga photography of a peaceful woman lying on her back on a yoga mat, gently hugging both knees to her chest with her arms wrapped around her shins. Her head is relaxed on the mat, eyes closed with a serene expression. The pose demonstrates perfect Apanasana (Wind-Relieving Pose) with knees drawn up toward the torso.

VISUAL DETAILS:
- Woman lying supine (on her back) on a clean yoga mat
- Both knees bent and drawn up to chest level
- Arms wrapped around shins, gently hugging knees
- Head resting comfortably on the mat
- Peaceful, relaxed facial expression
- Comfortable yoga attire in soft colors

SETTING:
- Clean, minimalist yoga studio with warm natural lighting
- Neutral background, focus on the pose
- Peaceful, calming atmosphere
- Professional photography lighting

TECHNICAL:
- High quality photography, sharp focus
- Warm, soft lighting from the side
- Calm, therapeutic mood
- Suitable for yoga instruction and wellness
- No text, watermarks, or distracting elements""",
                "category": "restorative"
            },
            
            "Viparita Karani (Legs-up-the-Wall Pose)": {
                "prompt": """Professional yoga photography of a relaxed woman in a therapeutic yoga pose, lying on her back with legs extended upward against a wall. Her body is in an L-shape with torso on the floor and legs straight up the wall. Arms are relaxed by her sides, palms facing up. The pose demonstrates perfect Viparita Karani for circulation and relaxation.

VISUAL DETAILS:
- Woman lying on her back on a yoga mat near a wall
- Legs straight up against the wall, forming 90-degree angle with torso
- Arms relaxed at sides, palms facing up
- Peaceful, restful expression with eyes closed
- Comfortable yoga clothing in neutral tones

SETTING:
- Peaceful yoga space with a clean wall
- Soft, natural lighting creating a calming mood
- Minimalist background focusing on the therapeutic position
- Professional wellness photography

TECHNICAL:
- Clear demonstration of the pose's alignment
- Soft, diffused lighting
- Calming, restorative atmosphere
- High quality instructional photography
- Clean, uncluttered composition""",
                "category": "restorative"
            },
            
            "Setu Bandhasana (Bridge Pose)": {
                "prompt": """Professional yoga photography of a strong woman in Bridge Pose, lying on her back with knees bent and feet planted firmly on the ground. Her hips are lifted high, creating a beautiful arch with her body supported by her feet and shoulders. Arms are pressed into the mat alongside her body for stability.

VISUAL DETAILS:
- Woman lying with upper back and shoulders on the mat
- Knees bent, feet flat on floor hip-width apart
- Hips lifted high creating a strong bridge shape
- Arms alongside body, palms pressing down for support
- Strong, confident posture demonstrating the pose

SETTING:
- Bright, airy yoga studio with natural lighting
- Clean yoga mat on wooden floor
- Energizing, uplifting atmosphere
- Professional yoga instruction photography

TECHNICAL:
- Clear view of the bridge shape and alignment
- Bright, natural lighting highlighting the pose
- Strong, empowering mood
- High quality demonstration photography
- Focus on proper form and technique""",
                "category": "backbend"
            },
            
            "Bhujangasana (Cobra Pose)": {
                "prompt": """Professional yoga photography of a graceful woman in Cobra Pose, lying face down with palms planted under her shoulders, gently lifting her chest and head upward. The pose shows a gentle backbend with the lower body remaining grounded on the mat.

VISUAL DETAILS:
- Woman lying prone (face down) on yoga mat
- Palms planted firmly under shoulders
- Chest and head gently lifted, creating gentle spinal extension
- Lower body from hips down remaining on the mat
- Graceful neck alignment, looking slightly forward
- Peaceful expression showing gentle effort

SETTING:
- Warm, inviting yoga studio with soft lighting
- Clean practice space with minimal distractions
- Natural, earthy tones creating a grounding atmosphere
- Professional instructional photography

TECHNICAL:
- Clear demonstration of gentle backbend technique
- Warm, golden lighting emphasizing the heart opening
- Gentle, strengthening energy
- High quality yoga instruction photography
- Safe, accessible pose demonstration""",
                "category": "backbend"
            },
            
            "Parivrtta Janu Sirsasana (Revolved Head-to-Knee Pose)": {
                "prompt": """Professional yoga photography of a flexible woman in a seated spinal twist, sitting with one leg extended and the other bent with foot near the inner thigh. She is gently twisting her torso over the extended leg, reaching one arm over to create a gentle side stretch and twist.

VISUAL DETAILS:
- Woman seated on yoga mat with one leg straight, one bent
- Gentle twist and side stretch over the extended leg
- One arm reaching overhead in the direction of the stretch
- Graceful spinal rotation with proper alignment
- Calm, focused expression during the twist

SETTING:
- Peaceful yoga studio with soft, natural lighting
- Clean practice space emphasizing the stretch
- Quiet, meditative atmosphere
- Professional wellness photography

TECHNICAL:
- Clear demonstration of the twisting movement
- Soft lighting highlighting the spinal rotation
- Calm, centering energy
- High quality instructional photography
- Safe, mindful pose execution""",
                "category": "twist"
            },
            
            "Parivrtta Trikonasana (Revolved Triangle Pose)": {
                "prompt": """Professional yoga photography of a balanced woman in a standing twist pose, with legs in a wide stance and one hand reaching down toward the floor while the other extends upward, creating a gentle spinal twist and triangle shape with the body.

VISUAL DETAILS:
- Woman in wide-legged standing position
- One hand reaching toward the floor, other extending upward
- Gentle spinal twist creating a triangular shape
- Strong, grounded legs maintaining stability
- Focused, balanced expression

SETTING:
- Spacious yoga studio with ample room for the pose
- Clean, uncluttered background
- Natural lighting emphasizing balance and strength
- Professional yoga instruction setting

TECHNICAL:
- Clear demonstration of the twisting triangle position
- Balanced lighting showing both strength and flexibility
- Grounded, centering energy
- High quality demonstration photography
- Emphasis on safe alignment and balance""",
                "category": "twist"
            },
            
            "Paschimottanasana (Seated Forward Bend)": {
                "prompt": """Professional yoga photography of a serene woman in a seated forward fold, sitting with legs extended straight in front, gently folding forward from the hips over her legs. Her hands rest comfortably on her legs or feet, and her spine maintains a gentle curve as she folds forward.

VISUAL DETAILS:
- Woman seated with both legs extended straight
- Gentle forward fold from the hips over the legs
- Hands resting naturally on legs, ankles, or feet
- Soft, introspective expression with eyes closed or downcast
- Peaceful, meditative quality to the pose

SETTING:
- Calm, quiet yoga space with soft lighting
- Minimalist background focusing on the forward fold
- Peaceful, introspective atmosphere
- Professional meditation and yoga photography

TECHNICAL:
- Clear view of the forward folding position
- Soft, gentle lighting creating a meditative mood
- Calm, introspective energy
- High quality instructional photography
- Emphasis on mindful, gentle stretching""",
                "category": "forward_fold"
            },
            
            "Matsyasana (Fish Pose)": {
                "prompt": """Professional yoga photography of a graceful woman in a gentle heart-opening pose, lying on her back with her chest lifted and head gently tilted back. Her elbows support her as she creates a gentle arch in her upper back, opening the chest and throat area.

VISUAL DETAILS:
- Woman lying on her back on a yoga mat
- Chest gently lifted and opened toward the ceiling
- Head tilted back in a comfortable position
- Elbows supporting the body weight
- Gentle arch in the upper back creating heart opening
- Peaceful, open expression

SETTING:
- Bright, airy yoga studio with uplifting lighting
- Clean practice space with minimal distractions
- Energizing yet peaceful atmosphere
- Professional heart-opening yoga photography

TECHNICAL:
- Clear demonstration of the gentle backbend
- Bright, uplifting lighting emphasizing the heart opening
- Open, expansive energy
- High quality yoga instruction photography
- Safe, accessible heart-opening demonstration""",
                "category": "backbend"
            },
            
            "Supta Virasana (Reclining Hero Pose)": {
                "prompt": """Professional yoga photography of a peaceful woman in a reclining position, sitting with her legs folded beneath her and then gently leaning back to rest on her elbows or fully on her back. The pose demonstrates a gentle hip and thigh stretch in a restful position.

VISUAL DETAILS:
- Woman in a kneeling position with shins on the mat
- Gently reclining backward, supported by elbows or lying flat
- Knees together, feet slightly apart
- Peaceful, restful expression
- Comfortable yoga attire

SETTING:
- Calm, supportive yoga environment
- Soft, warm lighting creating a restful mood
- Clean practice space with supportive props nearby
- Professional restorative yoga photography

TECHNICAL:
- Clear demonstration of the reclining position
- Soft, comforting lighting
- Restful, therapeutic energy
- High quality instructional photography
- Emphasis on comfort and support""",
                "category": "restorative"
            },
            
            "Salamba Sarvangasana (Supported Shoulderstand)": {
                "prompt": """Professional yoga photography of a skilled woman in a supported inversion, lying on her back with her legs extending straight upward and her body weight supported by her shoulders and upper arms. A folded blanket or bolster supports her shoulders for comfort and safety.

VISUAL DETAILS:
- Woman with shoulders on a folded blanket for support
- Legs straight up toward the ceiling
- Body weight balanced on shoulders and upper arms
- Hands supporting the middle back for stability
- Calm, focused expression

SETTING:
- Safe, supportive yoga environment with proper props
- Clean background emphasizing the inversion
- Professional therapeutic yoga setting
- Adequate space for the supported pose

TECHNICAL:
- Clear demonstration of proper shoulder support
- Balanced lighting showing stability and calm
- Safe, therapeutic energy
- High quality instruction photography
- Emphasis on proper support and alignment""",
                "category": "inversion"
            }
        }
    
    def _enhance_image(self, image):
        """Apply subtle enhancements to the generated image"""
        try:
            # Subtle brightness adjustment
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.05)
            
            # Slight contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.08)
            
            # Subtle color enhancement
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.03)
            
            # Gentle sharpening
            image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=30, threshold=3))
            
            return image
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}")
            return image
    
    def regenerate_pose_image(self, pose_name):
        """Regenerate image for a specific pose with improved prompt"""
        try:
            if pose_name not in self.pose_specific_prompts:
                logger.error(f"No specific prompt available for: {pose_name}")
                return None
            
            logger.info(f"\n🔄 Regenerating image for: {pose_name}")
            
            pose_info = self.pose_specific_prompts[pose_name]
            prompt = pose_info["prompt"]
            category = pose_info["category"]
            
            logger.info(f"📝 Category: {category}")
            logger.info(f"🎯 Using specialized prompt for this pose...")
            
            # Generate image with enhanced parameters
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="block_only_high",  # Less restrictive
                person_generation="allow_adult",
                language="en",
                guidance_scale=15,  # Balanced guidance
                negative_prompt="inappropriate, dark, distorted, low quality, blurry, text, watermarks"
            )
            
            if not response.images:
                logger.error(f"❌ No images generated for {pose_name}")
                return None
            
            # Get the generated image
            generated_image = response.images[0]
            
            # Convert to PIL Image
            image_bytes = generated_image._image_bytes
            image = Image.open(io.BytesIO(image_bytes))
            
            # Apply enhancements
            image = self._enhance_image(image)
            
            # Resize to standard dimensions
            image = image.resize((512, 512), Image.Resampling.LANCZOS)
            
            # Save to buffer
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=90, optimize=True)
            buffer.seek(0)
            
            # Create safe filename
            safe_name = pose_name.lower()
            safe_name = ''.join(c for c in safe_name if c.isalnum() or c in (' ', '-', '_'))
            safe_name = safe_name.replace(' ', '_').replace('-', '_')
            safe_name = safe_name.split('(')[0].strip('_')
            filename = f"yoga_pose_{safe_name}.jpg"
            
            # Upload to Cloud Storage
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(f"poses/{filename}")
            blob.upload_from_string(buffer.getvalue(), content_type='image/jpeg')
            blob.make_public()
            
            # Get public URL
            public_url = blob.public_url
            logger.info(f"✅ Image regenerated successfully: {public_url}")
            
            # Store result
            result = {
                'pose_name': pose_name,
                'filename': filename,
                'url': public_url,
                'category': category,
                'success': True,
                'regenerated': True,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error regenerating image for {pose_name}: {str(e)}")
            return None
    
    def fix_problematic_poses(self):
        """Fix all problematic poses identified by the user"""
        
        # List of poses to fix
        poses_to_fix = [
            "Apanasana (Knees-to-Chest Pose)",  # Incorrect image
            "Viparita Karani (Legs-up-the-Wall Pose)",  # Failed generation
            "Setu Bandhasana (Bridge Pose)",  # Failed generation
            "Bhujangasana (Cobra Pose)",  # Failed generation
            "Parivrtta Janu Sirsasana (Revolved Head-to-Knee Pose)",  # Failed generation
            "Parivrtta Trikonasana (Revolved Triangle Pose)",  # Failed generation
            "Paschimottanasana (Seated Forward Bend)",  # Failed generation
            "Matsyasana (Fish Pose)",  # Failed generation
            "Supta Virasana (Reclining Hero Pose)",  # Failed generation
            "Salamba Sarvangasana (Supported Shoulderstand)"  # Failed generation
        ]
        
        logger.info(f"🔧 Starting to fix {len(poses_to_fix)} problematic poses...")
        
        fixed_results = []
        
        for i, pose_name in enumerate(poses_to_fix, 1):
            logger.info(f"\n📊 Progress: {i}/{len(poses_to_fix)}")
            
            result = self.regenerate_pose_image(pose_name)
            if result:
                fixed_results.append(result)
                self.results.append(result)
            
            # Add delay between requests
            if i < len(poses_to_fix):
                logger.info("⏱️  Waiting 3 seconds before next generation...")
                time.sleep(3)
        
        # Save results
        self._save_results(fixed_results)
        
        # Update yoga.json with the new images
        self._update_yoga_json(fixed_results)
        
        return fixed_results
    
    def _save_results(self, results):
        """Save regeneration results to a JSON file"""
        try:
            results_file = 'yoga_pose_regeneration_results.json'
            with open(results_file, 'w') as f:
                json.dump({
                    'regeneration_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_regenerated': len(results),
                    'successful_regenerations': len([r for r in results if r and r.get('success', False)]),
                    'failed_regenerations': len([r for r in results if not r or not r.get('success', False)]),
                    'bucket_name': self.bucket_name,
                    'results': results
                }, f, indent=2)
            
            logger.info(f"📄 Regeneration results saved to: {results_file}")
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {str(e)}")
    
    def _update_yoga_json(self, results):
        """Update yoga.json with the newly generated images"""
        try:
            # Load current yoga.json
            with open('static/data/yoga.json', 'r', encoding='utf-8') as f:
                yoga_poses = json.load(f)
            
            # Create mapping of successful regenerations
            image_mapping = {}
            for result in results:
                if result and result.get('success', False):
                    image_mapping[result['pose_name']] = result['url']
            
            # Update yoga poses with new image URLs
            updated_count = 0
            for pose in yoga_poses:
                pose_name = pose.get('name', '')
                if pose_name in image_mapping:
                    pose['image'] = image_mapping[pose_name]
                    updated_count += 1
                    logger.info(f"✅ Updated image URL for: {pose_name}")
            
            # Save updated file
            with open('static/data/yoga.json', 'w', encoding='utf-8') as f:
                json.dump(yoga_poses, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Updated yoga.json with {updated_count} new images")
            
        except Exception as e:
            logger.error(f"❌ Error updating yoga.json: {str(e)}")

def main():
    """Main function to fix problematic yoga pose images"""
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'your-project-id')
    
    if PROJECT_ID == 'your-project-id':
        logger.error("❌ Please set GOOGLE_CLOUD_PROJECT_ID environment variable")
        return
    
    try:
        logger.info("🔧 Starting Yoga Pose Image Fix Process...")
        logger.info(f"📋 Project ID: {PROJECT_ID}")
        
        # Initialize fixer
        fixer = YogaPoseImageFixer(PROJECT_ID)
        
        # Fix problematic poses
        results = fixer.fix_problematic_poses()
        
        # Print summary
        successful = len([r for r in results if r and r.get('success', False)])
        failed = len(results) - successful
        
        logger.info(f"\n🎉 FIX PROCESS COMPLETE!")
        logger.info(f"✅ Successfully regenerated: {successful}")
        logger.info(f"❌ Still failed: {failed}")
        logger.info(f"📊 Total attempted: {len(results)}")
        
        if successful > 0:
            logger.info(f"🌐 New images available at: https://storage.googleapis.com/{fixer.bucket_name}/poses/")
            logger.info(f"📝 Yoga.json updated with new image URLs")
            
    except Exception as e:
        logger.error(f"❌ Error in fix process: {str(e)}")

if __name__ == "__main__":
    main()
