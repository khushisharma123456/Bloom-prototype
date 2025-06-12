#!/usr/bin/env python3
"""
Yoga Pose Image Generator for Bloom - AI-Generated Yoga Pose Images
Generates beautiful, professional AI images for all yoga poses using Google Cloud Vertex AI
"""

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import os
from google.cloud import storage
import base64
from PIL import Image, ImageEnhance, ImageFilter
import io
import json
import requests
from dotenv import load_dotenv
import time
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YogaPoseImageGenerator:
    def __init__(self, project_id, location="us-central1"):
        self.project_id = project_id
        self.location = location
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        self.model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        # Initialize Cloud Storage client
        self.storage_client = storage.Client()
        self.bucket_name = f"{project_id}-yoga-pose-images"
        self._ensure_bucket_exists()
        
        # Results storage
        self.results = []
        
        # Enhanced style mappings for different yoga pose categories
        self.pose_style_mappings = {
            # Restorative/Calming poses
            'restorative': {
                'style': 'peaceful woman in comfortable yoga pose, serene expression, soft natural lighting',
                'background': 'minimalist yoga studio with wooden floor, plants, soft natural lighting',
                'props': 'yoga mat, bolsters, soft cushions, peaceful environment',
                'mood': 'calm, peaceful, nurturing, healing'
            },
            
            # Standing poses
            'standing': {
                'style': 'confident woman in strong standing yoga pose, balanced and grounded',
                'background': 'modern yoga studio with large windows, natural light',
                'props': 'yoga mat, clean space, minimal aesthetic',
                'mood': 'strong, balanced, focused, empowered'
            },
            
            # Seated poses
            'seated': {
                'style': 'graceful woman in seated yoga pose, spine straight, meditative posture',
                'background': 'quiet meditation space with soft lighting',
                'props': 'yoga mat, meditation cushion, serene environment',
                'mood': 'centered, grounded, introspective, calm'
            },
            
            # Backbends
            'backbend': {
                'style': 'flexible woman in heart-opening backbend pose, chest open, graceful arch',
                'background': 'bright airy yoga studio with natural elements',
                'props': 'yoga mat, yoga blocks for support',
                'mood': 'open, energizing, uplifting, confident'
            },
            
            # Forward folds
            'forward_fold': {
                'style': 'woman in calming forward fold pose, introspective, releasing tension',
                'background': 'peaceful yoga space with soft warm lighting',
                'props': 'yoga mat, yoga strap if needed, calming environment',
                'mood': 'releasing, calming, introspective, grounding'
            },
            
            # Twists
            'twist': {
                'style': 'woman in spinal twist pose, healthy rotation, balanced alignment',
                'background': 'clean yoga studio with neutral colors',
                'props': 'yoga mat, yoga block for support',
                'mood': 'detoxifying, balancing, centering, cleansing'
            },
            
            # Inversions
            'inversion': {
                'style': 'skilled woman in safe inversion pose, legs elevated, peaceful expression',
                'background': 'supportive yoga environment with wall support',
                'props': 'yoga mat, wall support, blanket for comfort',
                'mood': 'rejuvenating, calming, restorative, therapeutic'
            },
            
            # Prone poses (lying face down)
            'prone': {
                'style': 'woman in gentle prone yoga pose, chest opening, strengthening',
                'background': 'clean yoga mat in peaceful studio',
                'props': 'yoga mat, minimal props, clean space',
                'mood': 'strengthening, opening, energizing, focusing'
            }
        }
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            if not bucket.exists():
                bucket = self.storage_client.create_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except Exception as e:
            logger.warning(f"Bucket operation warning: {e}")
    
    def _categorize_pose(self, pose_name, steps):
        """Determine the category of yoga pose for styling"""
        name_lower = pose_name.lower()
        steps_text = ' '.join(steps).lower() if steps else ''
        
        # Categorize based on pose name and steps
        if any(keyword in name_lower for keyword in ['reclining', 'supine', 'legs-up', 'child', 'corpse', 'bound angle']):
            return 'restorative'
        elif any(keyword in name_lower for keyword in ['standing', 'tree', 'warrior', 'mountain']):
            return 'standing'
        elif any(keyword in name_lower for keyword in ['seated', 'sitting', 'cross-legged', 'lotus']):
            return 'seated'
        elif any(keyword in name_lower for keyword in ['bridge', 'camel', 'wheel', 'cobra', 'fish']):
            return 'backbend'
        elif any(keyword in name_lower for keyword in ['forward', 'fold', 'head-to-knee']):
            return 'forward_fold'
        elif any(keyword in name_lower for keyword in ['twist', 'revolved', 'spiral']):
            return 'twist'
        elif any(keyword in name_lower for keyword in ['inversion', 'legs-up', 'shoulder stand', 'headstand']):
            return 'inversion'
        elif any(keyword in steps_text for keyword in ['lie face down', 'lying face down', 'prone']):
            return 'prone'
        elif any(keyword in steps_text for keyword in ['lie on your back', 'lying on back']):
            return 'restorative'
        else:
            # Default to seated for unknown poses
            return 'seated'
    
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
    
    def generate_yoga_pose_prompt(self, pose_data):
        """Generate detailed prompt for yoga pose image"""
        pose_name = pose_data.get('name', 'Unknown Pose')
        steps = pose_data.get('steps', [])
        benefits = pose_data.get('benefits', [])
        
        # Determine pose category
        category = self._categorize_pose(pose_name, steps)
        style_info = self.pose_style_mappings[category]
        
        # Extract the core pose name (remove parenthetical Sanskrit/English)
        core_name = pose_name.split('(')[0].strip()
        
        # Create detailed prompt
        prompt = f"""Professional yoga photography of {style_info['style']} demonstrating {core_name}.

POSE DETAILS:
- Woman practicing {core_name} with perfect alignment and form
- {style_info['mood']} energy and expression
- Proper yoga technique and safe positioning

VISUAL STYLE:
- {style_info['background']}
- {style_info['props']}
- Professional yoga photography lighting
- Clean, minimalist aesthetic
- Peaceful and inspiring atmosphere

TECHNICAL REQUIREMENTS:
- High quality photography, 4K resolution
- Professional studio lighting, soft and natural
- Beautiful yoga practitioner demonstrating proper form
- Inspirational and calming mood
- Suitable for wellness and yoga instruction
- Clean background, focus on the pose
- Warm, inviting color palette with soft earth tones

AVOID:
- Text, watermarks, or logos
- Dark or cluttered backgrounds
- Poor form or unsafe positioning
- Distracting elements
- Overly dramatic lighting"""

        return prompt, category
    
    def generate_and_save_image(self, pose_data):
        """Generate and save enhanced image for a single yoga pose"""
        try:
            pose_name = pose_data.get('name', 'Unknown Pose')
            logger.info(f"\n🧘‍♀️ Generating image for: {pose_name}")
            
            # Generate enhanced prompt
            prompt, category = self.generate_yoga_pose_prompt(pose_data)
            logger.info(f"📝 Category: {category}")
            logger.info(f"🎯 Prompt: {prompt[:120]}...")
            
            # Generate image with enhanced parameters
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="block_few",
                person_generation="allow_adult",
                # Enhanced parameters for better quality
                language="en",
                guidance_scale=20,  # Higher guidance for better prompt adherence
                negative_prompt="text, letters, words, watermark, low quality, blurry, dark, distorted, inappropriate, violent"
            )
            
            if not response.images:
                raise Exception("No images generated")
            
            # Get the generated image
            generated_image = response.images[0]
            
            # Convert to PIL Image
            image_bytes = generated_image._image_bytes
            image = Image.open(io.BytesIO(image_bytes))
            
            # Apply enhancements
            image = self._enhance_image(image)
            
            # Resize to standard dimensions (512x512 for optimal quality)
            image = image.resize((512, 512), Image.Resampling.LANCZOS)
            
            # Save to buffer
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=90, optimize=True)
            buffer.seek(0)
            
            # Create safe filename
            safe_name = pose_name.lower()
            # Remove special characters and replace spaces
            safe_name = ''.join(c for c in safe_name if c.isalnum() or c in (' ', '-', '_'))
            safe_name = safe_name.replace(' ', '_').replace('-', '_')
            # Remove parenthetical parts
            safe_name = safe_name.split('(')[0].strip('_')
            filename = f"yoga_pose_{safe_name}.jpg"
            
            # Upload to Cloud Storage
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(f"poses/{filename}")
            blob.upload_from_string(buffer.getvalue(), content_type='image/jpeg')
            
            # Make the blob publicly readable
            blob.make_public()
            
            # Get public URL
            public_url = blob.public_url
            logger.info(f"✅ Image saved: {public_url}")
            
            # Store result
            result = {
                'pose_name': pose_name,
                'filename': filename,
                'url': public_url,
                'category': category,
                'success': True,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.results.append(result)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating image for {pose_name}: {str(e)}")
            
            # Store failed result
            result = {
                'pose_name': pose_name,
                'filename': None,
                'url': None,
                'category': None,
                'success': False,
                'error': str(e),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.results.append(result)
            return result
    
    def generate_all_pose_images(self, yoga_data):
        """Generate images for all yoga poses"""
        logger.info(f"🚀 Starting image generation for {len(yoga_data)} yoga poses...")
        
        for i, pose_data in enumerate(yoga_data, 1):
            logger.info(f"\n📊 Progress: {i}/{len(yoga_data)}")
            
            try:
                result = self.generate_and_save_image(pose_data)
                
                # Add delay between requests to avoid rate limits
                if i < len(yoga_data):
                    logger.info("⏱️  Waiting 3 seconds before next generation...")
                    time.sleep(3)
                    
            except Exception as e:
                logger.error(f"❌ Failed to process pose {i}: {str(e)}")
                continue
        
        # Save results to file
        self._save_results()
        return self.results
    
    def _save_results(self):
        """Save generation results to a JSON file"""
        try:
            results_file = 'yoga_pose_images_results.json'
            with open(results_file, 'w') as f:
                json.dump({
                    'generation_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_poses': len(self.results),
                    'successful_generations': len([r for r in self.results if r['success']]),
                    'failed_generations': len([r for r in self.results if not r['success']]),
                    'bucket_name': self.bucket_name,
                    'results': self.results
                }, f, indent=2)
            
            logger.info(f"📄 Results saved to: {results_file}")
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {str(e)}")
    
    def update_yoga_json_with_images(self, yoga_json_path, output_path=None):
        """Update the yoga.json file with generated image URLs"""
        try:
            # Load original yoga poses
            with open(yoga_json_path, 'r', encoding='utf-8') as f:
                yoga_poses = json.load(f)
            
            # Create a mapping of pose names to image URLs
            image_mapping = {}
            for result in self.results:
                if result['success']:
                    image_mapping[result['pose_name']] = result['url']
            
            # Update yoga poses with image URLs
            updated_poses = []
            updated_count = 0
            for pose in yoga_poses:
                pose_name = pose.get('name', '')
                if pose_name in image_mapping:
                    pose['image'] = image_mapping[pose_name]
                    updated_count += 1
                    logger.info(f"✅ Added image URL for: {pose_name}")
                else:
                    # Keep existing image if available, or use default
                    if 'image' not in pose:
                        pose['image'] = '/static/Images/meditation-figure.png'
                    logger.warning(f"⚠️  Using default image for: {pose_name}")
                updated_poses.append(pose)
            
            # Save updated file
            output_file = output_path or yoga_json_path
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(updated_poses, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Updated yoga.json saved to: {output_file}")
            logger.info(f"🖼️  Updated {updated_count} poses with AI-generated images")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating yoga.json: {str(e)}")
            return False

def main():
    """Main function to generate images for all yoga poses"""
    # Configuration - Updated to match .env file variable name
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'your-project-id')
    
    if PROJECT_ID == 'your-project-id':
        logger.error("❌ Please set GOOGLE_CLOUD_PROJECT_ID environment variable")
        return
    
    try:
        # Load yoga data
        logger.info("📚 Loading yoga poses data...")
        with open('static/data/yoga.json', 'r', encoding='utf-8') as f:
            yoga_data = json.load(f)
        
        logger.info(f"✅ Loaded {len(yoga_data)} yoga poses")
        
        # Initialize generator
        generator = YogaPoseImageGenerator(PROJECT_ID)
          # Generate all images
        results = generator.generate_all_pose_images(yoga_data)
        
        # Update yoga.json with generated image URLs
        if results:
            yoga_json_path = 'static/data/yoga.json'
            generator.update_yoga_json_with_images(yoga_json_path)
        
        # Print summary
        successful = len([r for r in results if r['success']])
        failed = len([r for r in results if not r['success']])
        
        logger.info(f"\n🎉 GENERATION COMPLETE!")
        logger.info(f"✅ Successful: {successful}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"📊 Total: {len(results)}")
        
        if successful > 0:
            logger.info(f"🌐 Images available at: https://storage.googleapis.com/{generator.bucket_name}/poses/")
            logger.info(f"📝 Yoga.json updated with generated image URLs")
            
    except Exception as e:
        logger.error(f"❌ Error in main execution: {str(e)}")

if __name__ == "__main__":
    main()
