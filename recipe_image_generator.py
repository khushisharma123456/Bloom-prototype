#!/usr/bin/env python3
"""
Recipe Image Generator using Google Cloud Vertex AI
Generates AI images for all recipes in recipes.json
"""

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import os
from google.cloud import storage
import base64
from PIL import Image
import io
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RecipeImageGenerator:
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
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            if not bucket.exists():
                bucket = self.storage_client.create_bucket(self.bucket_name)
                print(f"Created bucket: {self.bucket_name}")
        except Exception as e:
            print(f"Error with bucket: {e}")
    
    def generate_recipe_prompt(self, recipe_data):
        """Generate a detailed prompt for recipe image"""
        name = recipe_data.get('name', 'Unknown Recipe')
        description = recipe_data.get('description', '')
        badge = recipe_data.get('badge', '')
        ingredients = recipe_data.get('ingredients', [])
        
        # Extract main ingredients for visual context
        main_ingredients = []
        if ingredients:
            for ingredient in ingredients[:3]:  # Use first 3 ingredients
                ingredient_clean = ingredient.lower().split('(')[0].strip()
                main_ingredients.append(ingredient_clean)
        
        ingredients_text = ", ".join(main_ingredients) if main_ingredients else "natural ingredients"
        
        # Create category-specific styling
        style_mapping = {
            'bloating': 'warm herbal tea with steam, soothing colors',
            'hormone balance': 'elegant wellness drink with natural herbs',
            'pain relief': 'comforting warm beverage with healing herbs',
            'energy boost': 'vibrant energizing drink or food',
            'iron-rich': 'rich colored nutritious food with leafy greens',
            'protein': 'hearty protein-rich dish with legumes',
            'anti-inflammatory': 'golden turmeric-colored healing drink',
            'digestive': 'fresh colorful soup or tea with herbs',
            'hydration': 'refreshing clear drink with fruits',
            'mood boost': 'chocolate-rich dark colored treat',
            'gut health': 'fermented food with probiotics',
            'calcium': 'creamy white dish with dairy or leafy greens'
        }
        
        style = style_mapping.get(badge.lower(), 'beautiful healthy food')
        
        prompt = f"""Professional food photography of {name}, {style}, 
        featuring {ingredients_text}, beautiful presentation on a clean white background,
        high quality food styling, natural lighting, appetizing and fresh appearance,
        {description}, ayurvedic and wellness focused, colorful and nutritious,
        shot from above or at 45 degree angle, minimal props, clean aesthetic,
        high resolution, restaurant quality presentation"""
        
        return prompt
    
    def generate_and_save_image(self, recipe_data):
        """Generate and save image for a single recipe"""
        try:
            recipe_name = recipe_data.get('name', 'Unknown Recipe')
            print(f"\nGenerating image for: {recipe_name}")
            
            # Generate prompt
            prompt = self.generate_recipe_prompt(recipe_data)
            print(f"Prompt: {prompt[:100]}...")
            
            # Generate image
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="block_few",
                person_generation="dont_allow"
            )
            
            if not response.images:
                raise Exception("No images generated")
            
            # Get the generated image
            generated_image = response.images[0]
            
            # Convert to PIL Image
            image_bytes = generated_image._image_bytes
            image = Image.open(io.BytesIO(image_bytes))
            
            # Resize to standard dimensions (400x400)
            image = image.resize((400, 400), Image.Resampling.LANCZOS)
            
            # Save to buffer
            buffer = io.BytesIO()
            image.save(buffer, format='PNG', quality=95)
            buffer.seek(0)
            
            # Create filename
            safe_name = "".join(c for c in recipe_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '-').lower()
            filename = f"recipe_{safe_name}.png"
            
            # Upload to Cloud Storage
            blob = self.storage_client.bucket(self.bucket_name).blob(filename)
            blob.upload_from_file(buffer, content_type='image/png')
            blob.make_public()
            
            # Get public URL
            public_url = blob.public_url
            
            # Save locally as well
            local_path = f"static/Images/{filename}"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            buffer.seek(0)
            with open(local_path, 'wb') as f:
                f.write(buffer.read())
            
            result = {
                'success': True,
                'recipe_name': recipe_name,
                'filename': filename,
                'local_path': local_path,
                'cloud_url': public_url,
                'prompt': prompt
            }
            
            print(f"✅ Success: {recipe_name} -> {filename}")
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'recipe_name': recipe_data.get('name', 'Unknown'),
                'error': str(e)
            }
            print(f"❌ Error generating image for {recipe_data.get('name', 'Unknown')}: {e}")
            return error_result
    
    def load_recipes_from_json(self):
        """Load recipes from recipes.json"""
        try:
            recipes_path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'recipes.json')
            with open(recipes_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('remedies', [])
        except Exception as e:
            print(f"Error loading recipes: {e}")
            return []
    
    def generate_all_recipe_images(self):
        """Generate images for all recipes"""
        recipes = self.load_recipes_from_json()
        
        if not recipes:
            print("No recipes found!")
            return
        
        print(f"Found {len(recipes)} recipes to generate images for...")
        
        for i, recipe in enumerate(recipes, 1):
            print(f"\n--- Processing {i}/{len(recipes)} ---")
            result = self.generate_and_save_image(recipe)
            self.results.append(result)
            
            # Small delay to avoid hitting rate limits
            import time
            time.sleep(2)
        
        # Save results
        self.save_results()
        self.update_recipes_json()
        
        # Print summary
        successful = len([r for r in self.results if r['success']])
        failed = len([r for r in self.results if not r['success']])
        
        print(f"\n🎉 Generation Complete!")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📄 Results saved to recipe_images_results.json")
    
    def save_results(self):
        """Save generation results to JSON file"""
        results_path = os.path.join(os.path.dirname(__file__), 'recipe_images_results.json')
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
            for recipe in data['remedies']:
                recipe_name = recipe['name']
                if recipe_name in image_mapping:
                    recipe['image'] = image_mapping[recipe_name]
                    print(f"Updated {recipe_name} -> {image_mapping[recipe_name]}")
            
            # Save updated recipes.json
            with open(recipes_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print("✅ Updated recipes.json with new image paths")
            
        except Exception as e:
            print(f"❌ Error updating recipes.json: {e}")

def main():
    """Main function to generate all recipe images"""
    # Get project ID from environment
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    
    if not project_id or project_id == 'your-imagen4-project-id':
        print("❌ Error: GOOGLE_CLOUD_PROJECT_ID not set or using placeholder value")
        print("Please set your actual Google Cloud Project ID in the .env file")
        return
    
    print(f"🚀 Starting Recipe Image Generation")
    print(f"📋 Project ID: {project_id}")
    
    try:
        generator = RecipeImageGenerator(project_id)
        generator.generate_all_recipe_images()
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
