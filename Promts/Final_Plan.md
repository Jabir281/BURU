# BRACU AI Chatbot — Final Optimized Plan

> Based on cons analysis of two prior plans. Combines the best of both while fixing all weaknesses.

---

## Cons of Plan A (My Original Plan)

| # | Con | Severity |
|---|-----|----------|
| 1 | **Suggests running a local LLM (Phi-3-mini GGUF) on i5-6200U + 8GB RAM** — will crash the laptop. Even quantized models need 16GB+ RAM for acceptable performance on CPU. | **Critical** |
| 2 | Recommends FastAPI + separate frontend (Gradio/HTML) instead of Streamlit — unnecessary complexity for a prototype. More code to write and debug. | Medium |
| 3 | Deployment plan on Hugging Face Spaces lacks detail on handling the ChromaDB vector store size and Git LFS limits. | Medium |
| 4 | Doesn't leverage free cloud API tiers (Groq, Gemini) which give vastly faster inference than any local setup. | High |
| 5 | No backup plan if local LLM inference fails or is too slow. | Medium |

## Cons of Plan B (Kimi's Plan)

| # | Con | Severity |
|---|-----|----------|
| 1 | **Keyword-based guardrail is weak** — query "Tell me about admission at Harvard" contains "admission" and passes the filter, then RAG retrieves BRACU admission info and the LLM answers about *BRACU* admission to a *Harvard* question. Misleading. | **Critical** |
| 2 | Relies entirely on Groq API free tier with no fallback. If Groq changes/removes free tier, the chatbot dies. | High |
| 3 | Single monolithic `app.py` (~1000 lines) — hard to debug, test, or modify individual components. | Medium |
| 4 | Scrapes only ~12 BRACU pages — misses PDF documents (handbook, forms, policies) and deeper department pages. | Medium |
| 5 | Firecrawl dependency (500 free credits, then paid) — you'll exhaust credits quickly if you scrape more pages or iterate. | Low-Medium |
| 6 | No mechanism to handle PDFs — many BRACU documents (handbook, fee structure, forms) are PDF-only. | Medium |
| 7 | ChromaDB folder can exceed 100MB with enough data, hitting GitHub's file size limit. | Low-Medium |

---

# Final Optimized Plan (Fixes All Cons Above)

## Architecture Overview

```
Your Laptop (Development ONLY — lightweight tasks)
    │
    ├── VS Code + Python (run scrapers, chunkers, test queries)
    │
    ↓
GitHub Repository (Code only — NO vector DB in repo)
    │
    ↓
Streamlit Cloud (Free hosting — builds vector DB on startup)
    │
    ├── Free API #1: Groq (Llama 3 8B — fast primary LLM)
    ├── Free API #2: Gemini (Fallback LLM if Groq fails)
    └── Sentence-Transformers (all-MiniLM-L6-v2 — runs on Streamlit Cloud CPU)
```

**Key difference:** The vector database is NOT committed to GitHub. Instead, it's rebuilt on Streamlit Cloud at startup from a compressed JSON file (<5MB). This avoids the 100MB GitHub limit entirely.

---

## Phase 0: Environment Setup (Day 1)

### 0.1 Install Python 3.11
- Download from python.org
- During install: CHECK **"Add Python to PATH"**
- Verify: `python --version`

### 0.2 Install VS Code Extensions
- Python (by Microsoft)
- Pylance
- GitLens (optional, helps with Git)

### 0.3 Get Free API Keys (Get BOTH — one is fallback)

| API | URL | Free Tier | Purpose |
|-----|-----|-----------|---------|
| **Groq** | console.groq.com | Sign up free, get key | Primary LLM (Llama 3 8B) |
| **Gemini** | aistudio.google.com | 1,500 requests/day | Fallback LLM |

Store in `.env` file (local dev only):
```
GROQ_API_KEY=gsk_your_key
GEMINI_API_KEY=your_key
```

### 0.4 Create Project Structure
```
bracu-chatbot/
├── .env                          # API keys (gitignored)
├── .gitignore                    # Ignore .env, chroma_db/, cache/
├── requirements.txt
├── app.py                        # Streamlit app (Cloud entry point)
├── chat_engine.py                # Core logic: retrieval + LLM call
├── guardrails.py                 # OFF-TOPIC DETECTION (improved)
├── system_prompt.py              # BRACU-only system prompt
├── data/
│   ├── raw/                      # Original scraped content
│   ├── processed/
│   │   └── chunks.json           # Compressed chunks (<5MB)
│   └── build_db.py               # Script to generate chunks.json
├── scripts/
│   ├── scrape.py                 # BRACU website scraper
│   └── parse_pdfs.py             # PDF extractor (PyMuPDF)
└── README.md
```

Why this structure: Modular code. Each component is testable independently.

---

## Phase 1: Data Collection — Full Coverage (Day 2–5)

### 1.1 Scrape All BRACU Web Pages (Not Just 12)

**Fix for Kimi's Con #4:** Scrape comprehensively, not just 12 pages.

Use `requests` + `BeautifulSoup` (free, no credit limits — fixes Firecrawl dependency):

```python
# scripts/scrape.py
import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin

BRACU_BASE = "https://www.bracu.ac.bd"

PRIORITY_PATHS = [
    # Academics
    "/academics",
    "/academic-dates",
    "/schools-and-departments",
    "/programs",
    "/programs/undergraduate",
    "/programs/graduate",
    # Admissions - undergrad
    "/admissions",
    "/admissions/undergraduate",
    "/admissions/undergraduate/admission-requirements",
    "/admissions/undergraduate/application-procedure",
    "/admissions/undergraduate/tuition-and-fees",
    "/admissions/undergraduate/scholarships-and-financial-aid",
    # Admissions - graduate
    "/admissions/graduate",
    "/admissions/graduate/admission-requirements",
    "/admissions/graduate/tuition-and-fees",
    "/admissions/graduate/scholarships-and-financial-aid",
    # Student Life
    "/student-life",
    "/student-life/residential-semester",
    "/student-life/housing-and-dining",
    "/student-life/medical-center",
    "/student-life/counseling-and-wellness",
    "/student-life/career-services",
    "/student-life/student-clubs",
    "/student-life/sports-and-recreation",
    "/student-life/dress-code",
    # Services
    "/office-of-academic-advising",
    "/office-of-career-services",
    "/library",
    "/transport",
    "/it-services",
    # Policies
    "/policies-and-procedures",
    "/academic-policies",
    "/code-of-conduct",
    # Announcements
    "/announcements",
]

def scrape_page(url):
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove nav, footer, scripts
        for tag in soup(["nav", "footer", "script", "style", "header"]):
            tag.decompose()
        main = soup.find("main") or soup.find("article") or soup.find("div", class_="content") or soup
        text = main.get_text(separator="\n", strip=True)
        return text
    except Exception as e:
        print(f"  Failed: {e}")
        return None

all_content = {}
for path in PRIORITY_PATHS:
    url = urljoin(BRACU_BASE, path)
    print(f"Scraping: {url}")
    content = scrape_page(url)
    if content and len(content) > 100:
        all_content[url] = content
        print(f"  OK ({len(content)} chars)")
    else:
        print(f"  Empty or failed")
    time.sleep(1)  # Be polite

with open("data/raw/bracu_pages.json", "w", encoding="utf-8") as f:
    json.dump(all_content, f, ensure_ascii=False, indent=2)

print(f"Scraped {len(all_content)} pages")
```

### 1.2 Extract PDFs — Critical Missing Piece

**Fix for Kimi's Con #6:** Use `PyMuPDF` (fitz) — free, no API needed.

```python
# scripts/parse_pdfs.py
import fitz  # PyMuPDF
import json
import os
import requests
from urllib.parse import urljoin

PDF_URLS = [
    "https://www.bracu.ac.bd/sites/default/files/student-handbook.pdf",
    # Add more PDF URLs as you find them
]

def download_and_extract(pdf_url):
    local_path = f"data/raw/pdfs/{os.path.basename(pdf_url)}"
    os.makedirs("data/raw/pdfs", exist_ok=True)
    
    # Download
    resp = requests.get(pdf_url)
    with open(local_path, "wb") as f:
        f.write(resp.content)
    
    # Extract text
    doc = fitz.open(local_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

pdf_content = {}
for url in PDF_URLS:
    print(f"Extracting PDF: {url}")
    text = download_and_extract(url)
    if len(text) > 100:
        pdf_content[url] = text

with open("data/raw/bracu_pdfs.json", "w", encoding="utf-8") as f:
    json.dump(pdf_content, f, ensure_ascii=False, indent=2)
```

### 1.3 Chunk All Content

Combine web pages + PDFs → clean chunks (800 chars each, 100 char overlap).

### 1.4 Build Compressed Chunks JSON (NOT a full ChromaDB)

**Fix for GitHub size limit (My Con #3 + Kimi's Con #7):** Store chunks as compressed JSON (<5MB). The vector DB is rebuilt on Streamlit Cloud at startup.

```python
# data/build_db.py — Generates chunks.json (NOT ChromaDB)
import json
import re

# Load all raw data
with open("data/raw/bracu_pages.json", "r") as f:
    pages = json.load(f)
with open("data/raw/bracu_pdfs.json", "r") as f:
    pdfs = json.load(f)

all_sources = {**pages, **pdfs}
chunks = []

def chunk_text(text, source_url, chunk_size=800, overlap=100):
    # ... (same chunking logic as Kimi's plan, but cleaner)
    text = re.sub(r'\n+', '\n', text).strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    current_chunk = []
    current_len = 0
    for sent in sentences:
        if current_len + len(sent) > chunk_size and current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "id": len(chunks),
                "text": chunk_text,
                "source": source_url
            })
            # overlap: keep last 2 sentences
            overlap_text = " ".join(current_chunk[-2:]) if len(current_chunk) >= 2 else current_chunk[-1]
            current_chunk = [overlap_text, sent]
            current_len = len(overlap_text) + len(sent)
        else:
            current_chunk.append(sent)
            current_len += len(sent)
    if current_chunk:
        chunks.append({
            "id": len(chunks),
            "text": " ".join(current_chunk),
            "source": source_url
        })

for url, content in all_sources.items():
    chunk_text(content, url)

with open("data/processed/chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False)

print(f"Created {len(chunks)} chunks -> data/processed/chunks.json")
```

**Result:** `chunks.json` is typically 2–5MB for 20–30 pages. Easily fits in GitHub.

---

## Phase 2: Core Chat Engine (Day 6–10)

### 2.1 Modular Code Structure (Fix for My Con #2 + Kimi's Con #3)

**`guardrails.py`** — Improved off-topic detection (Fix for Kimi's Con #1):

The critical flaw: a keyword check alone can't distinguish "Tell me about admission at Harvard" from "Tell me about admission at BRACU". The first should be rejected, the second should be answered.

**Solution:** Two-layer guardrail:

1. **Layer 1 (Pre-retrieval):** Check if query explicitly mentions another university by name → reject immediately.
2. **Layer 2 (Post-retrieval):** After RAG retrieves top chunks, check if the retrieved similarity score is above a threshold. Low similarity → the query wasn't about BRACU content → reject.

```python
# guardrails.py
import re

OTHER_UNIVERSITIES = [
    "harvard", "mit", "stanford", "oxford", "cambridge", "yale",
    "princeton", "columbia", "buet", "du", "cu", "ru", "juniv",
    "north south", "north-south", "northsouth", "australian", "east west",
    "daffodil", "ulab", "uiu", "iub", "independent", "american"
]

def mentions_other_university(query):
    """Layer 1: Reject if another university is explicitly mentioned."""
    q = query.lower()
    for uni in OTHER_UNIVERSITIES:
        if uni in q and "brac" not in q:
            return True
    return False

def is_relevant_by_similarity(query_embedding, retrieved_embeddings, threshold=0.3):
    """Layer 2: Check if the best retrieved chunk is similar enough to the query."""
    if not retrieved_embeddings:
        return False
    import numpy as np
    q_vec = np.array(query_embedding)
    similarities = [np.dot(q_vec, np.array(r)) / (np.linalg.norm(q_vec) * np.linalg.norm(np.array(r))) for r in retrieved_embeddings]
    return max(similarities) >= threshold

def get_rejection_message(reason="off_topic"):
    messages = {
        "other_university": "I can only help with questions related to BRAC University. You mentioned another institution. Please ask me about BRACU instead!",
        "off_topic": "I can only answer questions about BRAC University — admissions, academics, scholarships, student life, and more. Ask me something BRACU-related!",
        "no_info": "I don't have that information in my current knowledge base. Please check the official BRACU website or contact the relevant office directly.",
    }
    return messages.get(reason, messages["off_topic"])
```

**`chat_engine.py`** — Core RAG logic (separate from UI):

```python
# chat_engine.py
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
import requests
import os
from guardrails import mentions_other_university, is_relevant_by_similarity, get_rejection_message

CHUNKS_PATH = "data/processed/chunks.json"
CHROMA_PATH = "./bracu_chroma_db"

# Global cache (loaded once by Streamlit)
_collection = None
_model = None

def load_or_build_db():
    """Load chunks.json, build ChromaDB in memory, return collection + model."""
    global _collection, _model
    if _collection is not None:
        return _collection, _model
    
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    
    _model = SentenceTransformer('all-MiniLM-L6-v2')
    
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    # Check if already built
    try:
        _collection = client.get_collection("bracu_knowledge")
        return _collection, _model
    except:
        pass
    
    _collection = client.create_collection("bracu_knowledge")
    
    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [c["text"] for c in batch]
        ids = [str(c["id"]) for c in batch]
        sources = [c["source"] for c in batch]
        embeddings = _model.encode(texts).tolist()
        _collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=[{"source": s} for s in sources]
        )
    
    return _collection, _model

def retrieve(query, top_k=5):
    collection, model = load_or_build_db()
    query_emb = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_emb, n_results=top_k, include=["documents", "metadatas", "embeddings"])
    return results, query_emb

def call_llm(provider, system_prompt, user_query):
    """Call LLM via Groq (primary) or Gemini (fallback)."""
    if provider == "groq":
        key = os.getenv("GROQ_API_KEY")
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            },
            timeout=30
        )
        return resp.json()["choices"][0]["message"]["content"]
    
    elif provider == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
            json={
                "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser: {user_query}"}]}]
            },
            timeout=30
        )
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    
    return "AI provider unavailable."

def generate_response(user_query):
    # Layer 1: Check for other university mention
    if mentions_other_university(user_query):
        return {"answer": get_rejection_message("other_university"), "sources": []}
    
    # Retrieve
    results, query_emb = retrieve(user_query)
    
    if not results["documents"][0]:
        return {"answer": get_rejection_message("no_info"), "sources": []}
    
    # Layer 2: Check similarity threshold
    retrieved_embs = results.get("embeddings", [[]])[0]
    if not is_relevant_by_similarity(query_emb[0], retrieved_embs, threshold=0.3):
        return {"answer": get_rejection_message("off_topic"), "sources": []}
    
    # Build context
    context_parts = []
    sources = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        context_parts.append(doc)
        sources.append(meta["source"])
    
    context = "\n\n---\n\n".join(context_parts)
    
    from system_prompt import BRACU_SYSTEM_PROMPT
    system_msg = BRACU_SYSTEM_PROMPT.format(context=context)
    
    # Try Groq first, fallback to Gemini
    try:
        answer = call_llm("groq", system_msg, user_query)
    except Exception as e:
        print(f"Groq failed: {e}. Falling back to Gemini.")
        try:
            answer = call_llm("gemini", system_msg, user_query)
        except Exception as e2:
            answer = f"Sorry, both AI services are unavailable right now. Please try again later. (Error: {e2})"
    
    return {"answer": answer, "sources": list(set(sources))}
```

**`system_prompt.py`** — Same as Kimi's but with tighter rules.

### 2.2 Streamlit UI (`app.py`)

Same approach as Kimi's but cleaner — imports from `chat_engine.py`:

```python
# app.py
import streamlit as st
from chat_engine import generate_response, load_or_build_db

st.set_page_config(page_title="BRACU Advisor", page_icon="🎓", layout="centered")

# Initialize (loads vector DB on first request)
with st.spinner("Loading BRACU knowledge base..."):
    load_or_build_db()

st.title("🎓 BRACU Advisor")
st.caption("Ask about admissions, academics, scholarships, student life, and more!")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            st.caption(f"Sources: {', '.join(msg['sources'])}")

# Quick buttons
cols = st.columns(4)
quick = {}
with cols[0]: quick["scholarship"] = st.button("💰 Scholarships")
with cols[1]: quick["admission"] = st.button("📝 Admission")
with cols[2]: quick["housing"] = st.button("🏠 Housing")
with cols[3]: quick["calendar"] = st.button("📅 Calendar")

quick_map = {
    "scholarship": "What scholarships are available at BRAC University?",
    "admission": "What are the undergraduate admission requirements?",
    "housing": "Tell me about student accommodation at BRACU",
    "calendar": "What are the important academic dates?",
}

user_input = None
for key, clicked in quick.items():
    if clicked:
        user_input = quick_map[key]

if not user_input:
    user_input = st.chat_input("Ask me anything about BRAC University...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = generate_response(user_input)
        st.markdown(result["answer"])
        if result["sources"]:
            st.caption(f"Sources: {', '.join(result['sources'])}")
    
    st.session_state.messages.append({"role": "assistant", "content": result["answer"], "sources": result["sources"]})
```

---

## Phase 3: Testing & Hardening (Day 11–14)

### 3.1 Test Against Edge Cases (Fix for Kimi's Con #1)

Add these test cases to verify guardrails:

| Query | Expected | Why |
|-------|----------|-----|
| "Tell me about admission at Harvard" | Rejected (Layer 1) | Other university mentioned |
| "Tell me about admission" | Answered (BRACU context) | No other university named |
| "What is the capital of France?" | Rejected (Layer 2) | Low similarity to BRACU docs |
| "Solve 2x + 5 = 15" | Rejected (Layer 2) | Low similarity |
| "Write Python code" | Rejected (Layer 2) | Low similarity |
| "I feel stressed about exams" | Answered (counseling info) | Related to BRACU student services |
| "When is the fall 2026 deadline?" | Answered | Good match with BRACU data |

### 3.2 Adjust Similarity Threshold

Test with 20 valid + 10 invalid queries. Adjust `threshold` in `is_relevant_by_similarity()` until:
- Valid queries pass (recall > 90%)
- Invalid queries are rejected (precision > 90%)

Default 0.3 is a starting point. Tune to 0.25–0.35 based on results.

---

## Phase 4: Deployment (Day 15–17)

### 4.1 Prepare for Streamlit Cloud

**`requirements.txt`:**
```
streamlit==1.40.0
chromadb==0.5.0
sentence-transformers==3.0.0
requests==2.32.0
python-dotenv==1.0.0
numpy==1.26.0
```

**`.gitignore`:**
```
.env
__pycache__/
*.pyc
bracu_chroma_db/
.streamlit/secrets.toml
```

**Note:** `chunks.json` is small (<5MB) → committed to GitHub. `bracu_chroma_db/` is gitignored — rebuilt on Streamlit Cloud at startup.

### 4.2 Deploy Steps

1. Push to GitHub:
```bash
git init
git add .
git commit -m "BRACU Advisor v1"
git remote add origin https://github.com/YOUR_USERNAME/bracu-advisor.git
git branch -M main
git push -u origin main
```

2. Go to share.streamlit.io → New app → Select repo

3. Add secrets:
   - `GROQ_API_KEY`: your key
   - `GEMINI_API_KEY`: your key (fallback)

4. Deploy

---

## Phase 5: Polish & Pitch (Day 18–21)

### 5.1 Demo Script

1. Open the live link on your phone
2. Ask: "What scholarships are available at BRACU?" (shows correct answer + citation)
3. Ask: "Tell me about admission at Harvard" (Layer 1 guardrail → rejects)
4. Ask: "Write Python code" (Layer 2 guardrail → rejects)
5. Ask: "I feel stressed about exams" (shows counseling service info)

### 5.2 Pitch to Authority

Key points:
- **Zero cost built** — all free/open-source tools
- **Not a generic chatbot** — two-layer guardrail ensures BRACU-only
- **Cites sources** — every answer links to official BRACU pages
- **Scalable** — can handle 100+ simultaneous users (Streamlit + Groq)
- **Student pain solved** — no more travel, queues, or searching fragmented websites

---

## Summary: What's Better in This Plan

| Old Con | How This Plan Fixes It |
|---------|----------------------|
| Local LLM will crash laptop (My Con #1) | Zero local inference — Groq API (primary) + Gemini API (fallback) |
| Weak keyword guardrail (Kimi's Con #1) | Two-layer guardrail: (1) other-university detection, (2) similarity threshold |
| Vector DB too big for GitHub (Kimi's Con #7) | Store compressed chunks.json (<5MB) in GitHub, rebuild ChromaDB on deploy |
| Single monolithic file (Kimi's Con #3) | Modular: `guardrails.py`, `chat_engine.py`, `system_prompt.py`, `app.py` |
| Firecrawl dependency / credit limit (Kimi's Con #5) | Use requests + BeautifulSoup (free, unlimited) + PyMuPDF for PDFs |
| Missing PDF content (Kimi's Con #6) | PyMuPDF extracts PDF text — no API needed |
| Only 12 pages scraped (Kimi's Con #4) | Scrape 30+ pages covering all departments, policies, services |
| No API fallback (Kimi's Con #2) | Groq primary, Gemini fallback — if one fails, the other works |
| Complex FastAPI + separate frontend (My Con #2) | Streamlit — single framework, auto-deploy to Streamlit Cloud |

---

## Immediate Next Steps (Right Now)

1. Install Python 3.11
2. Install VS Code + Python extension
3. Get Groq API key (free) + Gemini API key (free)
4. Run: `pip install streamlit chromadb sentence-transformers requests beautifulsoup4 python-dotenv numpy PyMuPDF`
5. Run `scrape.py` — collect all BRACU pages
6. Run `build_db.py` — generate chunks.json
7. Run `app.py` locally — test with 20 queries
8. Push to GitHub → Deploy to Streamlit Cloud
9. Share the live link
