#!/usr/bin/env python3
"""
Test script for the base64 image functionality in the /extract endpoint
"""

import base64
import requests
import json
from pathlib import Path

# API endpoint
# API_URL = "http://localhost:8000/extract"
API_URL = "https://plate-ocr-production.up.railway.app/extract"

def image_to_base64(image_path):
    """Convert an image file to base64 string"""
    try:
        with open(image_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return None

def test_base64_upload(image_path):
    """Test uploading image via base64 string"""
    print(f"🔄 Converting {image_path} to base64...")
    
    base64_string = image_to_base64(image_path)
    if not base64_string:
        return
    
    print(f"📤 Sending base64 image to API...")
    
    # Send as query parameter
    params = {'base64_image': base64_string}
    
    try:
        response = requests.post(API_URL, params=params)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")

def test_base64_data_url(image_path):
    """Test uploading image as complete data URL"""
    print(f"🔄 Converting {image_path} to data URL...")
    
    try:
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
        
        # Get file extension to determine MIME type
        file_extension = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'jpeg',
            '.jpeg': 'jpeg',
            '.png': 'png',
            '.gif': 'gif',
            '.bmp': 'bmp',
            '.webp': 'webp'
        }
        
        image_type = mime_types.get(file_extension, 'jpeg')
        base64_string = base64.b64encode(image_data).decode('utf-8')
        data_url = f"data:image/{image_type};base64,{base64_string}"
        
        print(f"📤 Sending data URL to API...")
        
        params = {'base64_image': data_url}
        response = requests.post(API_URL, params=params)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
        
    except Exception as e:
        print(f"Error: {e}")

def create_test_base64():
    """Create a simple test base64 string for demonstration"""
    # Create a simple 1x1 pixel PNG image
    # This is a minimal valid PNG image in base64
    tiny_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI/YPxXEQAAAABJRU5ErkJggg=="
    
    print("🧪 Testing with minimal PNG image...")
    params = {'base64_image': tiny_png_base64}
    
    try:
        response = requests.post(API_URL, params=params)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("🚗 License Plate OCR - Base64 Test Script")
    print("=" * 50)
    
    # Test with minimal image first
    # print("\n1️⃣ Testing with minimal test image:")
    # create_test_base64()
    
    # Example usage with real image file
    # print("\n2️⃣ To test with your own image:")
    # print("   Uncomment and modify the lines below:")
    # print('   test_base64_upload("/path/to/your/license_plate.jpg")')
    # print('   test_base64_data_url("/path/to/your/license_plate.jpg")')
    
    # Uncomment these lines to test with a real image:
    image_path = "images/plate2.jpg"
    if Path(image_path).exists():
        print(f"\n3️⃣ Testing base64 string method:")
        test_base64_upload(image_path)
        
        print(f"\n4️⃣ Testing data URL method:")
        test_base64_data_url(image_path)
    else:
        print(f"\n❌ Image file not found: {image_path}")

if __name__ == "__main__":
    main()