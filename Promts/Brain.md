# Brain.md — Persistent Context

> Read this before every response. Update after every significant decision.

---

## HARD RULES (Never Violate)

| # | Rule | Why |
|---|------|-----|
| 1 | **No local LLM inference.** Never suggest running any model locally. | i5-6200U + 8GB RAM + no GPU = crash. |
| 2 | **Guardrails must be TWO-layer.** Keyword check alone is insufficient. | "Tell me about admission at Harvard" passes keyword check but must be rejected. |
| 3 | **Vector DB never committed to GitHub.** Use chunks.json (<5MB) instead. | ChromaDB exceeds GitHub 100MB limit with enough data. |
| 4 | **Always have an API fallback.** Groq primary, Gemini backup. | If one API fails/goes paid, the other must work. |
| 5 | **Never suggest paid services.** All tools must be free/open-source. | Student has zero budget. |
| 6 | **No Firecrawl dependency.** Use cloudscraper + BeautifulSoup for scraping. | Firecrawl has credit limits. BRACU website uses Cloudflare — plain requests gets blocked. |
| 7 | **No separate frontend/backend.** Use Streamlit (mono-repo). | FastAPI + separate frontend adds complexity for zero benefit in a prototype. |

---

## MISTAKE LOG (Read Before Answering — Never Repeat)

| # | Mistake | When | Fix Applied |
|---|---------|------|-------------|
| 1 | Suggested Phi-3-mini GGUF local LLM on i5/8GB laptop. Would crash. | Plan.md | Discarded. Replaced with Groq + Gemini cloud APIs. |
| 2 | Suggested FastAPI + separate frontend (unnecessary complexity). | Plan.md | Streamlit single-file approach adopted instead. |
| 3 | FAILED TO CONSIDER: keyword-only guardrail misses "Harvard admission" queries. | Not in my plan, but caught in Kimi's. | Two-layer guardrail: (1) other-uni detection + (2) similarity threshold. |
| 4 | FAILED TO CONSIDER: ChromaDB in GitHub hits 100MB file limit. | Not in my plan, but caught in Kimi's. | Store chunks.json only. Rebuild ChromaDB on deploy. |
| 5 | FAILED TO CONSIDER: PDF documents exist (handbook, forms). | Both plans initially. | PyMuPDF added for PDF extraction. |
| 6 | FAILED TO CONSIDER: BRACU website uses Cloudflare. Plain requests gets 403. | scrape.py | Switched to cloudscraper. |
| 7 | FAILED TO CONSIDER: Groq model llama3-8b-8192 decommissioned. | chat_engine.py | Switched to llama-3.1-8b-instant. |
| 8 | FAILED TO CONSIDER: ChromaDB returns embeddings as numpy arrays. | guardrails.py, chat_engine.py | Fixed truth checks to use len() instead of truthiness. |
| 9 | FAILED TO CONSIDER: Context from chunks exceeds Groq token limit (6000 TPM). | chat_engine.py | Truncated context to 4000 chars, reduced top_k to 3. |

**Rule:** If a mistake is logged here, never make the same suggestion again.

---

## DECISION LOG (Why Things Are The Way They Are)

| Decision | Chosen Option | Rejected Options | Rationale |
|----------|--------------|-----------------|-----------|
| LLM source | Groq API + Gemini fallback | Local model, HuggingFace Inference API | Laptop can't run models; Groq is fastest free API |
| UI framework | Streamlit | Gradio, HTML/CSS/JS, React | Streamlit = one Python file, auto-deploy to cloud, built-in chat components |
| Scraping tool | cloudscraper + BeautifulSoup | Firecrawl, Scrapy, Selenium, plain requests | Free, no credit limit, no browser needed. cloudscraper bypasses Cloudflare. |
| PDF parser | PyMuPDF (fitz) | pdfplumber, PDFMiner | Fastest, simplest API, single dependency |
| Vector store | ChromaDB (persistent, disk-based) | FAISS, Pinecone, Weaviate | FAISS has no built-in persistence; Pinecone/Weaviate are paid |
| Embedding model | all-MiniLM-L6-v2 | all-mpnet-base-v2, text-embedding-ada | Best quality/speed balance for CPU. 384-dim, ~400MB RAM |
| Deployment | Streamlit Cloud | Hugging Face Spaces, Render, Vercel | Free, 2-click deploy from GitHub, designed for Streamlit apps |
| Git strategy | chunks.json in repo, ChromaDB gitignored | ChromaDB in repo, Git LFS | ChromaDB exceeds 100MB; Git LFS is unnecessary friction |

---

## COMMON QUESTIONS & ANSWERS (Cache — So I Don't Recompute)

> If user asks these, answer directly from here — no need to search/think.

**Q: What's the first thing I should do?**
A: Install Python 3.11 and get Groq API key.

**Q: Can my laptop run AI models?**
A: No. i5-6200U + 8GB RAM + Intel HD 520 = no local LLM. Use cloud APIs.

**Q: What's the project folder?**
A: `D:\BURU`.

**Q: Is there a budget?**
A: Zero. Everything must be free/open-source.

**Q: Should I use Firecrawl?**
A: No. Use cloudscraper + BeautifulSoup (free, unlimited, bypasses Cloudflare).

**Q: Should I commit the vector database to GitHub?**
A: No. Commit chunks.json only. ChromaDB is rebuilt on deploy.

**Q: What if Groq stops being free?**
A: Gemini API is the fallback. Both are free tier as of 2026.

**Q: What if the chatbot needs to handle 100+ users?**
A: Streamlit Cloud + Groq API scale fine for demo. If university invests, migrate to paid infrastructure.

**Q: What's the difference between Plan.md, KIMI_2.6.md, and Final_Plan.md?**
A: Plan.md was my first (flawed — suggested local LLM). KIMI_2.6.md was Kimi's (better but weak guardrails). Final_Plan.md merges both, fixes all cons.

**Q: How do I run the chatbot locally?**
A: Two terminals needed:
   1. Backend: `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`
   2. Frontend: `cd frontend && npm run dev`
   Then open http://localhost:3000.

**Q: How do I share the chatbot with testers?**
A: Deploy to Streamlit Cloud → share the `.streamlit.app` URL.

---

## WHAT NOT TO SUGGEST (Rejected & Blacklisted)

- Local LLMs (llama.cpp, Ollama, LM Studio, GPT4All, Phi-3, Mistral GGUF)
- Paid APIs (OpenAI, Claude, Cohere, paid Pinecone)
- Firecrawl (credit limit; use BS4)
- FastAPI + separate frontend (overkill for prototype)
- Docker / containers (overhead, not needed)
- GPU or cloud compute (laptop has no GPU; free tiers don't offer GPU)
- Git LFS (unnecessary — use chunks.json approach)
- Any database that requires a server (PostgreSQL, Redis)
- Any service that requires a credit card

---

## BRACU FACTS (For Quick Reference)

| Fact | Detail |
|------|--------|
| Full name | BRAC University |
| Website | https://www.bracu.ac.bd |
| Location | 66 Mohakhali, Dhaka, Bangladesh |
| Founded | 2001 |
| Key departments | CSE, BBS (Business), Law, Architecture, Pharmacy, ESS, MNS |
| Academic calendar | 3 semesters: Spring (Jan–Apr), Summer (May–Aug), Fall (Sep–Dec) |

---

## CURRENT STATE

| Aspect | Status |
|--------|--------|
| Planning | ✅ Complete (Final_Plan.md active) |
| Python installed | ✅ 3.10.8 |
| Node.js installed | ✅ v22.18.0 |
| Dependencies installed | ✅ chromadb, sentence-transformers, cloudscraper, fastapi, next.js, etc. |
| Groq API key obtained | ✅ Added to .env |
| Backend code | ✅ FastAPI server (backend/main.py) + chat_engine.py, guardrails.py, system_prompt.py |
| Frontend code | ✅ Next.js app (frontend/) with chat UI + API proxy |
| Data collected | ✅ 10 BRACU web pages scraped (scripts/scrape.py) |
| Chunks built | ✅ 153 chunks (data/processed/chunks.json) |
| Vector DB built | ✅ Builds on first backend startup |
| Bug fixes applied | ✅ guardrails.py numpy truth check, Groq model updated to llama-3.1-8b-instant, context truncated to 4000 chars, top_k reduced to 3 |
| Full stack tested | ✅ Backend (port 8000) + Frontend (port 3000) both running |
| App deployed | ❌ Not yet |
| Documentation | ✅ Documentation.md (updated for two-service architecture) |
| User's last confirmed step | Full stack running locally, Next.js + FastAPI architecture |

---

## USER PREFERENCES

- Tone: Direct, concise, no emojis unless asked
- Wants to use VS Code + AI agent (Continue/Copilot) for code
- Will prototype first, then pitch to university authority for funding
- Wants a shareable web link for testing

---

## SELF-CHECK (Ask Before Every Answer)

- [ ] Have I checked the Mistake Log to avoid repeating errors?
- [ ] Is my suggestion within the hardware constraints (i5, 8GB, no GPU)?
- [ ] Is my suggestion free?
- [ ] Does this violate any Hard Rule?
- [ ] Is there a cached answer in Common Questions I should use instead?
- [ ] Is this in the "What Not To Suggest" blacklist?
- [ ] Have I read the current state so I don't suggest something already done?

---

## LOG

| Date | Event |
|------|-------|
| — | Planning phase. Final_Plan.md created. |
| — | Brain.md created and expanded with mistake log, decision log, blacklist, cache. |
| 2026-06-19 | All dependencies installed (pip install). .env created with Groq key. |
| 2026-06-19 | Project structure created: app.py, chat_engine.py, guardrails.py, system_prompt.py. |
| 2026-06-19 | scripts/scrape.py written. Discovered BRACU uses Cloudflare → switched to cloudscraper. |
| 2026-06-19 | 10 BRACU pages scraped → 153 chunks built. |
| 2026-06-19 | Documentation.md created in Promts/. Brain.md updated. |
| 2026-06-19 | Abandoned Streamlit. Built FastAPI backend (backend/main.py) + Next.js frontend (frontend/). |
| 2026-06-19 | Fixed ChromaDB numpy array bug in guardrails.py and chat_engine.py. |
| 2026-06-19 | Updated Groq model from decommissioned llama3-8b-8192 to llama-3.1-8b-instant. |
| 2026-06-19 | Fixed context overflow: truncated to 4000 chars, reduced top_k from 5 to 3. |
| 2026-06-19 | Full stack tested: Backend (8000) + Frontend (3000) working. |
