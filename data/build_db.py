import json
import re
import os

pages_path = "data/raw/bracu_pages.json"
pdfs_path = "data/raw/bracu_pdfs.json"
output_path = "data/processed/chunks.json"

all_sources = {}

if os.path.exists(pages_path):
    with open(pages_path, "r", encoding="utf-8") as f:
        all_sources.update(json.load(f))

if os.path.exists(pdfs_path):
    with open(pdfs_path, "r", encoding="utf-8") as f:
        all_sources.update(json.load(f))

chunks = []

def chunk_text(text, source_url, chunk_size=800, overlap=100):
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

os.makedirs("data/processed", exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False)

print(f"Created {len(chunks)} chunks -> {output_path}")
