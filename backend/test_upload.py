"""
Simple test script to verify upload functionality
"""
import requests
import sys

def test_upload():
    # Test health endpoint
    print("1️⃣ Testing health endpoint...")
    response = requests.get("http://localhost:8000/health")
    print(f"   Health check: {response.status_code} - {response.json()}")
    
    # Test status endpoint
    print("\n2️⃣ Testing status endpoint...")
    response = requests.get("http://localhost:8000/status")
    print(f"   Status: {response.json()}")
    
    # Test upload with a sample text file (simulating PDF)
    print("\n3️⃣ Ready to test upload...")
    print("   To test upload, you need to:")
    print("   - Use the UI at http://localhost:5174")
    print("   - Or use: curl -F 'file=@yourfile.pdf' -F 'title=Test' http://localhost:8000/upload_pdf")
    
if __name__ == "__main__":
    test_upload()
