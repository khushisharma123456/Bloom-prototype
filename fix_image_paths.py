"""
Script to fix image paths in consultation.js
This script replaces all non-existent image paths with working ones
"""

import re

def fix_image_paths():
    file_path = r"d:\Projects\Bloom\Khushi Delpoyment-Blooom\colab deployment\bloom-gcp\Bloom-prototype\static\css\consultation.js"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define replacement patterns
    replacements = {
        r'|| "Images/doctor\d+\.jpg"': '|| "static/Images/profile.png"',
        r'|| "Images/coach\d+\.jpg"': '|| "static/Images/Khushi.png"',
        r'|| "Images/therapist\d+\.jpg"': '|| "static/Images/Mehak.png"',
        r'|| "Images/nutritionist\d+\.jpg"': '|| "static/Images/Suhani.png"',
        r'"Images/doctor\d+\.jpg"': '"static/Images/profile.png"',
        r'"Images/coach\d+\.jpg"': '"static/Images/Khushi.png"',
        r'"Images/therapist\d+\.jpg"': '"static/Images/Mehak.png"',
        r'"Images/nutritionist\d+\.jpg"': '"static/Images/Suhani.png"'
    }
    
    # Apply replacements
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Image paths fixed successfully!")
    print("All non-existent image paths have been replaced with working ones.")

if __name__ == "__main__":
    fix_image_paths()
