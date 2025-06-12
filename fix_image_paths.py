"""
Script to fix image paths in HTML and JS files
This script ensures all static image paths are using absolute URLs for proper rendering in GCP deployment
"""

import re
import os
import glob

def fix_image_paths():
    # Base directory for the project
    base_dir = r"d:\Projects\Bloom\Khushi Delpoyment-Blooom\colab deployment\bloom-gcp\Bloom-prototype"
    
    # Patterns to look for and fix
    replacements = {
        r'src="static/Images/': r'src="/static/Images/',
        r'src="static/img/': r'src="/static/img/',
        r'url\("static/Images/': r'url("/static/Images/',
        r'url\("static/img/': r'url("/static/img/',
        r'url\(\'static/Images/': r'url(\'/static/Images/',
        r'url\(\'static/img/': r'url(\'/static/img/',
        r'image["\']:\s*["\']static/Images/': r'image": "/static/Images/',
        r'aiImage:\s*"static/Images/': r'aiImage: "/static/Images/',
        r'background-image:\s*url\(static/': r'background-image: url(/static/',
        # Original patterns from the script
        r'\|\|\s*"Images/doctor\d+\.jpg"': r'|| "/static/Images/profile.png"',
        r'\|\|\s*"Images/coach\d+\.jpg"': r'|| "/static/Images/Khushi.png"',
        r'\|\|\s*"Images/therapist\d+\.jpg"': r'|| "/static/Images/Mehak.png"',
        r'\|\|\s*"Images/nutritionist\d+\.jpg"': r'|| "/static/Images/Suhani.png"',
        r'"Images/doctor\d+\.jpg"': r'"/static/Images/profile.png"',
        r'"Images/coach\d+\.jpg"': r'"/static/Images/Khushi.png"',
        r'"Images/therapist\d+\.jpg"': r'"/static/Images/Mehak.png"',
        r'"Images/nutritionist\d+\.jpg"': r'"/static/Images/Suhani.png"'
    }
    
    # File types to process
    file_patterns = [
        os.path.join(base_dir, "templates", "*.html"),
        os.path.join(base_dir, "static", "css", "*.js"),
        os.path.join(base_dir, "static", "js", "*.js"),
    ]
    
    total_files = 0
    modified_files = 0
    
    # Process all matching files
    for pattern in file_patterns:
        for file_path in glob.glob(pattern):
            total_files += 1
            print(f"Processing: {os.path.basename(file_path)}")
            
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply replacements
            for pattern, replacement in replacements.items():
                content = re.sub(pattern, replacement, content)
            
            # Only write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                modified_files += 1
                print(f"  ✓ Fixed paths in {os.path.basename(file_path)}")
    
    print(f"\n✅ Image paths fixed successfully! Modified {modified_files} out of {total_files} files.")
    print("All relative image paths have been converted to absolute paths for proper GCP deployment.")

if __name__ == "__main__":
    fix_image_paths()
