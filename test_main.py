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

# Test 2 - Metrics endpoint
def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "total_questions" in data

# Test 3 - Ask without document
def test_ask_without_document():
    response = client.post("/ask",
        json={"question": "What is this about?"})
    assert response.status_code == 200
    assert "answer" in response.json()

# Test 4 - PDF upload
def test_pdf_upload():
    pdf_content = b"%PDF-1.4 test document"
    response = client.post("/analyze",
        files={"file": ("test.pdf",
               io.BytesIO(pdf_content),
               "application/pdf")})
    assert response.status_code == 200

# Test 5 - Multilingual question
def test_multilingual():
    response = client.post("/ask",
        json={"question": "यह क्या है?"})
    assert response.status_code == 200
    assert "answer" in response.json()

# Test 6 - Health has chromadb status
def test_health_chromadb():
    response = client.get("/health")
    assert "chromadb" in response.json()

# Test 7 - Metrics has avg processing time
def test_metrics_processing_time():
    response = client.get("/metrics")
    assert "avg_processing_time" in response.json()

# Test 8 - Ask returns string answer
def test_ask_returns_string():
    response = client.post("/ask",
        json={"question": "Hello"})
    assert isinstance(response.json()["answer"], str)

# Test 9 - Spanish question
def test_spanish_question():
    response = client.post("/ask",
        json={"question": "¿Qué es esto?"})
    assert response.status_code == 200

# Test 10 - French question
def test_french_question():
    response = client.post("/ask",
        json={"question": "Qu'est-ce que c'est?"})
    assert response.status_code == 200

# Test 11 - Metrics total documents
def test_metrics_total_documents():
    response = client.get("/metrics")
    assert response.json()["total_documents"] >= 0

# Test 12 - Metrics total questions
def test_metrics_total_questions():
    response = client.get("/metrics")
    assert response.json()["total_questions"] >= 0

# Test 13 - Ask empty question
def test_ask_empty_question():
    response = client.post("/ask",
        json={"question": ""})
    assert response.status_code == 200

# Test 14 - Metrics recent documents
def test_metrics_recent_documents():
    response = client.get("/metrics")
    assert "recent_documents" in response.json()

# Test 15 - Metrics languages detected
def test_metrics_languages():
    response = client.get("/metrics")
    assert "languages_detected" in response.json()