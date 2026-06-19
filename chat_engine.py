import json
import os
import requests
from sentence_transformers import SentenceTransformer
import chromadb
from dotenv import load_dotenv
from guardrails import mentions_other_university, is_relevant_by_similarity, get_rejection_message
from system_prompt import BRACU_SYSTEM_PROMPT

load_dotenv()

CHUNKS_PATH = "data/processed/chunks.json"
CHROMA_PATH = "./bracu_chroma_db"

_collection = None
_model = None

def load_or_build_db():
    global _collection, _model
    if _collection is not None:
        return _collection, _model

    if not os.path.exists(CHUNKS_PATH):
        raise FileNotFoundError(f"chunks.json not found at {CHUNKS_PATH}. Run data/build_db.py first.")

    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    _model = SentenceTransformer('all-MiniLM-L6-v2')

    client = chromadb.PersistentClient(path=CHROMA_PATH)
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

def retrieve(query, top_k=3):
    collection, model = load_or_build_db()
    query_emb = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_emb,
        n_results=top_k,
        include=["documents", "metadatas", "embeddings"]
    )
    return results, query_emb

def call_llm(provider, system_prompt, user_query):
    if provider == "groq":
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY not set")
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            },
            timeout=30
        )
        data = resp.json()
        if "choices" not in data:
            err = data.get("error", {}).get("message", str(data))
            raise ValueError(f"Groq API error: {err}")
        return data["choices"][0]["message"]["content"]

    elif provider == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY not set")
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
            json={
                "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser: {user_query}"}]}]
            },
            timeout=30
        )
        data = resp.json()
        if "candidates" not in data:
            err = data.get("error", {}).get("message", str(data))
            raise ValueError(f"Gemini API error: {err}")
        return data["candidates"][0]["content"]["parts"][0]["text"]

    return "AI provider unavailable."

def generate_response(user_query):
    if mentions_other_university(user_query):
        return {"answer": get_rejection_message("other_university"), "sources": []}

    results, query_emb = retrieve(user_query)

    if not results["documents"] or not results["documents"][0]:
        return {"answer": get_rejection_message("no_info"), "sources": []}

    retrieved_embs = results.get("embeddings", None)
    if retrieved_embs is not None and len(retrieved_embs) > 0:
        retrieved_embs = retrieved_embs[0]
    else:
        retrieved_embs = []
    if not is_relevant_by_similarity(query_emb[0], retrieved_embs, threshold=0.3):
        return {"answer": get_rejection_message("off_topic"), "sources": []}

    sources = []
    context_parts = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        sources.append(meta["source"])
        truncated = doc[:500] if len(doc) > 500 else doc
        context_parts.append(truncated)

    context = "\n\n---\n\n".join(context_parts)
    if len(context) > 4000:
        context = context[:4000] + "..."

    system_msg = BRACU_SYSTEM_PROMPT.format(context=context)

    try:
        answer = call_llm("groq", system_msg, user_query)
    except Exception as e:
        print(f"Groq failed: {e}. Falling back to Gemini.")
        try:
            answer = call_llm("gemini", system_msg, user_query)
        except Exception as e2:
            answer = f"Sorry, I'm having trouble connecting to my AI services. Please try again later."

    return {"answer": answer, "sources": list(set(sources))}
