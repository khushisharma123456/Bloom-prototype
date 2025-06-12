from imagen_generator import DoctorImageGenerator
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    # Secure environment variable handling for production
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    
    if not PROJECT_ID or PROJECT_ID == 'your-imagen4-project-id':
        print("❌ ERROR: GOOGLE_CLOUD_PROJECT_ID environment variable not set!")
        print("🔧 SETUP REQUIRED:")
        print("   Local Development:")
        print("   - Update .env file with your actual project ID")
        print("   Production Deployment:")
        print("   - Set GOOGLE_CLOUD_PROJECT_ID as environment variable on your hosting platform")
        print("   - Example: GOOGLE_CLOUD_PROJECT_ID=my-bloom-project-123456")
        return
    
    print(f"🚀 Using Google Cloud Project: {PROJECT_ID}")
    
    # Initialize the generator
    generator = DoctorImageGenerator(PROJECT_ID)
    
    # Doctor data extracted from consultation.js
    doctors_data = [
        {
            "id": 1,
            "name": "Dr. Priya Sharma",
            "specialty": "Gynecologist",
            "gender": "female"
        },
        {
            "id": 2,
            "name": "Dr. Meera Bhatia",
            "specialty": "Gynecologist",
            "gender": "female"
        },
        {
            "id": 3,
            "name": "Dr. Rajesh Kumar",
            "specialty": "Gynecologist",
            "gender": "male"
        },
        {
            "id": 4,
            "name": "Dr. Amit Tandon",
            "specialty": "Gynecologist",
            "gender": "male"
        },
        {
            "id": 5,
            "name": "Dr. Deepa Krishnan",
            "specialty": "Ayurvedic Expert",
            "gender": "female"
        },
        {
            "id": 6,
            "name": "Dr. Smita Naram",
            "specialty": "Ayurvedic Expert",
            "gender": "female"
        },
        {
            "id": 7,
            "name": "Dr. Partap Chauhan",
            "specialty": "Ayurvedic Expert",
            "gender": "male"
        },
        {
            "id": 8,
            "name": "Dr. Ram Krishna Shastri",
            "specialty": "Ayurvedic Expert",
            "gender": "male"
        },
        {
            "id": 9,
            "name": "Yasmin Karachiwala",
            "specialty": "Fitness Coach",
            "gender": "female"
        },
        {
            "id": 10,
            "name": "Sapna Vyas",
            "specialty": "Fitness Coach",
            "gender": "female"
        },
        {
            "id": 11,
            "name": "Mustafa Ahmed",
            "specialty": "Fitness Coach",
            "gender": "male"
        },
        {
            "id": 12,
            "name": "Ranveer Allahbadia",
            "specialty": "Fitness Coach",
            "gender": "male"
        },
        {
            "id": 13,
            "name": "Dr. Rachna Khanna Singh",
            "specialty": "Therapist",
            "gender": "female"
        },
        {
            "id": 14,
            "name": "Dr. Shefali Batra",
            "specialty": "Therapist",
            "gender": "female"
        },
        {
            "id": 15,
            "name": "Dr. Sayeli Jaiswal",
            "specialty": "Therapist",
            "gender": "female"
        },
        {
            "id": 16,
            "name": "Dr. Kamna Chhibber",
            "specialty": "Therapist",
            "gender": "female"
        },
        {
            "id": 17,
            "name": "Dr. Kersi Chavda",
            "specialty": "Therapist",
            "gender": "male"
        },
        {
            "id": 18,
            "name": "Dr. Achal Bhagat",
            "specialty": "Therapist",
            "gender": "male"
        },
        {
            "id": 19,
            "name": "Dr. Harish Shetty",
            "specialty": "Therapist",
            "gender": "male"
        },
        {
            "id": 20,
            "name": "Dr. Samir Parikh",
            "specialty": "Therapist",
            "gender": "male"
        },
        {
            "id": 21,
            "name": "Dr. Rujuta Diwekar",
            "specialty": "Nutritionist",
            "gender": "female"
        },
        {
            "id": 22,
            "name": "Dr. Ishi Khosla",
            "specialty": "Nutritionist",
            "gender": "female"
        },
        {
            "id": 23,
            "name": "Dr. Nikhil Dhurandhar",
            "specialty": "Nutritionist",
            "gender": "male"
        },
        {
            "id": 24,
            "name": "Dr. Manjari Chandra",
            "specialty": "Nutritionist",
            "gender": "female"  # Fixed from original data
        }
    ]
    
    # Generate images for all doctors
    print("Starting image generation for all doctors...")
    results = generator.generate_all_doctor_images(doctors_data)
    
    # Save results to a JSON file
    with open('doctor_images_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"\nImage generation complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    # Print URLs for successful generations
    print("\nGenerated image URLs:")
    for result in results:
        if result['success']:
            print(f"{result['doctor_name']}: {result['url']}")

if __name__ == "__main__":
    main()
