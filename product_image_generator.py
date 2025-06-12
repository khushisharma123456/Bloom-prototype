#!/usr/bin/env python3
"""
Product Image Generator for Bloom Store - Organic & Ayurvedic Products
Generates beautiful, professional AI images for all store products using Google Cloud Vertex AI
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

class ProductImageGenerator:
    def __init__(self, project_id, location="us-central1"):
        self.project_id = project_id
        self.location = location
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        self.model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        # Initialize Cloud Storage client
        self.storage_client = storage.Client()
        self.bucket_name = f"{project_id}-product-images"
        self._ensure_bucket_exists()
        
        # Results storage
        self.results = []
        
        # Enhanced style mappings for different product categories
        self.style_mappings = {
            # Menstrual Care Products
            'menstrual': {
                'style': 'clean, hygienic product photography with soft natural colors',
                'background': 'minimalist white background with subtle lavender accents',
                'props': 'organic cotton elements, natural fabrics, eco-friendly packaging',
                'lighting': 'soft, clean professional lighting'
            },
            # Ayurvedic Products
            'ayurvedic': {
                'style': 'traditional ayurvedic medicine presentation with authentic herbs and natural ingredients',
                'background': 'warm wooden surface or traditional clay backdrop',
                'props': 'fresh herbs, traditional bottles, ayurvedic elements, natural stones',
                'lighting': 'warm golden hour lighting'
            },
            # Eco-Friendly Products
            'eco': {
                'style': 'sustainable and environmentally conscious product styling',
                'background': 'natural outdoor setting or eco-friendly background',
                'props': 'bamboo elements, reusable materials, green plants, earth tones',
                'lighting': 'natural daylight, environmental conscious presentation'
            },
            # Artisan Made Products
            'artisan': {
                'style': 'handcrafted artisanal product with traditional Indian elements',
                'background': 'rustic handwoven fabric or traditional Indian backdrop',
                'props': 'traditional weaving, handmade elements, Indian craftsmanship details',
                'lighting': 'warm artisanal lighting highlighting craftsmanship'
            }
        }
        
        # Product data extracted from store.html
        self.products = [
            {
                'title': 'Saathi Organic Pads',
                'maker': 'By Saathi, Gujarat',
                'price': '₹249 (pack of 10)',
                'categories': ['all', 'menstrual', 'eco', 'artisan']
            },
            {
                'title': "Boomerang Menstrual Cup",
                'maker': "By Boomerang, India",
                'price': "₹599",
                'categories': ['all', 'menstrual', 'eco']
            },
            {
                'title': "The Woman's Company Cloth Pads",
                'maker': "By The Woman's Company",
                'price': "₹399 (pack of 3)",
                'categories': ['all', 'menstrual', 'eco', 'artisan']
            },
            {
                'title': "Bamboo Razor with Blades",
                'maker': "By EcoRoots, Karnataka",
                'price': "₹349",
                'categories': ['all', 'eco']
            },
            {
                'title': "Himalaya Menstrual Comfort Tea",
                'maker': "By Himalaya Herbals",
                'price': "₹199 (25 tea bags)",
                'categories': ['all', 'ayurvedic']
            },
            {
                'title': "Kottakkal M2 Tone Syrup",
                'maker': "By Arya Vaidya Sala",
                'price': "₹275 (200ml)",
                'categories': ['all', 'ayurvedic']
            },
            {
                'title': "Organic India Shatavari",
                'maker': "By Organic India",
                'price': "₹399 (60 capsules)",
                'categories': ['all', 'ayurvedic']
            },
            {
                'title': "Kama Ayurveda Kumkumadi Oil",
                'maker': "By Kama Ayurveda",
                'price': "₹1,250 (30ml)",
                'categories': ['all', 'ayurvedic']
            },
            {
                'title': "EcoFemme Reusable Pads",
                'maker': "By EcoFemme, Tamil Nadu",
                'price': "₹1,200 (pack of 5)",
                'categories': ['all', 'eco', 'artisan']
            },
            {
                'title': "Ahimsa Silk Underwear",
                'maker': "By No Nasties",
                'price': "₹899 each",
                'categories': ['all', 'eco', 'artisan']
            },
            {
                'title': "Organic Cotton Tampons",
                'maker': "By Carmesi",
                'price': "₹299 (pack of 16)",
                'categories': ['all', 'eco']
            },
            {
                'title': "Neem Wood Comb",
                'maker': "By Forest Essentials",
                'price': "₹450",
                'categories': ['all', 'eco']
            }
        ]

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            if not bucket.exists():
                bucket = self.storage_client.create_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Error with bucket: {e}")

    def _get_product_category(self, categories):
        """Determine primary product category for styling"""
        # Priority order for category selection
        category_priority = ['menstrual', 'ayurvedic', 'eco', 'artisan']
        
        for category in category_priority:
            if category in categories:
                return category
        
        return 'eco'  # default fallback

    def generate_enhanced_prompt(self, product_data):
        """Generate an enhanced, detailed prompt for product image"""
        title = product_data.get('title', 'Unknown Product')
        maker = product_data.get('maker', '')
        categories = product_data.get('categories', ['eco'])
        
        # Determine primary category for styling
        category = self._get_product_category(categories)
        
        # Get style information
        style_info = self.style_mappings.get(category, self.style_mappings['eco'])
        
        # Create comprehensive prompt based on product type
        prompt = f"""Professional product photography of {title}, {style_info['style']}, 
        {style_info['background']}, high-end commercial photography, 
        {style_info['props']}, {style_info['lighting']},
        shot from optimal angle for e-commerce, minimal clean composition, 
        high resolution 4K quality, commercial product shot, Amazon-quality photography,
        sharp focus on product, premium packaging visible, brand aesthetic,
        studio quality, professional product styling, clean white or natural background,
        organic and sustainable visual appeal, {maker} branding subtle,
        depth of field, product catalog quality, elegant composition, Indian wellness brand aesthetic"""
        
        return prompt, category

    def _enhance_image(self, image):
        """Apply subtle enhancements to the generated image"""
        try:
            # Slightly enhance contrast and color saturation for product photography
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.15)
            
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.1)
            
            # Subtle sharpening for product details
            image = image.filter(ImageFilter.UnsharpMask(radius=1.5, percent=60, threshold=3))
            
            return image
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}")
            return image

    def generate_and_save_image(self, product_data):
        """Generate and save enhanced image for a single product"""
        try:
            product_title = product_data.get('title', 'Unknown Product')
            logger.info(f"\n🛍️ Generating image for: {product_title}")
            
            # Generate enhanced prompt
            prompt, category = self.generate_enhanced_prompt(product_data)
            logger.info(f"📝 Category: {category}")
            logger.info(f"🎯 Prompt: {prompt[:120]}...")
            
            # Generate image with enhanced parameters
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="block_few",
                person_generation="dont_allow",
                # Enhanced parameters for better product photography
                language="en",
                guidance_scale=20,  # Higher guidance for better product representation
                negative_prompt="people, hands, person, human, text, letters, words, watermark, low quality, blurry, dark, messy background, cluttered"
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
            
            # Resize to standard dimensions (400x400) for consistency
            image = image.resize((400, 400), Image.Resampling.LANCZOS)
            
            # Save to buffer
            buffer = io.BytesIO()
            image.save(buffer, format='PNG', quality=95)
            buffer.seek(0)
            
            # Create filename
            safe_name = "".join(c for c in product_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '-').lower()
            filename = f"product_{safe_name}.png"
            
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
                'product_title': product_title,
                'filename': filename,
                'local_path': local_path,
                'cloud_url': public_url,
                'prompt': prompt,
                'category': category
            }
            
            logger.info(f"✅ Success: {product_title} -> {filename}")
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'product_title': product_data.get('title', 'Unknown'),
                'error': str(e),
                'category': None
            }
            logger.error(f"❌ Error generating image for {product_data.get('title', 'Unknown')}: {e}")
            return error_result

    def generate_all_product_images(self):
        """Generate enhanced images for all products"""
        if not self.products:
            logger.error("No products found!")
            return
        
        logger.info(f"🚀 Found {len(self.products)} products to generate images for...")
        logger.info("🎨 Using Enhanced AI Image Generation for Store Products")
        
        for i, product in enumerate(self.products, 1):
            logger.info(f"\n--- Processing {i}/{len(self.products)} ---")
            result = self.generate_and_save_image(product)
            self.results.append(result)
            
            # Delay to avoid rate limits
            if i < len(self.products):  # Don't delay after the last one
                logger.info("⏳ Waiting 3 seconds to avoid rate limits...")
                time.sleep(3)
        
        # Save results
        self.save_results()
        self.update_store_html()
        
        # Print comprehensive summary
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        logger.info(f"\n🎉 Enhanced Product Image Generation Complete!")
        logger.info(f"✅ Successful: {len(successful)}")
        logger.info(f"❌ Failed: {len(failed)}")
        
        if successful:
            logger.info("\n✅ Successfully Generated:")
            for result in successful:
                logger.info(f"   🛍️ {result['product_title']} -> {result['filename']}")
        
        if failed:
            logger.info("\n❌ Failed to Generate:")
            for result in failed:
                logger.info(f"   💥 {result['product_title']}: {result['error']}")
        
        logger.info(f"\n📄 Results saved to product_images_results.json")

    def save_results(self):
        """Save generation results to JSON file"""
        results_file = 'product_images_results.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Results saved to {results_file}")

    def update_store_html(self):
        """Update store.html with new image paths"""
        store_html_path = 'templates/store.html'
        
        if not os.path.exists(store_html_path):
            logger.warning(f"store.html not found at {store_html_path}")
            return
        
        # Create mapping of product titles to new image paths
        image_mapping = {}
        for result in self.results:
            if result['success']:
                # Use local path for the store
                image_mapping[result['product_title']] = f"static/Images/{result['filename']}"
        
        logger.info(f"📝 Updating store.html with {len(image_mapping)} new product images...")
        
        # Read current store.html
        with open(store_html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update image URLs for each product
        for product_title, new_image_path in image_mapping.items():
            # Find and replace the image URL in the JavaScript products array
            # This is a simple approach - for production, consider using a more robust parser
            old_pattern = f'title: "{product_title}"'
            if old_pattern in content:
                # Find the image line after this title
                start_idx = content.find(old_pattern)
                if start_idx != -1:
                    # Find the image line in the next few lines
                    lines_to_check = content[start_idx:start_idx+500]
                    if 'image: "' in lines_to_check:
                        # Replace the image URL
                        image_start = lines_to_check.find('image: "') + 8
                        image_end = lines_to_check.find('"', image_start)
                        if image_end != -1:
                            old_image_url = lines_to_check[image_start:image_end]
                            content = content.replace(
                                f'image: "{old_image_url}"',
                                f'image: "{new_image_path}"'
                            )
                            logger.info(f"   ✅ Updated {product_title}")
        
        # Write updated content back
        with open(store_html_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("🎨 store.html updated with new AI-generated product images!")

def main():
    """Main function to generate all enhanced product images"""
    # Get project ID from environment
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    
    if not project_id or project_id == 'your-imagen4-project-id':
        logger.error("❌ Error: GOOGLE_CLOUD_PROJECT_ID not set or using placeholder value")
        logger.error("Please set your actual Google Cloud Project ID in the .env file")
        return
    
    logger.info(f"🚀 Starting Enhanced Product Image Generation")
    logger.info(f"📋 Project ID: {project_id}")
    logger.info(f"🛍️ Using Professional AI Image Generation for Store Products")
    
    try:
        generator = ProductImageGenerator(project_id)
        generator.generate_all_product_images()
        
        logger.info(f"\n🎉 All done! Check the static/Images/ folder for your beautiful new product images!")
        logger.info(f"🌐 The store will now display the enhanced AI-generated product images!")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
