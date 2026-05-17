import time
from doc_agents import run_agents
from metrics import record_document,get_metrics
from graph_rag import build_graph,graph_search
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import PyPDF2
import io
import os
import requests
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

# ChromaDB setup
chroma_client = chromadb.Client()
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def call_gemini(prompt):
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(GEMINI_URL, json=body)
    data = response.json()
    if "error" in data:
        return "Error: " + data["error"].get("message", "Unknown")
    if "candidates" not in data:
        return "No response"
    return data["candidates"][0]["content"]["parts"][0]["text"]

def extract_text(file_bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks

def store_in_chromadb(text, doc_name="current_doc"):
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
    return collection

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

def parse_summary(raw):
    oneline, full = "", ""
    for line in raw.split("\n"):
        if line.startswith("ONE LINE:"):
            oneline = line.replace("ONE LINE:", "").strip()
        elif line.startswith("FULL:"):
            full = line.replace("FULL:", "").strip()
    return oneline, full

def parse_analyzer(raw):
    entities, risks, insights = [], [], []
    for line in raw.split("\n"):
        if line.startswith("ENTITIES:"):
            entities = [e.strip() for e in line.replace("ENTITIES:", "").split("|")]
        elif line.startswith("RISKS:"):
            risks = [r.strip() for r in line.replace("RISKS:", "").split("|")]
        elif line.startswith("INSIGHTS:"):
            insights = [i.strip() for i in line.replace("INSIGHTS:", "").split("|")]
    return entities, risks, insights

document_store = {}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    start_time= time.time()
    contents = await file.read()
    text = extract_text(contents)
    document_store["current"] = text

    # Store in ChromaDB
    store_in_chromadb(text)

    #Build Graph RAG
    chunks=chunk_text(text)
    build_graph(text,chunks)

    # Run LangGraph agents
    result = run_agents(text)

    processing_time = time.time() - start_time  # END TIMER
    pages = len(PyPDF2.PdfReader(io.BytesIO(contents)).pages)

    # Record metrics
    record_document(
        filename=file.filename,
        pages=pages,
        word_count=len(text.split()),
        processing_time=processing_time
    )

    return {
        "success": True,
        "summary": {
            "oneline": result["summary_oneline"] or "Summary not available",
            "paragraph": result["summary_full"] or "Full summary not available"
        },
        "entities": result["entities"] or ["No entities found"],
        "risks": result["risks"] or ["No risks found"],
        "insights": result["insights"] or ["No insights found"],
        "pages": pages,
        "word_count": len(text.split()),
        "processing_time": round(processing_time, 2)
    }

class Question(BaseModel):
    question: str

@app.post("/ask")
async def ask(q: Question):
    # Real RAG — search ChromaDB first
    relevant_context = search_chromadb(q.question)
    if not relevant_context:
        relevant_context = document_store.get("current", "")[:2000]

    answer = call_gemini(f"""Answer this question using only the context below.
Always cite which part of document supports your answer.
Context: {relevant_context}
Question: {q.question}""")
    return {"answer": answer}

@app.get("/health")
async def health():
    return {"status": "running", "chromadb": "connected"}

@app.get("/metrics")
async def metrics():
    return get_metrics()