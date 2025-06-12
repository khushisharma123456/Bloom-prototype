#!/usr/bin/env python3
"""
Quick test and regeneration of a single yoga pose
"""

import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🧪 Testing environment...")
    
    # Check environment
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'your-project-id')
    logger.info(f"📋 Project ID: {PROJECT_ID}")
    
    if PROJECT_ID == 'your-project-id':
        logger.error("❌ Please set GOOGLE_CLOUD_PROJECT_ID environment variable")
        return
    
    logger.info("✅ Environment looks good!")
    
    # Test imports
    try:
        import vertexai
        from vertexai.preview.vision_models import ImageGenerationModel
        from google.cloud import storage
        from PIL import Image
        logger.info("✅ All imports successful!")
    except Exception as e:
        logger.error(f"❌ Import error: {e}")
        return
    
    logger.info("🚀 Environment test complete - ready for image generation!")

if __name__ == "__main__":
    main()
