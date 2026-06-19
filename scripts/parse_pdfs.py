import fitz
import json
import os
import requests

PDF_URLS = [
    "https://www.bracu.ac.bd/sites/default/files/student-handbook.pdf",
]

def download_and_extract(pdf_url):
    local_path = f"data/raw/pdfs/{os.path.basename(pdf_url)}"
    os.makedirs("data/raw/pdfs", exist_ok=True)
    resp = requests.get(pdf_url)
    with open(local_path, "wb") as f:
        f.write(resp.content)
    doc = fitz.open(local_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

pdf_content = {}
for url in PDF_URLS:
    print(f"Extracting PDF: {url}")
    try:
        text = download_and_extract(url)
        if len(text) > 100:
            pdf_content[url] = text
            print(f"  OK ({len(text)} chars)")
        else:
            print(f"  Empty or failed")
    except Exception as e:
        print(f"  Failed: {e}")

with open("data/raw/bracu_pdfs.json", "w", encoding="utf-8") as f:
    json.dump(pdf_content, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(pdf_content)} PDFs")
