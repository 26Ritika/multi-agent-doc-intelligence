import pytest
from fastapi.testclient import TestClient
from main import app
import io

client = TestClient(app)

# Test 1 - Health check
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "running"
    print("✅ Health check passed")

# Test 2 - Metrics endpoint
def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "total_questions" in data
    print("✅ Metrics endpoint passed")

# Test 3 - Ask without document
def test_ask_without_document():
    response = client.post("/ask",
        json={"question": "What is this about?"})
    assert response.status_code == 200
    assert "answer" in response.json()
    print("✅ Ask without document passed")

# Test 4 - PDF upload
def test_pdf_upload():
    # Create simple test PDF content
    pdf_content = b"%PDF-1.4 test document"
    response = client.post("/analyze",
        files={"file": ("test.pdf",
               io.BytesIO(pdf_content),
               "application/pdf")})
    assert response.status_code == 200
    print("✅ PDF upload passed")

# Test 5 - Multilingual question
def test_multilingual():
    response = client.post("/ask",
        json={"question": "यह क्या है?"})
    assert response.status_code == 200
    assert "answer" in response.json()
    print("✅ Multilingual test passed")