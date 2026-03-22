# FieldAssist AI

FieldAssist AI is a completely offline, highly secure, and privacy-preserving Legal & Procedural AI Assistant. It is designed to act as an advanced Multi-Modal RAG (Retrieval-Augmented Generation) engine specifically tailored for fields that strictly forbid data from leaving standard offline boundaries (e.g., military networks, secret internal deployments, or confidential legal firms).

## Core Features
1. **100% Offline Capability**: Runs seamlessly via local HuggingFace Embeddings, ChromaDB, and local LLMs (like Ollama). No API keys or internet connection required.
2. **Context-Specific Routing**: Intelligent vector isolation separating distinct domains (e.g., `bns_2023`, `military_law`, `tccc_guides`).
3. **Persistent Native History**: Implements a zero-configuration SQLite layer on the backend to elegantly track and restore conversation loops dynamically.
4. **Sleek Interface**: Shipped with an ultra-premium, dark-themed React + Vite SPA ensuring rapid interactions and deep focus.

## Tech Stack
- **Backend API**: FastAPI (Python)
- **RAG Engine**: LangChain, ChromaDB, HuggingFace Sentence Transformers
- **Database**: Native SQLite3
- **Frontend**: React.js, Vite

## Getting Started

### 1. Prerequisites
- Python 3.9+ 
- Node.js 18+
- [Ollama](https://ollama.com/) (Required for the local model runtime)

### 2. Install Backend Dependencies
Navigate to the root directory and create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. Embed your Vector Database (One-time setup)
Place your PDF files logically inside the `data/` folder grouped by category (e.g., `data/bns_2023/`, `data/military_law/`). Then, execute the automated batch ingestion script:
```bash
python3 -m backend.ingestion
```

### 4. Running the Complete System
**Start the Backend Engine:**
Make sure you are in the root directory and your virtual environment is active.
```bash
uvicorn backend.main:app --reload --port 8000
```

**Start the Frontend Client:**
In a separate terminal window:
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:5173`. Select your required legal or medical context category, and begin querying securely!
