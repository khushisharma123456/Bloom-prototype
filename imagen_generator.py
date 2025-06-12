import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import os
from google.cloud import storage
import base64
from PIL import Image
import io
import requests

class DoctorImageGenerator:
    def __init__(self, project_id, location="us-central1"):
        self.project_id = project_id
        self.location = location
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        self.model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        # Initialize Cloud Storage client
        self.storage_client = storage.Client()
        self.bucket_name = f"{project_id}-doctor-images"
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            if not bucket.exists():
                bucket = self.storage_client.create_bucket(self.bucket_name)
                print(f"Created bucket: {self.bucket_name}")
        except Exception as e:
            print(f"Error with bucket: {e}")
    
    def generate_doctor_prompt(self, name, specialty, gender, ethnicity="diverse"):
        """Generate a detailed prompt for doctor image"""
        gender_desc = "female" if gender.lower() == "female" else "male"
        
        # Specialty-specific descriptions
        specialty_desc = {
            "gynecologist": "gynecologist in medical coat",
            "therapist": "mental health therapist in professional attire",
            "nutritionist": "nutritionist with healthy lifestyle focus",
            "fitness": "fitness coach in athletic wear",
            "ayurveda": "ayurvedic practitioner in traditional attire"
        }
        
        specialty_key = next((key for key in specialty_desc.keys() if key in specialty.lower()), "doctor")
        profession_desc = specialty_desc.get(specialty_key, "medical doctor in white coat")
        
        prompt = f"""Professional headshot portrait of a {gender_desc} {profession_desc}, 
        smiling warmly, confident and approachable, clean medical/professional background, 
        high quality photography, professional lighting, medical setting, 
        {ethnicity} ethnicity, age 30-45, wearing appropriate professional attire,
        friendly demeanor, trustworthy appearance, medical professional headshot style"""
        
        return prompt
    
    def generate_and_save_image(self, doctor_data):
        """Generate image for a doctor and save to Cloud Storage"""
        try:
            name = doctor_data['name']
            specialty = doctor_data['specialty']
            gender = doctor_data['gender']
            
            # Generate prompt
            prompt = self.generate_doctor_prompt(name, specialty, gender)
            
            # Generate image
            print(f"Generating image for Dr. {name}...")
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                language="en",
                aspect_ratio="1:1",
            )
            
            # Get the generated image
            generated_image = response.images[0]
            
            # Convert to bytes
            image_bytes = generated_image._image_bytes
            
            # Create filename
            safe_name = name.replace(" ", "_").replace(".", "").lower()
            filename = f"doctor_{safe_name}_{specialty.lower().replace(' ', '_')}.jpg"
            
            # Upload to Cloud Storage
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(f"doctors/{filename}")
            blob.upload_from_string(image_bytes, content_type='image/jpeg')
            
            # Make the blob publicly readable
            blob.make_public()
            
            # Return the public URL
            public_url = blob.public_url
            print(f"Image saved for Dr. {name}: {public_url}")
            
            return {
                'filename': filename,
                'url': public_url,
                'success': True
            }
            
        except Exception as e:
            print(f"Error generating image for Dr. {name}: {e}")
            return {
                'filename': None,
                'url': None,
                'success': False,
                'error': str(e)
            }
    
    def generate_all_doctor_images(self, doctors_list):
        """Generate images for all doctors in the list"""
        results = []
        for doctor in doctors_list:
            result = self.generate_and_save_image(doctor)
            result['doctor_id'] = doctor.get('id')
            result['doctor_name'] = doctor.get('name')
            results.append(result)
        
        return results
