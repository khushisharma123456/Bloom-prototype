#!/usr/bin/env python3
"""
Extract all recipe names from recipes.json to generate AI images for them.
"""

import json
import os

def extract_recipe_names():
    """Extract all recipe names from recipes.json"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    recipes_path = os.path.join(base_dir, 'static', 'data', 'recipes.json')
    
    try:
        with open(recipes_path, 'r') as f:
            data = json.load(f)
        
        remedies = data.get('remedies', [])
        recipe_names = []
        
        print(f"Found {len(remedies)} recipes in recipes.json:")
        print("-" * 50)
        
        for i, recipe in enumerate(remedies, 1):
            name = recipe.get('name', 'Unknown')
            badge = recipe.get('badge', 'Unknown')
            image_path = recipe.get('image', 'No image')
            
            recipe_names.append(name)
            print(f"{i:2d}. {name}")
            print(f"    Badge: {badge}")
            print(f"    Current image: {image_path}")
            print()
        
        print(f"\nTotal recipes to generate images for: {len(recipe_names)}")
        return recipe_names
        
    except FileNotFoundError:
        print(f"Error: recipes.json not found at {recipes_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in recipes.json: {e}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    recipe_names = extract_recipe_names()
    
    # Save recipe names to a file for further processing
    if recipe_names:
        output_file = 'recipe_names_list.txt'
        with open(output_file, 'w') as f:
            for name in recipe_names:
                f.write(f"{name}\n")
        print(f"\nRecipe names saved to {output_file}")
