#!/usr/bin/env python3
"""
Verify that all recipe images are properly generated and linked
"""

import json
import os
from pathlib import Path

def verify_recipe_images():
    """Verify all recipe images exist and are properly linked"""
    
    # Load recipes data
    recipes_path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'recipes.json')
    with open(recipes_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    remedies = data.get('remedies', [])
    
    print(f"🔍 Verifying {len(remedies)} recipes...")
    print("=" * 60)
    
    success_count = 0
    missing_count = 0
    placeholder_count = 0
    
    for i, recipe in enumerate(remedies, 1):
        name = recipe.get('name', 'Unknown')
        image_path = recipe.get('image', '')
        full_path = os.path.join(os.path.dirname(__file__), 'static', image_path)
        
        status = ""
        if not image_path:
            status = "❌ NO IMAGE PATH"
            missing_count += 1
        elif image_path.endswith(('.png', '.jpg', '.jpeg')) and 'recipe_' in image_path:
            if os.path.exists(full_path):
                status = "✅ AI IMAGE"
                success_count += 1
            else:
                status = "❌ MISSING FILE"
                missing_count += 1
        elif any(placeholder in image_path for placeholder in ['1h.png', '2h.png', '3h.png', '4h.png', '5h.png', '6h.png', '7h.png', '8h.png', '9h.png', '10h.png', '11h.png', '12h.png', '13h.png', '14h.png', '15h.png', '16h.png']):
            status = "⚠️  PLACEHOLDER"
            placeholder_count += 1
        else:
            if os.path.exists(full_path):
                status = "✅ EXISTING"
                success_count += 1
            else:
                status = "❌ MISSING"
                missing_count += 1
        
        print(f"{i:2d}. {name:<35} {status:<15} {image_path}")
    
    print("=" * 60)
    print(f"📊 SUMMARY:")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Missing: {missing_count}")
    print(f"   ⚠️  Placeholders: {placeholder_count}")
    print(f"   📸 Total: {len(remedies)}")
    
    success_rate = (success_count / len(remedies)) * 100
    print(f"   🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("\n🎉 Excellent! Almost all recipes have proper images!")
    elif success_rate >= 75:
        print("\n👍 Good! Most recipes have proper images!")
    elif success_rate >= 50:
        print("\n⚡ Moderate. Some recipes still need images.")
    else:
        print("\n⚠️  Many recipes still need proper images.")
    
    return {
        'total': len(remedies),
        'success': success_count,
        'missing': missing_count,
        'placeholders': placeholder_count,
        'success_rate': success_rate
    }

if __name__ == "__main__":
    try:
        verify_recipe_images()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
