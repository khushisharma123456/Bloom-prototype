#!/usr/bin/env python3
"""
Regenerate missing image for Coconut Water & Chia Fresca recipe
"""

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import os
from google.cloud import storage
import base64
from PIL import Image
import io
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MissingImageRegenerator:
    def __init__(self, project_id, location="us-central1"):
        self.project_id = project_id
        self.location = location
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        self.model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        # Initialize Cloud Storage client
        self.storage_client = storage.Client()
        self.bucket_name = f"{project_id}-recipe-images"

    def find_missing_recipe(self):
        """Find the Coconut Water & Chia Fresca recipe data"""
        try:
            recipes_path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'recipes.json')
            with open(recipes_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for recipe in data.get('remedies', []):
                if recipe.get('name') == 'Coconut Water & Chia Fresca':
                    return recipe
            
            print("❌ Recipe 'Coconut Water & Chia Fresca' not found in recipes.json")
            return None
            
        except Exception as e:
            print(f"❌ Error loading recipes: {e}")
            return None

    def generate_enhanced_prompt(self, recipe_data):
        """Generate an enhanced, more specific prompt for Coconut Water & Chia Fresca"""
        name = recipe_data.get('name', 'Coconut Water & Chia Fresca')
        description = recipe_data.get('description', '')
        ingredients = recipe_data.get('ingredients', [])
        
        # Create a very specific and appealing prompt for this hydrating drink
        prompt = f"""Professional food photography of a refreshing {name}, 
        a crystal clear glass filled with coconut water and chia seeds,
        beautiful hydrating drink with tiny black chia seeds floating like pearls,
        fresh lime wedge garnish, condensation droplets on the glass,
        tropical and refreshing aesthetic, clean white marble background,
        natural daylight photography, high resolution food styling,
        appetizing and thirst-quenching appearance, health drink photography,
        minimalist composition, shot from 45 degree angle,
        restaurant quality presentation, wellness and hydration focused,
        coconut water's natural clarity with chia seeds creating texture,
        fresh and energizing summer drink"""
        
        return prompt

    def generate_coconut_chia_image(self):
        """Generate image specifically for Coconut Water & Chia Fresca"""
        try:
            recipe_data = self.find_missing_recipe()
            if not recipe_data:
                return {'success': False, 'error': 'Recipe not found'}

            recipe_name = recipe_data.get('name', 'Coconut Water & Chia Fresca')
            print(f"🎨 Generating image for: {recipe_name}")
            
            # Generate enhanced prompt
            prompt = self.generate_enhanced_prompt(recipe_data)
            print(f"📝 Using prompt: {prompt[:100]}...")
            
            # Try multiple attempts with slight variations
            for attempt in range(3):
                try:
                    print(f"   Attempt {attempt + 1}/3...")
                    
                    # Add slight variation to prompt for different attempts
                    variation_prompts = [
                        prompt,
                        prompt.replace("45 degree angle", "overhead view"),
                        prompt.replace("white marble background", "light wooden background")
                    ]
                    
                    current_prompt = variation_prompts[attempt]
                    
                    # Generate image
                    response = self.model.generate_images(
                        prompt=current_prompt,
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
                    filename = "recipe_coconut-water--chia-fresca.png"
                    
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
                        'prompt': current_prompt,
                        'attempt': attempt + 1
                    }
                    
                    print(f"✅ Success on attempt {attempt + 1}: {recipe_name} -> {filename}")
                    return result
                    
                except Exception as e:
                    print(f"   ❌ Attempt {attempt + 1} failed: {e}")
                    if attempt < 2:  # If not the last attempt
                        print(f"   ⏳ Waiting 5 seconds before retry...")
                        time.sleep(5)
                    continue
            
            # If all attempts failed
            return {
                'success': False,
                'recipe_name': recipe_name,
                'error': 'All 3 attempts failed'
            }
            
        except Exception as e:
            error_result = {
                'success': False,
                'recipe_name': 'Coconut Water & Chia Fresca',
                'error': str(e)
            }
            print(f"❌ Fatal error: {e}")
            return error_result

    def update_recipes_json(self, result):
        """Update recipes.json with the new image path"""
        if not result['success']:
            return False
            
        try:
            recipes_path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'recipes.json')
            
            # Load current recipes
            with open(recipes_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Find and update the specific recipe
            for recipe in data['remedies']:
                if recipe['name'] == 'Coconut Water & Chia Fresca':
                    old_image = recipe.get('image', 'N/A')
                    recipe['image'] = f"Images/{result['filename']}"
                    print(f"📝 Updated recipe image path:")
                    print(f"   From: {old_image}")
                    print(f"   To: {recipe['image']}")
                    break
            
            # Save updated recipes.json
            with open(recipes_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print("✅ Updated recipes.json with new image path")
            return True
            
        except Exception as e:
            print(f"❌ Error updating recipes.json: {e}")
            return False

    def update_results_file(self, result):
        """Update the results file with the new generation result"""
        try:
            results_path = os.path.join(os.path.dirname(__file__), 'recipe_images_results.json')
            
            # Load existing results
            with open(results_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Find and update the Coconut Water entry
            for i, entry in enumerate(results):
                if entry.get('recipe_name') == 'Coconut Water & Chia Fresca':
                    results[i] = result
                    print("📝 Updated results file with successful generation")
                    break
            
            # Save updated results
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating results file: {e}")
            return False

def main():
    """Main function to regenerate the missing image"""
    # Get project ID from environment
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    
    if not project_id or project_id == 'your-imagen4-project-id':
        print("❌ Error: GOOGLE_CLOUD_PROJECT_ID not set or using placeholder value")
        print("Please set your actual Google Cloud Project ID in the .env file")
        return
    
    print("🚀 Regenerating missing image for Coconut Water & Chia Fresca")
    print("=" * 60)
    print(f"📋 Project ID: {project_id}")
    
    try:
        regenerator = MissingImageRegenerator(project_id)
        result = regenerator.generate_coconut_chia_image()
        
        if result['success']:
            print("=" * 60)
            print("🎉 Image generation successful!")
            print(f"   📁 Local file: {result['local_path']}")
            print(f"   ☁️  Cloud URL: {result['cloud_url']}")
            print(f"   🎯 Attempt: {result['attempt']}")
            
            # Update recipes.json
            regenerator.update_recipes_json(result)
            
            # Update results file
            regenerator.update_results_file(result)
            
            print("\n✅ All files updated successfully!")
            print("🎨 The Coconut Water & Chia Fresca recipe now has a beautiful AI-generated image!")
            
        else:
            print("=" * 60)
            print("❌ Image generation failed!")
            print(f"   Error: {result['error']}")
            print("\n💡 Suggestions:")
            print("   • Try running the script again in a few minutes")
            print("   • Check your Google Cloud quota and billing")
            print("   • Verify your network connection")
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
