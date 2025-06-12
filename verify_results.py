import json

# Load the doctor images results
with open('doctor_images_results.json', 'r') as f:
    data = json.load(f)

total_doctors = len(data)
successful_generations = sum(1 for d in data if d.get('success', False))
ai_generated_images = sum(1 for d in data if 'storage.googleapis.com' in d.get('url', ''))
static_images = sum(1 for d in data if 'static/Images/' in d.get('url', ''))

print("🎉 FINAL RESULTS:")
print(f"📊 Total doctors: {total_doctors}")
print(f"✅ Successful AI generations: {successful_generations}")
print(f"🤖 Using AI-generated images: {ai_generated_images}")
print(f"📁 Using static fallback images: {static_images}")
print(f"❌ Failed generations: {total_doctors - successful_generations}")

print("\n🔍 VERIFICATION:")
if ai_generated_images >= 20:
    print("✅ SUCCESS: Most doctors now have unique AI-generated portraits!")
else:
    print("⚠️  WARNING: Still using too many static images")

print(f"\n📈 IMPROVEMENT:")
print(f"Before: 24 doctors using 5 static images (Mehak.png, Suhani.png, etc.)")
print(f"After: {ai_generated_images} doctors using unique AI-generated images")

# Show a few examples
print(f"\n🖼️  SAMPLE AI-GENERATED IMAGES:")
ai_doctors = [d for d in data if 'storage.googleapis.com' in d.get('url', '')][:3]
for doctor in ai_doctors:
    print(f"• {doctor['doctor_name']}: {doctor['url']}")
