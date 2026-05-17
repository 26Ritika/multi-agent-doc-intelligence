# 🤖 Multi-Agent Document Intelligence System

An AI-powered document analysis system using 6 specialized agents built with Google Gemini API and React.

## 🏗️ Architecture
User uploads PDF
↓
Orchestrator Agent → coordinates all agents
↓
Extractor Agent → extracts raw text
Summarizer Agent → generates summaries
Analyzer Agent → finds entities & risks
QA Agent → answers questions (RAG)
Aggregator Agent → combines all outputs
↓
React Dashboard → displays results

## 🛠️ Tech Stack

- **Frontend**: React.js
- **Backend**: FastAPI (Python)
- **AI**: Google Gemini API
- **PDF Processing**: PyPDF2
- **Architecture**: Multi-Agent + RAG

## ✨ Features

- 📄 PDF upload and processing
- 🤖 6 specialized AI agents
- 📊 Real-time agent activity logs
- 🌈 Multi-level document summarization