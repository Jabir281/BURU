# Brac University AI Chatbot — Full Development Plan (Start to Finish)

> **Goal**: Build a prototype AI chatbot that answers only Brac University-related queries (academic info, admissions, fees, schedules, etc.) using **100% free/open-source tools**. Deploy as a web app so anyone with a link can test it.

---

## Phase 0: Data Collection & Preparation (Foundation)

### Step 0.1 — Gather Official University Data
- Collect all publicly available Brac University documents:
  - Academic calendar
  - Course catalog (undergrad & grad)
  - Admission requirements & deadlines
  - Tuition fee structure
  - Exam schedules & grading policy
  - Department contacts & faculty list
  - Student handbook / rules & regulations
  - FAQ pages from the university website
- Store raw files in a folder: `data/raw/`

### Step 0.2 — Clean & Structure the Data
- Convert PDFs/HTML to plain text (use `pdfplumber` / `BeautifulSoup`)
- Split content into Q&A pairs or chunked documents (e.g., 500–1000 tokens per chunk)
- Save as structured JSON/CSV:
  ```json
  [
    { "id": "1", "question": "When is the admission deadline?", "answer": "..." },
    { "id": "2", "chunk": "Full text paragraph about fee structure", "source": "fees.pdf" }
  ]
  ```
- Output folder: `data/processed/`

---

## Phase 1: Backend — RAG (Retrieval-Augmented Generation) System

### Step 1.1 — Set Up Python Environment
- Create a virtual environment: `python -m venv venv`
- Install core dependencies (all free):
  - `langchain` — orchestration framework
  - `chromadb` or `faiss-cpu` — vector database
  - `sentence-transformers` — free embedding model (e.g., `all-MiniLM-L6-v2`)
  - `llama-cpp-python` — run local LLM (e.g., Mistral 7B / Phi-3-mini)
  - `fastapi` + `uvicorn` — API server
  - `pypdf`, `pdfplumber`, `beautifulsoup4` — document parsing

### Step 1.2 — Create Embeddings & Vector Store
- Load processed chunks
- Generate embeddings using `sentence-transformers/all-MiniLM-L6-v2`
- Store vectors in ChromaDB (persisted to disk)
- Test retrieval with sample queries

### Step 1.3 — Integrate Local LLM
- Download a small open-source LLM (e.g., **Phi-3-mini-4k-instruct Q4_K_M** GGUF — ~2.5GB, runs on 8GB RAM)
- Load with `llama-cpp-python` (CPU-only, no GPU needed)
- Create a LangChain chain:
  - **Retriever** → pulls top-3 relevant chunks from ChromaDB
  - **Prompt template** → instructs LLM to answer **only** from retrieved context, refuse off-topic questions
  - **LLM** → generates the final answer
- Test with 10–15 real queries

### Step 1.4 — Add Topic Guard (Off-Topic Filter)
- Before answering, run a classifier or a simple embedding-similarity check:
  - If query embedding is too far from any university chunk → return: *"I can only answer questions about Brac University."*
- This ensures the "no unrelated questions" requirement.

---

## Phase 2: Backend API

### Step 2.1 — Build FastAPI Server
- Endpoints:
  - `POST /chat` — accepts `{ "message": "..." }`, returns `{ "reply": "..." }`
  - `GET /health` — health check
- Add CORS middleware (for web frontend access)
- Load the RAG pipeline at startup (singleton)
- Implement streaming response for better UX

### Step 2.2 — Test API Locally
- Run `uvicorn main:app --reload`
- Test with Postman / curl / browser Swagger UI (`/docs`)

---

## Phase 3: Frontend — Web UI

### Step 3.1 — Build a Minimal Chat Interface
- Pure HTML + CSS + JavaScript (no framework needed for prototype)
- Or use **Streamlit / Gradio** (fastest — free, Python-based, no separate frontend code)
- Recommended: **Gradio** for quick prototype:
  ```python
  gr.ChatInterface(fn=chat_fn, title="BracU Info Bot")
  ```
- Chat bubbles, loading indicator, input box

### Step 3.2 — Connect Frontend to Backend
- Frontend sends `POST /chat` requests
- Displays responses in chat UI
- Handle errors gracefully

### Step 3.3 — Test Full Stack Locally
- Run both backend + frontend
- Test with ~20 real university-related queries
- Test with 5 off-topic queries → must be rejected

---

## Phase 4: Deployment (Free Tier)

### Step 4.1 — Deploy Backend
- Option A: **Render.com** (free tier — 750 hrs/month, 512MB RAM)
- Option B: **PythonAnywhere** (free tier — limited but works for demo)
- Option C: **Hugging Face Spaces** (free CPU/GPU, easy FastAPI/Gradio deployment)
- Recommended: **Hugging Face Spaces** — simplest for prototype
  - Create a Space, push code via git, set `app.py` as entry point

### Step 4.2 — Deploy Data (Vector Store)
- Embeddings & ChromaDB must be bundled or re-created on startup
- For HF Spaces: include a pre-built vector store in the repo (within size limits) or add a startup script to rebuild

### Step 4.3 — Get a Public URL
- Hugging Face Spaces gives `<your-space>.hf.space`
- Share this link with testers & university authority

---

## Phase 5: Testing & Polish

### Step 5.1 — Test with Real Users
- Send the link to 3–5 fellow BracU students
- Ask them to try 5–10 common queries
- Collect feedback on:
  - Accuracy of answers
  - Response speed
  - UX / UI clarity

### Step 5.2 — Iterate
- Add more data for weak areas
- Tune chunk size / retrieval top-k / prompt template
- Improve off-topic rejection accuracy

### Step 5.3 — Prepare Presentation
- Prepare a short demo script (5–10 min)
- Show:
  - Student asks "When is the fall deadline?" → answers correctly
  - Student asks "Solve 2+2" → refuses politely
- Highlight: 100% free tools, runs on a laptop, deployed on HF Spaces

---

## Phase 6: Pitch to Authority

### Step 6.1 — Demonstrate Prototype
- Let them test the live link on their own devices
- Show the codebase (GitHub repo — make it private or public as needed)

### Step 6.2 — Propose Next Steps (If They Invest)
- Scale up: move to paid cloud (better LLM, GPU, higher traffic)
- Add: user analytics, feedback loop, admin dashboard for updating data
- Integrate with university portal APIs for real-time data (if available)

---

## Tools & Their Roles (Summary)

| Tool | Purpose | Cost |
|---|---|---|
| `langchain` | RAG pipeline orchestration | Free |
| `chromadb` / `faiss-cpu` | Vector store | Free |
| `sentence-transformers` | Embeddings | Free |
| `Phi-3-mini` (GGUF) | Local LLM | Free |
| `llama-cpp-python` | Run LLM on CPU | Free |
| `FastAPI` | Backend API | Free |
| `Gradio` or HTML/CSS/JS | Web UI | Free |
| Hugging Face Spaces | Hosting | Free |
| VS Code + Continue/Copilot | Code assistant | Free |

---

## What to Tackle First (Immediate Next Steps)

1. **Create a GitHub repo** for version control.
2. **Install Python 3.10+** if not already.
3. **Collect all BracU data** from the web portal (manually or via scraping).
4. **Follow Phase 1** — build the RAG system locally.
5. Use VS Code + AI agent for code help as you go.

> **This plan expects no budget, works on your i5/8GB laptop, and produces a shareable web prototype ready for demo.**
