#!/usr/bin/env python3
"""
Script to update all doctor image references in consultation.js
"""

import re

# Read the consultation.js file
file_path = "d:/Projects/Bloom/Khushi Delpoyment-Blooom/colab deployment/bloom-gcp/Bloom-prototype/static/css/consultation.js"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the mapping of doctor names to their current image files
doctor_mappings = [
    ("Sapna Vyas", "coach2.jpg"),
    ("Mustafa Ahmed", "coach3.jpg"),
    ("Ranveer Allahbadia", "coach4.jpg"),
    ("Dr. Rachna Khanna Singh", "therapist1.jpg"),
    ("Dr. Shefali Batra", "therapist2.jpg"),
    ("Dr. Sayeli Jaiswal", "therapist3.jpg"),
    ("Dr. Kamna Chhibber", "therapist4.jpg"),
    ("Dr. Kersi Chavda", "therapist5.jpg"),
    ("Dr. Achal Bhagat", "therapist6.jpg"),
    ("Dr. Harish Shetty", "therapist7.jpg"),
    ("Dr. Samir Parikh", "therapist8.jpg"),
    ("Dr. Rujuta Diwekar", "nutritionist1.jpg"),
    ("Dr. Ishi Khosla", "nutritionist2.jpg"),
    ("Dr. Nikhil Dhurandhar", "nutritionist3.jpg"),
    ("Dr. Manjari Chandra", "nutritionist4.jpg")
]

# Update each doctor's image reference
for doctor_name, image_file in doctor_mappings:
    # Create the pattern to find the image line for this doctor
    pattern = f'(name: "{re.escape(doctor_name)}"[^}}]*?)image: "Images/{re.escape(image_file)}"'
    replacement = f'\\1image: doctorImages["{doctor_name}"] || "Images/{image_file}"'
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    print(f"Updated {doctor_name}")

# Write the updated content back to the file
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("All doctor image references updated successfully!")
