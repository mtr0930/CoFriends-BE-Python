"""
Test script to verify FastAPI server without databases
"""
import sys
from fastapi.testclient import TestClient

# Set UTF-8 encoding for console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Temporarily disable database initialization for testing
import os
os.environ['SKIP_DB_INIT'] = 'true'

try:
    from main import app
    
    client = TestClient(app)
    
    # Test root endpoint
    print("Testing root endpoint...")
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    print(f"[OK] Root endpoint working: {data['message']}")
    
    # Test health endpoint
    print("\nTesting health endpoint...")
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    print(f"[OK] Health endpoint working: {data['status']}")
    
    # Test OpenAPI docs
    print("\nTesting OpenAPI docs...")
    response = client.get("/docs")
    assert response.status_code == 200
    print("[OK] OpenAPI docs accessible")
    
    print("\n" + "="*50)
    print("[SUCCESS] All basic tests passed!")
    print("="*50)
    print("\nAPI Endpoints:")
    print("  - Swagger UI: http://localhost:5000/docs")
    print("  - ReDoc: http://localhost:5000/redoc")
    print("  - Health Check: http://localhost:5000/health")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

