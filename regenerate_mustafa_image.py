#!/usr/bin/env python3
"""
Script to regenerate Mustafa Ahmed's doctor image.
Fixes the missing AI-generated image for this specific doctor.
"""

from imagen_generator import DoctorImageGenerator
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def regenerate_mustafa_image():
    """Regenerate the image for Mustafa Ahmed specifically."""
    
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    
    if not PROJECT_ID or PROJECT_ID == 'your-imagen4-project-id':
        print("❌ ERROR: GOOGLE_CLOUD_PROJECT_ID environment variable not set!")
        return False
    
    print(f"🚀 Using Google Cloud Project: {PROJECT_ID}")
    print(f"🔄 Regenerating image for Mustafa Ahmed...")
    
    # Initialize the generator
    generator = DoctorImageGenerator(PROJECT_ID)
    
    # Mustafa Ahmed's data
    mustafa_data = {
        "id": 11,
        "name": "Mustafa Ahmed",
        "specialty": "Fitness Coach", 
        "gender": "male"
    }
    
    print(f"📸 Generating image for {mustafa_data['name']}...")
    
    try:
        # Generate the image
        image_url = generator.generate_doctor_image(
            name=mustafa_data["name"],
            specialty=mustafa_data["specialty"],
            gender=mustafa_data["gender"]
        )
        
        if image_url:
            print(f"✅ Image generated successfully!")
            print(f"🔗 URL: {image_url}")
            
            # Update the results file
            update_results_file(mustafa_data, image_url)
            return True
        else:
            print(f"❌ Failed to generate image for {mustafa_data['name']}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating image for {mustafa_data['name']}: {e}")
        return False

def update_results_file(doctor_data, image_url):
    """Update the doctor_images_results.json file with the new image."""
    
    results_file = "doctor_images_results.json"
    
    try:
        # Load existing results
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        # Find and update Mustafa Ahmed's entry
        for i, result in enumerate(results):
            if result.get('doctor_name') == doctor_data['name']:
                # Create filename from URL
                filename = image_url.split('/')[-1] if image_url else None
                
                # Update the entry
                results[i] = {
                    "filename": filename,
                    "url": image_url,
                    "success": True,
                    "doctor_id": doctor_data['id'],
                    "doctor_name": doctor_data['name']
                }
                
                print(f"📝 Updated results file for {doctor_data['name']}")
                break
        
        # Save the updated results
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"💾 Results file saved successfully")
        
    except Exception as e:
        print(f"❌ Error updating results file: {e}")

if __name__ == "__main__":
    success = regenerate_mustafa_image()
    
    if success:
        print(f"\n🎉 Success! Mustafa Ahmed's image has been generated.")
        print(f"📱 You can now refresh the consultation page to see his image.")
    else:
        print(f"\n❌ Failed to generate Mustafa Ahmed's image.")
        print(f"🔧 You may need to check the Google Cloud setup or try again later.")
