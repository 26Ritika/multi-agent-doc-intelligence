import os
import io
import time
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import PyPDF2
import chromadb
from chromadb.utils import embedding_functions
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from typing import List

from doc_agents import run_agents
from metrics import record_document, get_metrics
from graph_rag import build_graph, graph_search
from auth import (
    Token, User, UserInDB,
    authenticate_user, create_access_token,
    get_current_user, get_password_hash,
    fake_users_db
)
from export import export_results_pdf

# ── Logging ──────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

# ── ChromaDB ─────────────────────────────────────────────
chroma_client = chromadb.Client()
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# ── Rate Limiter ──────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── WebSocket Manager ─────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# ── FastAPI App ───────────────────────────────────────────
app = FastAPI(
    title="Multi Agent Document Intelligence",
    version="1.0.0",
    description="AI-powered document analysis using multi-agent architecture"
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Helper Functions ──────────────────────────────────────
def call_gemini(prompt):
    try:
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_URL, json=body)
        data = response.json()
        if "error" in data:
            return "Error: " + data["error"].get("message", "Unknown")
        if "candidates" not in data:
            return "No response"
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"Gemini error: {str(e)}")
        return f"Error: {str(e)}"

def extract_text(file_bytes):
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")

def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
    return chunks

def store_in_chromadb(text):
    try:
        chroma_client.delete_collection("documents")
    except:
        pass
    collection = chroma_client.create_collection(
        name="documents",
        embedding_function=embedding_fn
    )
    chunks = chunk_text(text)
    collection.add(
        documents=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )

def search_chromadb(question, n_results=3):
    try:
        collection = chroma_client.get_collection(
            name="documents",
            embedding_function=embedding_fn
        )
        results = collection.query(
            query_texts=[question],
            n_results=min(n_results, collection.count())
        )
        return " ".join(results["documents"][0])
    except:
        return ""

document_store = {}
results_store = {}

# ── Auth Endpoints ────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str = ""

@app.post("/register")
async def register(req: RegisterRequest):
    if req.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    fake_users_db[req.username] = {
        "username": req.username,
        "email": req.email,
        "hashed_password": get_password_hash(req.password)
    }
    return {"message": "User created successfully!"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# ── WebSocket ─────────────────────────────────────────────
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ── Main Endpoints ────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "running",
        "chromadb": "connected",
        "version": "1.0.0",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/analyze")
@limiter.limit("5/minute")
async def analyze(request: Request, file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    logger.info(f"Processing: {file.filename}")
    start_time = time.time()

    await manager.broadcast(f"Processing file: {file.filename}")

    try:
        contents = await file.read()
        text = extract_text(contents)

        if not text.strip():
            raise HTTPException(status_code=400, detail="Empty PDF")

        document_store["current"] = text

        await manager.broadcast("Storing in ChromaDB...")
        store_in_chromadb(text)

        await manager.broadcast("Building Graph RAG...")
        chunks = chunk_text(text)
        build_graph(text, chunks)

        await manager.broadcast("Running AI agents...")
        result = run_agents(text)

        processing_time = time.time() - start_time
        pages = len(PyPDF2.PdfReader(io.BytesIO(contents)).pages)

        record_document(
            filename=file.filename,
            pages=pages,
            word_count=len(text.split()),
            processing_time=processing_time
        )

        final_result = {
            "success": True,
            "summary": {
                "oneline": result["summary_oneline"] or "Not available",
                "paragraph": result["summary_full"] or "Not available"
            },
            "entities": result["entities"] or ["No entities found"],
            "risks": result["risks"] or ["No risks found"],
            "insights": result["insights"] or ["No insights found"],
            "pages": pages,
            "word_count": len(text.split()),
            "processing_time": round(processing_time, 2)
        }

        results_store["latest"] = final_result
        await manager.broadcast("Analysis complete!")
        logger.info(f"Done in {processing_time:.2f}s")
        return final_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class Question(BaseModel):
    question: str

@app.post("/ask")
@limiter.limit("10/minute")
async def ask(request: Request, q: Question):
    if not q.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    logger.info(f"Question: {q.question[:50]}")

    try:
        relevant_context = search_chromadb(q.question)
        if not relevant_context:
            relevant_context = document_store.get("current", "")[:2000]

        answer = call_gemini(f"""Answer using only context below.
Cite which part supports your answer.
Context: {relevant_context}
Question: {q.question}""")

        return {"answer": answer}

    except Exception as e:
        logger.error(f"QA error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/export/pdf")
async def export_pdf():
    if "latest" not in results_store:
        raise HTTPException(status_code=404, detail="No results to export")
    pdf_bytes = export_results_pdf(results_store["latest"])
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=report.pdf"}
    )

@app.get("/metrics")
async def metrics():
    return get_metrics()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)