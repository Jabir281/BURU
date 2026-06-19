# BRACU Advisor Chatbot — Complete Documentation

## What Is This?

A chatbot that answers questions about **BRAC University** (admissions, scholarships,
student life, academics, etc.). Built with a **Next.js frontend** + **Python FastAPI backend**,
powered by free cloud AI.

---

## Architecture Overview

```
┌─────────────────────┐         ┌──────────────────────┐
│   Next.js Frontend  │  HTTP   │   Python Backend     │
│   (localhost:3000)  │◄───────►│   (localhost:8000)   │
│                     │  /api/  │                      │
│  - Chat UI          │  chat   │  - ChromaDB search   │
│  - Quick buttons    │         │  - Embedding model   │
│  - Source links     │         │  - Groq API calls    │
└─────────────────────┘         └──────────────────────┘
```

**Why two services?** The embedding model (`sentence-transformers`) and ChromaDB
are Python-only. They can't run inside Next.js. So the Python backend handles all
AI work, and Next.js handles the UI and API routing.

---

## How the Chatbot Processes a Question

When a user types a question (e.g. *"What scholarships are available?"*), the
chatbot does this:

```
User types question in browser (Next.js)
         │
         ▼
Next.js sends POST /api/chat to Python backend
         │
         ▼
Layer 1 Guardrail: Is another university mentioned?
         │ (if passed)
         ▼
Convert question to vector (384 numbers)
         │
         ▼
Search ChromaDB for top 3 similar chunks
         │
         ▼
Layer 2 Guardrail: Is similarity high enough?
         │ (if passed)
         ▼
Build context from chunks (max 4000 chars)
         │
         ▼
Call Groq API: context + question → natural answer
         │ (if Groq fails, try Gemini)
         ▼
Return answer + source URLs to frontend
         │
         ▼
Display in chat bubble with source links
```

---

## Project Structure

```
D:\BURU\
├── backend/                        # Python FastAPI server
│   ├── main.py                     # Server endpoints (health, chat)
│   └── requirements.txt            # Python deps for the server
│
├── frontend/                       # Next.js web app
│   ├── src/app/
│   │   ├── page.js                 # Chat UI (input, bubbles, buttons)
│   │   ├── layout.js               # Page layout wrapper
│   │   ├── globals.css             # Tailwind + custom CSS vars
│   │   └── api/chat/route.js       # Proxies to Python backend
│   ├── package.json
│   └── next.config.mjs
│
├── data/
│   ├── raw/bracu_pages.json        # Scraped BRACU web pages
│   ├── processed/chunks.json       # 153 searchable chunks
│   └── build_db.py                 # Generates chunks from raw data
│
├── scripts/
│   ├── scrape.py                   # Web scraper (cloudscraper + BS4)
│   └── parse_pdfs.py               # PDF text extractor (PyMuPDF)
│
├── chat_engine.py                  # Core AI: retrieval + LLM calls
├── guardrails.py                   # Two-layer off-topic detection
├── system_prompt.py                # BRACU-only prompt template
│
├── .env                            # GROQ_API_KEY (gitignored)
├── .gitignore
├── requirements.txt                # Main Python dependencies
└── Promts/
    ├── Brain.md                    # Persistent context for AI
    ├── Documentation.md            # This file
    └── Final_Plan.md               # Original plan
```

---

## Files & What They Do

### Python Backend (backend/)

| File | What it does |
|------|-------------|
| `backend/main.py` | FastAPI server with two endpoints. `GET /api/health` checks if server is alive. `POST /api/chat` receives a message, runs the AI pipeline, returns answer. |
| `backend/requirements.txt` | Just FastAPI + Uvicorn (the main deps are in root `requirements.txt`). |

### Next.js Frontend (frontend/)

| File | What it does |
|------|-------------|
| `src/app/page.js` | The main chat page. Shows message history, quick action buttons (Scholarships, Admission, Housing, Calendar), input box, and loading animation. |
| `src/app/layout.js` | HTML wrapper with BRACU branding in title/description. |
| `src/app/globals.css` | Tailwind CSS with custom BRACU colors (dark blue primary, gold accent). |
| `src/app/api/chat/route.js` | Next.js API route. Receives chat requests from the frontend, forwards them to the Python backend at `localhost:8000`, returns the response. If backend is down, shows a friendly error. |

### Core AI Logic (root files)

| File | What it does |
|------|-------------|
| `chat_engine.py` | The brain. Loads the embedding model (`all-MiniLM-L6-v2`), builds/loads ChromaDB, retrieves relevant chunks, limits context to 4000 chars, and calls Groq API. |
| `guardrails.py` | Two-layer off-topic detection. Layer 1: checks if another university is mentioned (Harvard, MIT, etc.). Layer 2: checks if the best matching chunk has enough similarity (threshold 0.3). |
| `system_prompt.py` | The instruction template given to Groq. Tells it to only answer from BRACU context and cite sources. |

### Data Collection (scripts/)

| File | What it does |
|------|-------------|
| `scripts/scrape.py` | Visits 34 BRACU web pages using `cloudscraper` (bypasses Cloudflare), extracts text with BeautifulSoup, saves to `data/raw/bracu_pages.json`. Only 10 yielded content. |
| `scripts/parse_pdfs.py` | Downloads PDFs from BRACU, extracts text with PyMuPDF, saves to `data/raw/bracu_pdfs.json`. (Not yet run — no PDF URLs confirmed yet.) |
| `data/build_db.py` | Reads all raw data, splits text into 800-char chunks (100-char overlap), saves 153 chunks to `data/processed/chunks.json`. |

---

## How to Run Locally

You need **two terminal windows**:

### Terminal 1 — Python Backend

```bash
cd D:\BURU
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Wait until you see: `Application startup complete.`

### Terminal 2 — Next.js Frontend

```bash
cd D:\BURU\frontend
npm run dev
```

Then open **http://localhost:3000** in your browser.

---

## How the Guardrails Work (Important!)

The chatbot has **two layers** of protection to prevent off-topic answers:

### Layer 1: Other University Detection (`guardrails.py:11`)

Checks if the user's question mentions a non-BRACU university by name.
If a university name is found and "brac" is NOT in the query, it's rejected.

**Passes (answered):** "Tell me about admission at BRACU"
**Rejected:** "Tell me about admission at Harvard"

### Layer 2: Similarity Threshold (`guardrails.py:19`)

After ChromaDB returns the best matching chunks, the similarity score is checked.
If the highest similarity is below 0.3, the question is rejected as off-topic.

**Passes (answered):** "What scholarships exist?"
**Rejected:** "Write Python code", "What is the capital of France?"

### When Both Pass

The top 3 chunks are sent to Groq's LLM (Llama 3.1 8B) to generate a natural
answer. If Groq fails, Gemini is the fallback.

---

## How to Add More Data

1. **Add URLs** to the `PRIORITY_PATHS` list in `scripts/scrape.py`
2. **Run scraper:** `python scripts/scrape.py`
3. **Rebuild chunks:** `python data/build_db.py`
4. **Delete old ChromaDB:** Remove the `bracu_chroma_db/` folder
5. **Restart backend** — ChromaDB rebuilds automatically

---

## How to Deploy

### Backend (Python)

- Deploy to **Render**, **Railway**, or **Hugging Face Spaces**
- Set `GROQ_API_KEY` as an environment variable
- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`

### Frontend (Next.js)

- Deploy to **Vercel** (easiest, integrates with GitHub)
- Set `BACKEND_URL` env var to the deployed backend URL
- Vercel will auto-detect Next.js

---

## Key Decisions & Why

| Decision | Why |
|----------|-----|
| **Next.js** over Streamlit | User wanted no third-party UI framework dependency. Full control over UI. |
| **FastAPI** over plain Flask | FastAPI has built-in validation (Pydantic), auto-docs, async support, and cleaner API code. |
| **Cloudscraper** over requests | BRACU website uses Cloudflare — requests gets 403 blocked. |
| **Two separate services** | Sentence-transformers + ChromaDB are Python-only. Can't run inside Next.js. |
| **Context limited to 4000 chars** | Groq free tier has a 6000 token/min limit. 4000 chars keeps us well under. |
| **3 chunks instead of 5** | Reduces token usage while still providing relevant context. |
| **llama-3.1-8b-instant** | llama3-8b-8192 was decommissioned. This is the replacement model. |

---

## Current Bugs / Limitations

1. **Only 10 BRACU pages scraped successfully** — many paths return empty (different HTML structure or Cloudflare blocking).
2. **No PDF data yet** — `parse_pdfs.py` is written but not executed (need working PDF URLs).
3. **No Gemini API key in .env** — the Gemini fallback will fail if Groq is down. Add `GEMINI_API_KEY=your_key` to `.env`.
4. **Scraped content includes navigation text** — the extracted text has menus/footer links mixed with actual content.
