I'll read your uploaded file carefully and then build you a realistic, zero-budget plan tailored to your situation.
I've read your file carefully and explored BRAC University's website. Your laptop (i5-6200U, 8GB RAM, no GPU) is a significant constraint — you **cannot** run large AI models locally. But you absolutely can build a working prototype using free cloud APIs and lightweight tools. Here's your realistic, zero-budget, step-by-step plan.

---

# BRAC University AI Advisor — Zero-Budget Prototype Plan
## Tailored for your laptop + free resources only

---

## Your Hard Constraints (I will not suggest anything beyond these)

| Spec | Limitation | What it means |
|------|-----------|-------------|
| i5-6200U (2 cores, 2.3GHz) | No local LLM running | Models like Llama 3 need 16GB+ RAM and a GPU. Your laptop will crash. |
| 8GB RAM | Very tight | You can run Python, VS Code, and a browser. Not much else simultaneously. |
| Intel HD 520 (128MB) | No GPU acceleration | Cannot run any model inference locally. |
| 238GB SSD | Adequate | Enough for Python, code, and small datasets. |
| Windows 10 | Environment | Use WSL2 or native Python. |

**The only viable path:** Use **free cloud API tiers** for the AI brain, build everything else locally on your laptop.

---

## Free Resources You Will Use

| Resource | Free Tier | What You Get |
|----------|-----------|-------------|
| **Groq API** | Free tier available | Blazing fast inference with Llama 3, Mixtral, Gemma — no credit card needed for initial usage |
| **Google Gemini API** | Free tier (1,500 requests/day) | Powerful model, generous free limits |
| **Hugging Face Inference API** | Free tier | Access to open-source models |
| **ChromaDB** | Open source, runs locally | Your vector database for BRACU documents |
| **Python + VS Code** | Free | Your development environment |
| **GitHub** | Free | Host your code repository |
| **Streamlit** | Free, open source | Build the chat UI in Python (easiest for beginners) |
| **Firecrawl.dev** | Free tier (500 credits) | Scrape BRACU website pages into clean text |

---

## Phase 1: Environment Setup (Day 1–2)

### 1.1 Install Python & Tools
```bash
# Install Python 3.11 from python.org
# During install: CHECK "Add Python to PATH"

# Open Command Prompt (cmd) and run:
python -m pip install --upgrade pip

# Install all packages you'll need
pip install streamlit chromadb sentence-transformers requests beautifulsoup4 pdfplumber python-dotenv
```

### 1.2 Set Up VS Code
1. Install VS Code from [code.visualstudio.com](https://code.visualstudio.com)
2. Install extensions: **Python**, **Pylance**
3. Create a project folder: `C:\bracu-chatbot`
4. Open it in VS Code

### 1.3 Get Free API Keys
| API | Where to Get | Free Limit |
|-----|-------------|-----------|
| **Groq** | [console.groq.com](https://console.groq.com) | Sign up, get API key. Generous free tier. |
| **Google Gemini** | [aistudio.google.com](https://aistudio.google.com) | 1,500 requests/day |
| **Firecrawl** | [firecrawl.dev](https://firecrawl.dev) | 500 credits (enough for BRACU site) |

Store keys in a `.env` file in your project folder:
```
GROQ_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
FIRECRAWL_API_KEY=your_key_here
```

---

## Phase 2: Build the Knowledge Base (Day 3–7)

This is the most important part. The AI is only as good as the BRACU information you feed it.

### 2.1 Identify & Collect BRACU Sources

From the BRACU website, these are your priority pages to scrape:

| Category | URLs to Scrape |
|----------|---------------|
| **Academics** | `/academics`, `/academic-dates`, Schools & Departments pages, Programs in Detail |
| **Admissions** | `/admissions`, `/undergraduate-admission`, `/scholarships-and-financial-aid`, `/tuition-and-fees`, FAQs |
| **Student Life** | `/student-life`, `/residential-semester`, `/medical-center`, `/student-accommodation`, `/dress-code`, `/club-community` |
| **Services** | `/office-of-academic-advising`, `/office-of-career-services`, `/counseling-and-wellness-centre`, `/library`, `/transport` |
| **Policies** | `/policies-and-procedures`, Student Handbook (PDF if available) |
| **Announcements** | Recent announcements, class schedules, registration info |

### 2.2 Scrape the Content

Use **Firecrawl** (free tier) — it converts web pages into clean, LLM-ready text. Much better than basic scraping.

```python
# save as: scrape_bracu.py
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# List of BRACU pages to scrape
urls_to_scrape = [
    "https://www.bracu.ac.bd/academics",
    "https://www.bracu.ac.bd/academic-dates",
    "https://www.bracu.ac.bd/admissions",
    "https://www.bracu.ac.bd/scholarships-and-financial-aid",
    "https://www.bracu.ac.bd/tuition-and-fees",
    "https://www.bracu.ac.bd/student-life",
    "https://www.bracu.ac.bd/residential-semester",
    "https://www.bracu.ac.bd/student-accommodation",
    "https://www.bracu.ac.bd/policies-and-procedures",
    "https://www.bracu.ac.bd/office-of-academic-advising",
    "https://www.bracu.ac.bd/library",
    "https://www.bracu.ac.bd/transport",
]

def scrape_page(url):
    """Use Firecrawl to scrape a single page"""
    response = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}"},
        json={"url": url, "formats": ["markdown"]}
    )
    data = response.json()
    if data.get("success"):
        return data["data"]["markdown"]
    return None

# Scrape all pages
all_content = {}
for url in urls_to_scrape:
    print(f"Scraping: {url}")
    content = scrape_page(url)
    if content:
        all_content[url] = content
        print(f"  ✓ Got {len(content)} characters")
    else:
        print(f"  ✗ Failed")

# Save to file
with open("bracu_knowledge.json", "w", encoding="utf-8") as f:
    json.dump(all_content, f, ensure_ascii=False, indent=2)

print(f"\nTotal pages scraped: {len(all_content)}")
```

### 2.3 Chunk the Documents

LLMs have limited context. You must break long pages into small, meaningful chunks.

```python
# save as: chunk_documents.py
import json
import re

with open("bracu_knowledge.json", "r", encoding="utf-8") as f:
    data = json.load(f)

chunks = []

def chunk_text(text, source_url, chunk_size=800, overlap=100):
    """Split text into overlapping chunks"""
    # Clean the text
    text = re.sub(r'\n+', '\n', text).strip()
    
    sentences = re.split(r'(?<<=[.!?])\s+', text)
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        if current_length + sentence_length > chunk_size and current_chunk:
            chunks.append({
                "text": " ".join(current_chunk),
                "source": source_url,
                "chunk_id": len(chunks)
            })
            # Keep overlap
            overlap_text = " ".join(current_chunk[-2:]) if len(current_chunk) >= 2 else current_chunk[-1]
            current_chunk = [overlap_text, sentence] if len(current_chunk) >= 2 else [sentence]
            current_length = len(overlap_text) + sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length
    
    if current_chunk:
        chunks.append({
            "text": " ".join(current_chunk),
            "source": source_url,
            "chunk_id": len(chunks)
        })

# Process all pages
for url, content in data.items():
    chunk_text(content, url)

print(f"Total chunks created: {len(chunks)}")

with open("bracu_chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)
```

### 2.4 Build the Vector Database (Local, Free)

This runs entirely on your laptop. It stores chunks as mathematical vectors so the AI can find relevant information quickly.

```python
# save as: build_vector_db.py
import json
import chromadb
from sentence_transformers import SentenceTransformer

# Load chunks
with open("bracu_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

# Load a lightweight embedding model (runs on CPU, ~400MB)
# This is the heaviest thing on your laptop but it will work
print("Loading embedding model... (this takes 1-2 minutes)")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Create local ChromaDB
client = chromadb.PersistentClient(path="./bracu_chroma_db")

# Create collection
collection = client.get_or_create_collection(
    name="bracu_knowledge",
    metadata={"description": "BRAC University knowledge base"}
)

# Add chunks in batches (to manage RAM)
batch_size = 50
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    texts = [c["text"] for c in batch]
    ids = [f"chunk_{c['chunk_id']}" for c in batch]
    metadatas = [{"source": c["source"]} for c in batch]
    
    # Generate embeddings
    embeddings = model.encode(texts).tolist()
    
    # Add to database
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )
    print(f"Added batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")

print(f"\n✓ Vector database built with {len(chunks)} chunks")
print("Database saved to: ./bracu_chroma_db")
```

**Run this in VS Code terminal.** It will take 5–10 minutes on your laptop. Your RAM will be stressed — close Chrome tabs while it runs.

---

## Phase 3: Build the AI Brain + Guardrails (Day 8–12)

### 3.1 The Core System Prompt

This is what makes your AI "BRACU-only." It is the most critical piece of code.

```python
# save as: system_prompt.py

BRACU_SYSTEM_PROMPT = """You are BRACU Advisor, the official AI assistant for BRAC University students, prospective students, and their families.

YOUR STRICT RULES:
1. You may ONLY answer questions related to BRAC University. This includes:
   - Academic programs, courses, and degree requirements
   - Admissions, application processes, and deadlines
   - Scholarships, financial aid, tuition, and fees
   - Student life: housing, dining, clubs, campus facilities
   - Academic advising, registration, and class schedules
   - University policies, procedures, and codes of conduct
   - Career services, internships, and alumni relations
   - Library, IT, medical, counseling, and transport services
   - Campus locations, events, and announcements

2. You MUST REFUSE off-topic questions. If asked about:
   - Solving math problems, coding, homework help
   - General knowledge unrelated to BRACU
   - Other universities or topics
   - Personal advice beyond university scope
   → Respond: "I can only help with questions related to BRAC University. I'd be happy to assist you with admissions, academics, scholarships, student life, or any BRACU-related topic!"

3. If you don't know the answer or the information isn't in the provided context, say so honestly. Never make up facts, deadlines, or policies.

4. Always cite your sources like: [Source: bracu.ac.bd/academics]

5. Use a friendly, helpful, professional tone. Be concise but thorough.

6. For urgent or sensitive matters (mental health crises, legal issues, severe academic penalties), provide the relevant BRACU office contact and strongly recommend speaking to a human advisor immediately.

CONTEXT: The following information is from BRAC University's official website and documents. Use ONLY this information to answer:
{context}
"""
```

### 3.2 The Query + Response Engine

```python
# save as: chat_engine.py
import os
import chromadb
from sentence_transformers import SentenceTransformer
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Load vector DB and model (load once, reuse)
client = chromadb.PersistentClient(path="./bracu_chroma_db")
collection = client.get_collection("bracu_knowledge")
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_relevant_chunks(query, top_k=5):
    """Find the most relevant BRACU documents for the query"""
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas"]
    )
    return results

def check_if_bracu_related(query):
    """Simple guardrail: check if query is related to BRACU"""
    bracu_keywords = [
        "brac", "bracu", "university", "admission", "scholarship", "tuition", 
        "course", "class", "registration", "credit", "gpa", "department", 
        "program", "degree", "campus", "hostel", "dorm", "transport", 
        "library", "exam", "final", "midterm", "assignment", "faculty", 
        "professor", "advisor", "counseling", "medical", "career", "internship",
        "club", "event", "freshman", "senior", "graduate", "undergraduate",
        "phd", "masters", "bachelor", "enrollment", "waiver", "financial aid",
        "student life", "accommodation", "residential", "semester", "summer",
        "fall", "spring", "withdraw", "drop", "add", "prerequisite"
    ]
    query_lower = query.lower()
    return any(kw in query_lower for kw in bracu_keywords)

def generate_response(user_query):
    """Main function: process query and generate response"""
    
    # Guardrail 1: Check if BRACU-related
    if not check_if_bracu_related(user_query):
        return {
            "answer": "I can only help with questions related to BRAC University. I'd be happy to assist you with admissions, academics, scholarships, student life, or any BRACU-related topic! What would you like to know about BRACU?",
            "sources": []
        }
    
    # Retrieve relevant chunks
    results = get_relevant_chunks(user_query)
    
    if not results["documents"][0]:
        return {
            "answer": "I don't have specific information about that in my current knowledge base. I recommend contacting the relevant BRACU office directly or checking the official website at bracu.ac.bd. Would you like help with something else about BRACU?",
            "sources": []
        }
    
    # Build context from retrieved chunks
    context_parts = []
    sources = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        context_parts.append(doc)
        sources.append(meta["source"])
    
    context = "\n\n---\n\n".join(context_parts)
    
    # Build the full prompt
    from system_prompt import BRACU_SYSTEM_PROMPT
    system_msg = BRACU_SYSTEM_PROMPT.format(context=context)
    
    # Call Groq API (free tier, fast)
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama3-8b-8192",  # Fast, good, free tier available
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_query}
            ],
            "temperature": 0.3,  # Lower = more factual, less creative
            "max_tokens": 1024
        }
    )
    
    data = response.json()
    answer = data["choices"][0]["message"]["content"]
    
    return {
        "answer": answer,
        "sources": list(set(sources))  # Remove duplicates
    }

# Test it
if __name__ == "__main__":
    test_queries = [
        "What scholarships are available at BRACU?",
        "How do I register for summer 2026 classes?",
        "Solve this math problem: 2x + 5 = 15",  # Should refuse
        "Write Python code to sort a list",  # Should refuse
        "What is the tuition fee for CSE?",
    ]
    
    for q in test_queries:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        result = generate_response(q)
        print(f"A: {result['answer']}")
        print(f"Sources: {result['sources']}")
```

---

## Phase 4: Build the Chat Interface (Day 13–15)

### 4.1 Streamlit UI (Easiest for Prototypes)

```python
# save as: app.py
import streamlit as st
from chat_engine import generate_response

st.set_page_config(
    page_title="BRACU Advisor",
    page_icon="🎓",
    layout="centered"
)

# BRACU branding colors
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stChatMessage { border-radius: 10px; }
    .stChatMessage.user { background-color: #e3f2fd; }
    .stChatMessage.assistant { background-color: #fff3e0; }
</style>
""", unsafe_allow_html=True)

st.title("🎓 BRACU Advisor")
st.caption("Your AI assistant for BRAC University — Ask about admissions, academics, scholarships, student life, and more!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            st.caption(f"Sources: {', '.join(message['sources'])}")

# User input
if prompt := st.chat_input("Ask me anything about BRAC University..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = generate_response(prompt)
            answer = result["answer"]
            sources = result["sources"]
        
        st.markdown(answer)
        if sources:
            st.caption(f"Sources: {', '.join(sources)}")
    
    # Add assistant message to history
    st.session_state.messages.append({
        "role": "assistant", 
        "content": answer,
        "sources": sources
    })

# Sidebar info
with st.sidebar:
    st.header("About BRACU Advisor")
    st.write("""
    This AI assistant helps you find information about BRAC University quickly.
    
    **I can help with:**
    - 📚 Academic programs & courses
    - 📝 Admissions & applications
    - 💰 Scholarships & financial aid
    - 🏠 Student life & housing
    - 📅 Class schedules & registration
    - 🎯 Career services & internships
    
    **I cannot help with:**
    - Math problems or homework
    - Coding or technical tasks
    - General knowledge questions
    - Topics unrelated to BRACU
    """)
    
    st.divider()
    st.caption("Built by a BRACU student | Powered by AI")
    st.caption("⚠️ Always verify critical information with official BRACU offices.")
```

### 4.2 Run the App

```bash
# In VS Code terminal:
streamlit run app.py
```

This opens a browser tab with your chatbot. You can test it immediately.

---

## Phase 5: Testing & Refinement (Day 16–20)

### 5.1 Test Questions to Try

| Category | Test Query | Expected Behavior |
|----------|-----------|-----------------|
| **Valid** | "What are the admission requirements for CSE?" | Answers with info + cites source |
| **Valid** | "How much is the tuition fee?" | Answers with fee info |
| **Valid** | "Tell me about the residential semester" | Answers with housing info |
| **Invalid** | "Solve 2x + 5 = 15" | Refuses politely |
| **Invalid** | "Write Python code for bubble sort" | Refuses politely |
| **Invalid** | "What is the capital of France?" | Refuses politely |
| **Edge** | "I feel stressed about exams" | Provides counseling center info + human referral |
| **Unknown** | "What is the WiFi password for the library?" | Says "I don't have that info" + suggests IT help desk |

### 5.2 Improve the Guardrail

The simple keyword check is a starting point. As you test, add more BRACU keywords and patterns. Later, you can use a lightweight classifier model, but the keyword approach is sufficient for a prototype.

### 5.3 Add More Documents

As you find gaps in answers, scrape more pages and re-run `build_vector_db.py`.

---

## Phase 6: Polish for Demo (Day 21–25)

### 6.1 Add These Features for a Strong Demo

| Feature | Why It Impresses | How |
|---------|-----------------|-----|
| **Citations** | Shows accuracy | Already included — every answer shows source URL |
| **"I don't know" honesty** | Builds trust | Already included — never hallucinates |
| **Off-topic refusal** | Shows control | Already included — strict guardrail |
| **Suggested questions** | Helps users start | Add buttons: "Scholarships", "Admission", "Housing" |
| **Contact info fallback** | Shows completeness | When answer is incomplete, provide office email/phone |

### 6.2 Add Suggested Questions to UI

```python
# Add this to app.py, before the chat_input:

st.write("**Quick questions:**")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("💰 Scholarships"):
        prompt = "What scholarships are available at BRAC University?"
with col2:
    if st.button("📝 Admission"):
        prompt = "What are the undergraduate admission requirements?"
with col3:
    if st.button("🏠 Housing"):
        prompt = "Tell me about student accommodation at BRACU"
with col4:
    if st.button("📅 Academic Calendar"):
        prompt = "What are the important academic dates for 2026?"
```

### 6.3 Record a Demo Video

Use OBS (free) to record yourself:
1. Opening the chatbot
2. Asking 3–4 BRACU questions
3. Showing the AI refuses a math problem
4. Highlighting the source citations

---

## Phase 7: Prepare the Pitch (Day 26–30)

### 7.1 What Authorities Want to See

| Concern | How Your Prototype Addresses It |
|---------|-------------------------------|
| **Accuracy** | Every answer cites official BRACU sources |
| **Control** | Strictly limited to BRACU topics — no misuse |
| **Cost** | Built entirely on free/open-source tools |
| **Scalability** | Cloud API can handle thousands of students |
| **Student need** | Solves real pain point: information access |
| **Data privacy** | No student personal data stored in prototype |

### 7.2 Your Pitch Deck (5 Slides)

1. **Problem:** Students waste hours traveling to campus, waiting in lines, searching fragmented websites for basic info.
2. **Solution:** BRACU Advisor — an AI that instantly answers any university question, 24/7, with verified information.
3. **Demo:** Show the live chatbot answering real questions, refusing off-topic requests, citing sources.
4. **Technical:** Built with free tools, runs on any device, scalable to full deployment.
5. **Ask:** Funding for full knowledge base expansion, integration with student portal, dedicated hosting, and human escalation system.

### 7.3 Future Roadmap (If Funded)

| Phase | Investment | What It Adds |
|-------|-----------|-------------|
| **V1.5** | ~$500/month | Full website scrape, 10,000+ chunks, better guardrails, SMS/ WhatsApp integration |
| **V2.0** | ~$2,000/month | Student portal integration (personalized: "What courses do I need?"), human handoff, analytics dashboard |
| **V3.0** | Custom | Multilingual (Bangla + English), voice interface, mobile app, proactive notifications |

---

## Your Complete File Structure

```
bracu-chatbot/
├── .env                          # API keys (never commit this!)
├── .gitignore                    # Ignore .env and database files
├── app.py                        # Streamlit chat UI
├── chat_engine.py                # Core AI logic + guardrails
├── system_prompt.py              # BRACU-only system prompt
├── scrape_bracu.py               # Scrape BRACU website
├── chunk_documents.py            # Split into chunks
├── build_vector_db.py            # Create vector database
├── bracu_knowledge.json          # Raw scraped content
├── bracu_chunks.json             # Processed chunks
├── bracu_chroma_db/              # Local vector database (auto-created)
└── README.md                     # Project documentation
```

---

## Critical Tips for Your Laptop

| Tip | Why |
|-----|-----|
| **Close Chrome while running `build_vector_db.py`** | The embedding model needs 400MB+ RAM. With 8GB total and Windows overhead, you need every MB. |
| **Run scripts one at a time** | Don't run scrape + chunk + build simultaneously. |
| **Use Task Manager** | Check RAM usage. If it hits 90%, close other apps. |
| **If it crashes during embedding** | Reduce `batch_size` in `build_vector_db.py` from 50 to 20. |
| **Use VS Code terminal, not CMD** | Easier to see errors and manage. |

---

## What to Do Right Now (Next 2 Hours)

1. **Install Python 3.11** from python.org
2. **Install VS Code** and the Python extension
3. **Create the project folder** `C:\bracu-chatbot`
4. **Get your free Groq API key** at console.groq.com
5. **Get your free Firecrawl API key** at firecrawl.dev
6. **Create `.env` file** with your keys
7. **Run `pip install`** the packages
8. **Create `scrape_bracu.py`** and run it
9. **Create `chunk_documents.py`** and run it
10. **Create `build_vector_db.py`** and run it (close Chrome first!)

If you get stuck on any step, tell me the exact error message and I'll help you fix it. Once you have the vector database built, the rest is much easier.

---

## The Hosting Challenge

Your laptop cannot run 24/7 as a server. You need a free cloud platform to host the chatbot. Here are your options:

| Platform | Free Tier | Pros | Cons |
|----------|-----------|------|------|
| **Streamlit Cloud** | Unlimited public apps | Easiest — deploy from GitHub in 2 clicks | App sleeps after inactivity (wakes in ~30s) |
| **Hugging Face Spaces** | Free CPU tier | Good for AI demos, persistent | Slower cold start, limited RAM |
| **Render** | Free web services | Sleeps after 15 min inactivity | Wakes in ~30s |
| **Vercel** | Free for frontend | Very fast, great for static sites | Cannot run Python backend easily |
| **GitHub Pages** | Free | Fast, reliable | Static only — no Python backend |

**Best choice for you:** **Streamlit Cloud** — it's literally built for this. You push your code to GitHub, connect to Streamlit Cloud, and get a live URL in minutes.

---

## Updated Architecture: GitHub + Streamlit Cloud

```
Your Laptop (Development)
    ↓
GitHub Repository (Code + Vector DB)
    ↓
Streamlit Cloud (Free Hosting)
    ↓
Groq API (Free AI brain — hosted by Groq, not your laptop)
```

**Key insight:** The heavy AI work (LLM inference) happens on Groq's servers. Your hosted app only needs to:
- Run the lightweight Streamlit UI
- Query the local ChromaDB (which you'll also host)
- Call the Groq API

---

## Updated Plan: Add Hosting Phase

Here's what changes from the original plan:

### Phase 1–5: Same as before (build locally on your laptop)

You still develop and test everything on your laptop first.

### NEW Phase 6: Prepare for Cloud Hosting (Day 21–23)

#### Step 6.1: Create `requirements.txt`

This tells Streamlit Cloud what Python packages to install.

```txt
# requirements.txt
streamlit==1.40.0
chromadb==0.5.0
sentence-transformers==3.0.0
requests==2.32.0
python-dotenv==1.0.0
```

#### Step 6.2: Update `app.py` for Cloud

Two important changes:
1. **Remove `.env` dependency** — Streamlit Cloud uses secrets instead
2. **Ensure ChromaDB path works in cloud**

```python
# app.py — UPDATED for cloud hosting
import streamlit as st
import os
import chromadb
from sentence_transformers import SentenceTransformer
import requests

# ========== SECRETS CONFIGURATION ==========
# For local testing: use .env
# For Streamlit Cloud: use st.secrets
try:
    # Streamlit Cloud secrets
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    # Local development
    from dotenv import load_dotenv
    load_dotenv()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ========== LOAD VECTOR DATABASE ==========
# The database must be in your GitHub repo
@st.cache_resource  # Cache so it only loads once
def load_vector_db():
    client = chromadb.PersistentClient(path="./bracu_chroma_db")
    collection = client.get_collection("bracu_knowledge")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return collection, model

collection, model = load_vector_db()

# ========== SYSTEM PROMPT ==========
BRACU_SYSTEM_PROMPT = """You are BRACU Advisor, the official AI assistant for BRAC University students...

YOUR STRICT RULES:
1. You may ONLY answer questions related to BRAC University...
2. You MUST REFUSE off-topic questions...
3. If you don't know the answer, say so honestly...
4. Always cite your sources...
5. Use a friendly, helpful, professional tone...

CONTEXT:
{context}
"""

# ========== CHAT ENGINE FUNCTIONS ==========
def get_relevant_chunks(query, top_k=5):
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas"]
    )
    return results

def check_if_bracu_related(query):
    bracu_keywords = [
        "brac", "bracu", "university", "admission", "scholarship", "tuition", 
        "course", "class", "registration", "credit", "gpa", "department", 
        "program", "degree", "campus", "hostel", "dorm", "transport", 
        "library", "exam", "final", "midterm", "assignment", "faculty", 
        "professor", "advisor", "counseling", "medical", "career", "internship",
        "club", "event", "freshman", "senior", "graduate", "undergraduate",
        "phd", "masters", "bachelor", "enrollment", "waiver", "financial aid",
        "student life", "accommodation", "residential", "semester", "summer",
        "fall", "spring", "withdraw", "drop", "add", "prerequisite"
    ]
    query_lower = query.lower()
    return any(kw in query_lower for kw in bracu_keywords)

def generate_response(user_query):
    # Guardrail
    if not check_if_bracu_related(user_query):
        return {
            "answer": "I can only help with questions related to BRAC University. I'd be happy to assist you with admissions, academics, scholarships, student life, or any BRACU-related topic!",
            "sources": []
        }
    
    # Retrieve chunks
    results = get_relevant_chunks(user_query)
    
    if not results["documents"][0]:
        return {
            "answer": "I don't have specific information about that in my current knowledge base. I recommend contacting the relevant BRACU office directly or checking bracu.ac.bd. Would you like help with something else about BRACU?",
            "sources": []
        }
    
    # Build context
    context_parts = []
    sources = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        context_parts.append(doc)
        sources.append(meta["source"])
    
    context = "\n\n---\n\n".join(context_parts)
    system_msg = BRACU_SYSTEM_PROMPT.format(context=context)
    
    # Call Groq API
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_query}
            ],
            "temperature": 0.3,
            "max_tokens": 1024
        }
    )
    
    data = response.json()
    answer = data["choices"][0]["message"]["content"]
    
    return {
        "answer": answer,
        "sources": list(set(sources))
    }

# ========== STREAMLIT UI ==========
st.set_page_config(
    page_title="BRACU Advisor",
    page_icon="🎓",
    layout="centered"
)

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
</style>
""", unsafe_allow_html=True)

st.title("🎓 BRACU Advisor")
st.caption("Your AI assistant for BRAC University — Ask about admissions, academics, scholarships, student life, and more!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            st.caption(f"Sources: {', '.join(message['sources'])}")

# Quick question buttons
st.write("**Quick questions:**")
col1, col2, col3, col4 = st.columns(4)
quick_question = None
with col1:
    if st.button("💰 Scholarships"):
        quick_question = "What scholarships are available at BRAC University?"
with col2:
    if st.button("📝 Admission"):
        quick_question = "What are the undergraduate admission requirements?"
with col3:
    if st.button("🏠 Housing"):
        quick_question = "Tell me about student accommodation at BRACU"
with col4:
    if st.button("📅 Calendar"):
        quick_question = "What are the important academic dates?"

# Handle quick question or user input
if quick_question:
    prompt = quick_question
elif prompt := st.chat_input("Ask me anything about BRAC University..."):
    pass  # prompt already set
else:
    prompt = None

if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = generate_response(prompt)
            answer = result["answer"]
            sources = result["sources"]
        
        st.markdown(answer)
        if sources:
            st.caption(f"Sources: {', '.join(sources)}")
    
    # Add to history
    st.session_state.messages.append({
        "role": "assistant", 
        "content": answer,
        "sources": sources
    })

# Sidebar
with st.sidebar:
    st.header("About BRACU Advisor")
    st.write("""
    This AI assistant helps you find information about BRAC University quickly.
    
    **I can help with:**
    - 📚 Academic programs & courses
    - 📝 Admissions & applications
    - 💰 Scholarships & financial aid
    - 🏠 Student life & housing
    - 📅 Class schedules & registration
    - 🎯 Career services & internships
    
    **I cannot help with:**
    - Math problems or homework
    - Coding or technical tasks
    - General knowledge questions
    - Topics unrelated to BRACU
    """)
    
    st.divider()
    st.caption("Built by a BRACU student | Powered by AI")
    st.caption("⚠️ Always verify critical information with official BRACU offices.")
```

#### Step 6.3: Create `.gitignore`

```gitignore
# .gitignore
.env
__pycache__/
*.pyc
.pytest_cache/
.venv/
env/
venv/
```

**Important:** Do NOT put `.env` in GitHub. Use Streamlit secrets instead.

#### Step 6.4: Create `.streamlit/secrets.toml` (for local testing)

```toml
# .streamlit/secrets.toml
GROQ_API_KEY = "your_groq_api_key_here"
```

**Add to `.gitignore`:**
```gitignore
.streamlit/secrets.toml
```

---

### NEW Phase 7: Deploy to Streamlit Cloud (Day 24–25)

#### Step 7.1: Push to GitHub

```bash
# In your project folder (C:\bracu-chatbot)
# Initialize Git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial BRACU Advisor prototype"

# Create GitHub repo (go to github.com, create new repo, name it bracu-advisor)
# Then link and push:
git remote add origin https://github.com/YOUR_USERNAME/bracu-advisor.git
git branch -M main
git push -u origin main
```

#### Step 7.2: Add API Key to Streamlit Cloud Secrets

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select your `bracu-advisor` repo, branch `main`, file `app.py`
5. **Before deploying**, click **"Advanced settings"**
6. Add secrets:
   ```
   GROQ_API_KEY = "your_actual_groq_api_key"
   ```
7. Click **Deploy**

#### Step 7.3: Get Your Live URL

After deployment, Streamlit gives you a URL like:
```
https://bracu-advisor-xyz123.streamlit.app
```

**This is your demo link.** Share it with anyone. They can use the chatbot from any device.

---

### NEW Phase 8: Prepare for Demo (Day 26–30)

#### What to Show Authorities

1. **Open the link** on your phone or their computer
2. **Ask BRACU questions:**
   - "What scholarships are available?"
   - "How do I apply for admission?"
   - "Tell me about the residential semester"
3. **Show the refusal:**
   - "Solve this math problem" → Watch it politely refuse
   - "Write Python code" → Watch it refuse
4. **Show citations:** Every answer has a source URL
5. **Show quick buttons:** Pre-loaded common questions

---

## Critical: The Vector Database on GitHub

Your ChromaDB folder (`bracu_chroma_db/`) contains the vector embeddings. It's data, not code, but you need it for the app to work.

**Problem:** GitHub has a 100MB file limit. ChromaDB might exceed this if you have many documents.

**Solutions:**

| If your DB is small (<50MB) | If your DB is large (>50MB) |
|---------------------------|---------------------------|
| Just commit it to GitHub | Use Git LFS (free tier: 1GB) |
| | Or: Host ChromaDB separately (more complex) |

**For your prototype (scrape ~10–15 pages):** The DB will be under 50MB. Just commit it.

```bash
# Make sure bracu_chroma_db/ is NOT in .gitignore
# Check:
git add bracu_chroma_db/
git commit -m "Add vector database"
git push
```

---

## Updated Complete File Structure

```
bracu-chatbot/
├── .gitignore                    # Ignore .env, secrets, cache
├── .streamlit/
│   └── secrets.toml              # Local secrets (gitignored)
├── app.py                        # Main Streamlit app (cloud-ready)
├── requirements.txt              # Dependencies for cloud
├── README.md                     # Project description
├── bracu_chroma_db/              # Vector database (committed to GitHub)
│   ├── chroma.sqlite3
│   └── ... (other files)
├── scrape_bracu.py               # (local dev only, not needed in cloud)
├── chunk_documents.py            # (local dev only)
├── build_vector_db.py            # (local dev only)
├── bracu_knowledge.json          # (local dev only)
└── bracu_chunks.json             # (local dev only)
```

---

## Important Warnings

| Issue | Solution |
|-------|----------|
| **Streamlit Cloud sleeps after inactivity** | First visit after sleep takes ~30 seconds to wake up. Tell testers: "It might take a moment to start." |
| **Groq free tier has rate limits** | ~20 requests/minute. Enough for demo. If many testers use simultaneously, it might throttle. |
| **Don't expose your API key** | Never commit `.env` or `secrets.toml`. Always use Streamlit Cloud secrets. |
| **Keep your GitHub repo public** | Streamlit Cloud free tier requires public repos. That's fine for a prototype. |

---

## Your New Timeline

| Day | Task |
|-----|------|
| 1–2 | Setup Python, VS Code, get API keys |
| 3–7 | Scrape BRACU, build vector DB |
| 8–12 | Build chat engine + guardrails |
| 13–15 | Build Streamlit UI |
| 16–20 | Test, refine, add more documents |
| 21–23 | Prepare for cloud: `requirements.txt`, secrets, clean code |
| 24–25 | Push to GitHub, deploy to Streamlit Cloud |
| 26–30 | Polish UI, record demo, prepare pitch |

---

## Quick Start Checklist for Today

1. ✅ Install Python 3.11
2. ✅ Install VS Code + Python extension
3. ✅ Create `C:\bracu-chatbot` folder
4. ✅ Get Groq API key (free)
5. ✅ Get Firecrawl API key (free)
6. ✅ Run `pip install streamlit chromadb sentence-transformers requests beautifulsoup4 python-dotenv`
7. ✅ Create `scrape_bracu.py` → Run it
8. ✅ Create `chunk_documents.py` → Run it
9. ✅ Create `build_vector_db.py` → Run it (close Chrome first!)
10. ✅ Create `app.py` → Test locally with `streamlit run app.py`
11. ✅ Create GitHub repo, push code
12. ✅ Deploy to Streamlit Cloud
13. ✅ Share your live link!

If you get stuck on any step, paste the exact error and I'll help you debug it.