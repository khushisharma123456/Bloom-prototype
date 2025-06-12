#!/usr/bin/env python3
"""
Enhanced Recipe Image Generator for Bloom - Ayurvedic Remedies & Healthy Recipes
Generates beautiful, professional AI images for all recipes using Google Cloud Vertex AI
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

class EnhancedRecipeImageGenerator:
    def __init__(self, project_id, location="us-central1"):
        self.project_id = project_id
        self.location = location
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        self.model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        # Initialize Cloud Storage client
        self.storage_client = storage.Client()
        self.bucket_name = f"{project_id}-recipe-images"
        self._ensure_bucket_exists()
        
        # Results storage
        self.results = []
        
        # Enhanced style mappings for different recipe types
        self.style_mappings = {
            # Bloating remedies
            'bloating': {
                'style': 'warm herbal tea in elegant glass cup with steam, golden amber liquid, soothing warm lighting',
                'background': 'clean white marble surface with soft natural lighting',
                'props': 'dried herbs, wooden spoon, natural elements'
            },
            # Hormone balance remedies  
            'hormone balance': {
                'style': 'elegant wellness drink in beautiful glass, rich green or golden color, serene presentation',
                'background': 'minimalist spa-like setting with soft natural lighting',
                'props': 'fresh herbs, wooden elements, natural stones'
            },
            # Pain relief remedies
            'pain relief': {
                'style': 'comforting warm beverage with healing golden color, steam rising, nurturing presentation',
                'background': 'cozy wooden table with soft warm lighting',
                'props': 'ginger root, honey, cinnamon, healing spices'
            },
            # Energy boost foods
            'energy boost': {
                'style': 'vibrant energizing smoothie or food with bright colors, fresh appearance, uplifting presentation',
                'background': 'bright clean kitchen counter with natural daylight',
                'props': 'fresh fruits, nuts, seeds, energizing ingredients'
            },
            # Iron-rich foods
            'iron-rich': {
                'style': 'rich dark leafy greens, deep red colors, nutritious wholesome appearance',
                'background': 'rustic wooden board with natural lighting',
                'props': 'spinach leaves, beetroot, iron-rich ingredients'
            },
            # Anti-inflammatory
            'anti-inflammatory': {
                'style': 'golden turmeric-colored drink or food, warm healing colors, therapeutic appearance',
                'background': 'natural stone surface with soft lighting',
                'props': 'turmeric root, golden spices, healing herbs'
            },
            # Digestive
            'digestive': {
                'style': 'fresh colorful soup or herbal preparation, appetizing steam, digestive herbs visible',
                'background': 'clean white bowl on wooden surface',
                'props': 'fresh herbs, digestive spices, natural elements'
            },
            # Protein-rich
            'protein': {
                'style': 'hearty protein-rich dish with legumes, nuts, wholesome appearance',
                'background': 'rustic kitchen setting with warm lighting',
                'props': 'lentils, chickpeas, protein sources'
            },
            # Hydration
            'hydration': {
                'style': 'refreshing clear drink with fruits, sparkling appearance, thirst-quenching look',
                'background': 'bright clean surface with fresh lighting',
                'props': 'coconut, chia seeds, fresh fruits, water droplets'
            },
            # Mood boost
            'mood boost': {
                'style': 'rich chocolate-colored treat or drink, indulgent but healthy appearance',
                'background': 'cozy setting with warm ambient lighting',
                'props': 'dark chocolate, cocoa, mood-lifting ingredients'
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
    
    def _get_recipe_category(self, badge, ingredients):
        """Determine recipe category from badge and ingredients"""
        badge_lower = badge.lower()
        
        # Check for specific categories
        if 'bloating' in badge_lower:
            return 'bloating'
        elif 'hormone' in badge_lower or 'hormonal' in badge_lower:
            return 'hormone balance'
        elif 'pain' in badge_lower:
            return 'pain relief'
        elif 'energy' in badge_lower:
            return 'energy boost'
        elif 'iron' in badge_lower:
            return 'iron-rich'
        elif 'anti-inflammatory' in badge_lower:
            return 'anti-inflammatory'
        elif 'digestive' in badge_lower:
            return 'digestive'
        elif 'protein' in badge_lower:
            return 'protein'
        elif 'hydration' in badge_lower:
            return 'hydration'
        elif 'mood' in badge_lower:
            return 'mood boost'
        
        # Check ingredients for category hints
        ingredients_text = ' '.join(ingredients).lower()
        if 'turmeric' in ingredients_text or 'ginger' in ingredients_text:
            return 'anti-inflammatory'
        elif 'spinach' in ingredients_text or 'beetroot' in ingredients_text:
            return 'iron-rich'
        elif 'protein' in ingredients_text or 'dal' in ingredients_text:
            return 'protein'
        elif 'coconut water' in ingredients_text or 'water' in ingredients_text:
            return 'hydration'
        
        return 'hormone balance'  # Default for Ayurvedic remedies
    
    def generate_enhanced_prompt(self, recipe_data):
        """Generate an enhanced, detailed prompt for recipe image"""
        name = recipe_data.get('name', 'Unknown Recipe')
        description = recipe_data.get('description', '')
        badge = recipe_data.get('badge', '')
        ingredients = recipe_data.get('ingredients', [])
        
        # Extract main ingredients for visual context
        main_ingredients = []
        if ingredients:
            for ingredient in ingredients[:4]:  # Use first 4 ingredients
                ingredient_clean = ingredient.lower().split('(')[0].strip()
                # Clean up measurements
                ingredient_clean = ' '.join([word for word in ingredient_clean.split() 
                                           if not any(char.isdigit() for char in word)])
                if ingredient_clean:
                    main_ingredients.append(ingredient_clean)
        
        ingredients_text = ", ".join(main_ingredients) if main_ingredients else "natural ayurvedic ingredients"
        
        # Get category-specific styling
        category = self._get_recipe_category(badge, ingredients)
        style_info = self.style_mappings.get(category, self.style_mappings['hormone balance'])
        
        # Create comprehensive prompt
        prompt = f"""Professional food photography of {name}, {style_info['style']}, 
        beautifully featuring {ingredients_text}, {style_info['background']}, 
        high-end food styling, natural lighting, appetizing and fresh appearance,
        {description}, ayurvedic wellness aesthetic, {style_info['props']},
        shot from 45 degree angle, minimal clean props, sophisticated presentation,
        high resolution 4K quality, restaurant-quality plating, Instagram-worthy,
        warm natural colors, healing and nourishing visual appeal, professional studio lighting,
        depth of field, food magazine quality, elegant composition"""
        
        return prompt, category
    
    def _enhance_image(self, image):
        """Apply subtle enhancements to the generated image"""
        try:
            # Slightly enhance contrast and color saturation
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)
            
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.05)
            
            # Subtle sharpening
            image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=50, threshold=3))
            
            return image
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}")
            return image
    
    def generate_and_save_image(self, recipe_data):
        """Generate and save enhanced image for a single recipe"""
        try:
            recipe_name = recipe_data.get('name', 'Unknown Recipe')
            logger.info(f"\n🎨 Generating image for: {recipe_name}")
            
            # Generate enhanced prompt
            prompt, category = self.generate_enhanced_prompt(recipe_data)
            logger.info(f"📝 Category: {category}")
            logger.info(f"🎯 Prompt: {prompt[:120]}...")
            
            # Generate image with enhanced parameters
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="block_few",
                person_generation="dont_allow",
                # Enhanced parameters for better quality
                language="en",
                guidance_scale=15,  # Higher guidance for better prompt adherence
                negative_prompt="text, letters, words, watermark, low quality, blurry, dark, ugly"
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
            
            # Resize to standard dimensions (500x500 for better quality)
            image = image.resize((500, 500), Image.Resampling.LANCZOS)
            
            # Save to buffer
            buffer = io.BytesIO()
            image.save(buffer, format='PNG', quality=98)
            buffer.seek(0)
            
            # Create descriptive filename
            safe_name = "".join(c for c in recipe_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '-').lower()
            filename = f"recipe_{safe_name}.png"
            
            # Save locally
            local_path = f"static/Images/{filename}"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            buffer.seek(0)
            with open(local_path, 'wb') as f:
                f.write(buffer.read())
            
            # Try to upload to Cloud Storage (optional, don't fail if it doesn't work)
            cloud_url = None
            try:
                blob = self.storage_client.bucket(self.bucket_name).blob(filename)
                buffer.seek(0)
                blob.upload_from_file(buffer, content_type='image/png')
                blob.make_public()
                cloud_url = blob.public_url
            except Exception as e:
                logger.warning(f"Cloud upload failed (continuing anyway): {e}")
            
            result = {
                'success': True,
                'recipe_name': recipe_name,
                'filename': filename,
                'local_path': local_path,
                'cloud_url': cloud_url,
                'category': category,
                'prompt': prompt
            }
            
            logger.info(f"✅ Success: {recipe_name} -> {filename}")
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'recipe_name': recipe_data.get('name', 'Unknown'),
                'error': str(e)
            }
            logger.error(f"❌ Error generating image for {recipe_data.get('name', 'Unknown')}: {e}")
            return error_result
    
    def load_recipes_from_json(self):
        """Load recipes from recipes.json"""
        try:
            recipes_path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'recipes.json')
            with open(recipes_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('remedies', [])
        except Exception as e:
            logger.error(f"Error loading recipes: {e}")
            return []
    
    def generate_all_recipe_images(self):
        """Generate enhanced images for all recipes"""
        recipes = self.load_recipes_from_json()
        
        if not recipes:
            logger.error("No recipes found!")
            return
        
        logger.info(f"🚀 Found {len(recipes)} recipes to generate images for...")
        logger.info("🎨 Using Enhanced AI Image Generation with Professional Styling")
        
        for i, recipe in enumerate(recipes, 1):
            logger.info(f"\n--- Processing {i}/{len(recipes)} ---")
            result = self.generate_and_save_image(recipe)
            self.results.append(result)
            
            # Delay to avoid rate limits
            if i < len(recipes):  # Don't delay after the last one
                logger.info("⏳ Waiting 3 seconds to avoid rate limits...")
                time.sleep(3)
        
        # Save results
        self.save_results()
        self.update_recipes_json()
        
        # Print comprehensive summary
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        logger.info(f"\n🎉 Enhanced Image Generation Complete!")
        logger.info(f"✅ Successful: {len(successful)}")
        logger.info(f"❌ Failed: {len(failed)}")
        
        if successful:
            logger.info("\n✅ Successfully Generated:")
            for result in successful:
                logger.info(f"   📸 {result['recipe_name']} -> {result['filename']}")
        
        if failed:
            logger.info("\n❌ Failed to Generate:")
            for result in failed:
                logger.info(f"   💥 {result['recipe_name']}: {result['error']}")
        
        logger.info(f"\n📄 Results saved to enhanced_recipe_images_results.json")
    
    def save_results(self):
        """Save generation results to JSON file"""
        results_path = os.path.join(os.path.dirname(__file__), 'enhanced_recipe_images_results.json')
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
    
    def update_recipes_json(self):
        """Update recipes.json with new image paths"""
        try:
            recipes_path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'recipes.json')
            
            # Load current recipes
            with open(recipes_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create a mapping of recipe names to new image paths
            image_mapping = {}
            for result in self.results:
                if result['success']:
                    image_mapping[result['recipe_name']] = f"Images/{result['filename']}"
            
            # Update recipes with new image paths
            updated_count = 0
            for recipe in data['remedies']:
                recipe_name = recipe['name']
                if recipe_name in image_mapping:
                    old_image = recipe.get('image', 'No image')
                    recipe['image'] = image_mapping[recipe_name]
                    logger.info(f"🔄 Updated {recipe_name}: {old_image} -> {image_mapping[recipe_name]}")
                    updated_count += 1
            
            # Save updated recipes.json
            with open(recipes_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Updated recipes.json with {updated_count} new image paths")
            
        except Exception as e:
            logger.error(f"❌ Error updating recipes.json: {e}")

def main():
    """Main function to generate all enhanced recipe images"""
    # Get project ID from environment
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    
    if not project_id or project_id == 'your-imagen4-project-id':
        logger.error("❌ Error: GOOGLE_CLOUD_PROJECT_ID not set or using placeholder value")
        logger.error("Please set your actual Google Cloud Project ID in the .env file")
        return
    
    logger.info(f"🚀 Starting Enhanced Recipe Image Generation")
    logger.info(f"📋 Project ID: {project_id}")
    logger.info(f"🎨 Using Professional AI Image Generation for Ayurvedic Recipes")
    
    try:
        generator = EnhancedRecipeImageGenerator(project_id)
        generator.generate_all_recipe_images()
        
        logger.info(f"\n🎉 All done! Check the static/Images/ folder for your beautiful new recipe images!")
        logger.info(f"🌐 The cards in your app will now display the enhanced AI-generated images!")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
