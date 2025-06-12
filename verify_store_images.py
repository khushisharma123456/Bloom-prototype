#!/usr/bin/env python3
"""
Verify that all product images are available in the static/Images folder
"""

import os
import json

def verify_store_images():
    """Verify all product images exist in static/Images folder"""
    
    # Base path to static/Images folder
    base_path = "static/Images"
    
    # List of expected product images based on store.html
    expected_images = [
        "product_saathi-organic-pads.png",
        "product_boomerang-menstrual-cup.png", 
        "product_the-womans-company-cloth-pads.png",
        "product_bamboo-razor-with-blades.png",
        "product_himalaya-menstrual-comfort-tea.png",
        "product_kottakkal-m2-tone-syrup.png",
        "product_organic-india-shatavari.png",
        "product_kama-ayurveda-kumkumadi-oil.png",
        "product_ecofemme-reusable-pads.png",
        "product_ahimsa-silk-underwear.png",
        "product_organic-cotton-tampons.png",
        "product_neem-wood-comb.png"
    ]
    
    print("🔍 Verifying Product Images...")
    print("=" * 50)
    
    missing_images = []
    found_images = []
    
    for image in expected_images:
        image_path = os.path.join(base_path, image)
        if os.path.exists(image_path):
            file_size = os.path.getsize(image_path)
            found_images.append({"name": image, "size": file_size})
            print(f"✅ {image} - {file_size} bytes")
        else:
            missing_images.append(image)
            print(f"❌ {image} - NOT FOUND")
    
    print("\n" + "=" * 50)
    print(f"📊 Summary:")
    print(f"✅ Found: {len(found_images)}/{len(expected_images)} images")
    print(f"❌ Missing: {len(missing_images)} images")
    
    if missing_images:
        print(f"\n🚨 Missing Images:")
        for img in missing_images:
            print(f"   - {img}")
        return False
    else:
        print(f"\n🎉 All product images are available!")
        return True

def check_image_urls_in_store():
    """Check if store.html is using correct local image URLs"""
    
    store_file = "templates/store.html"
    
    if not os.path.exists(store_file):
        print(f"❌ Store file not found: {store_file}")
        return False
        
    with open(store_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Checking store.html image URL format...")
    
    # Check if using Flask url_for instead of Google Storage URLs
    if "url_for('static', filename='Images/" in content:
        print("✅ Using correct Flask static URLs")
        uses_flask_urls = True
    else:
        print("❌ Not using Flask static URLs")
        uses_flask_urls = False
        
    # Check if any Google Storage URLs remain
    if "storage.googleapis.com" in content:
        print("🚨 Found Google Storage URLs - these should be replaced")
        uses_google_storage = True
    else:
        print("✅ No Google Storage URLs found")
        uses_google_storage = False
        
    return uses_flask_urls and not uses_google_storage

if __name__ == "__main__":
    print("🏪 Store Images Verification")
    print("=" * 50)
    
    # Verify images exist
    images_ok = verify_store_images()
    
    # Check URL format in store.html
    urls_ok = check_image_urls_in_store()
    
    print("\n" + "=" * 50)
    print("🏁 Final Status:")
    if images_ok and urls_ok:
        print("✅ All checks passed! Store images should work correctly.")
    else:
        print("❌ Some issues found. Please review the output above.")
        
    print("\n💡 Next steps:")
    print("1. Run your Flask app: python app.py")
    print("2. Visit /store to verify images load correctly")
    print("3. Check browser console for any 404 errors")
