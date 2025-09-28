#!/usr/bin/env python3
"""
Simple test for the /extract-base64 endpoint (base64 in request body)
"""

import base64
import requests
import json
import os

# API_URL = "http://localhost:8000"
API_URL = "https://plate-ocr-production.up.railway.app"
IMAGE_PATH = "images/plate2.jpg"

def test_extract_base64_endpoint():
    """Test the new /extract-base64 endpoint"""
    
    print("🧪 Testing /extract-base64 endpoint")
    print("=" * 40)
    
    # Check if image exists
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Image not found: {IMAGE_PATH}")
        return
    
    # Read and convert to base64
    with open(IMAGE_PATH, 'rb') as f:
        image_data = f.read()
    
    base64_string = base64.b64encode(image_data).decode('utf-8')
    print(f"📊 Image size: {len(image_data)} bytes")
    print(f"📊 Base64 length: {len(base64_string)} chars")
    
    # Test the new endpoint with base64 in request body
    payload = {
        "base64_image": base64_string
    }
    
    try:
        response = requests.post(
            f"{API_URL}/extract-base64",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"\n📤 Request sent to: {API_URL}/extract-base64")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print("❌ Error:")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def compare_endpoints():
    """Compare the old query param method vs new body method"""
    
    print("\n🔄 Comparing both methods")
    print("=" * 40)
    
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Image not found: {IMAGE_PATH}")
        return
    
    with open(IMAGE_PATH, 'rb') as f:
        image_data = f.read()
    
    base64_string = base64.b64encode(image_data).decode('utf-8')
    
    # Method 1: Query parameter (old way - likely to fail with large images)
    print("Method 1: Query Parameter")
    try:
        response1 = requests.post(
            f"{API_URL}/extract",
            params={"base64_image": base64_string},
            timeout=60
        )
        print(f"Status: {response1.status_code}")
        if response1.status_code != 200:
            print(f"Error: {response1.text[:200]}...")
    except Exception as e:
        print(f"Failed: {e}")
    
    # Method 2: Request body (new way)
    print(f"\nMethod 2: Request Body")
    try:
        response2 = requests.post(
            f"{API_URL}/extract-base64",
            json={"base64_image": base64_string},
            timeout=60
        )
        print(f"Status: {response2.status_code}")
        if response2.status_code == 200:
            result = response2.json()
            print(f"Success: {result.get('plate', 'No plate detected')}")
        else:
            print(f"Error: {response2.text[:200]}...")
    except Exception as e:
        print(f"Failed: {e}")

def main():
    print("🚗 Base64 Request Body Test")
    print("=" * 40)
    
    # Test server connectivity
    try:
        response = requests.get(f"{API_URL}/plates", timeout=10)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"⚠️  Server responded with: {response.status_code}")
    except:
        print("❌ Cannot connect to server")
        print("Start server with: uvicorn main:app --host 0.0.0.0 --port 8000")
        return
    
    # Test the new endpoint
    test_extract_base64_endpoint()
    
    # Compare both methods
    compare_endpoints()

if __name__ == "__main__":
    main()