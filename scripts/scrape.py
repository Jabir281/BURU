import cloudscraper
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin

BRACU_BASE = "https://www.bracu.ac.bd"

PRIORITY_PATHS = [
    "/academics",
    "/academic-dates",
    "/schools-and-departments",
    "/programs",
    "/programs/undergraduate",
    "/programs/graduate",
    "/admissions",
    "/admissions/undergraduate",
    "/admissions/undergraduate/admission-requirements",
    "/admissions/undergraduate/application-procedure",
    "/admissions/undergraduate/tuition-and-fees",
    "/admissions/undergraduate/scholarships-and-financial-aid",
    "/admissions/graduate",
    "/admissions/graduate/admission-requirements",
    "/admissions/graduate/tuition-and-fees",
    "/admissions/graduate/scholarships-and-financial-aid",
    "/student-life",
    "/student-life/residential-semester",
    "/student-life/housing-and-dining",
    "/student-life/medical-center",
    "/student-life/counseling-and-wellness",
    "/student-life/career-services",
    "/student-life/student-clubs",
    "/student-life/sports-and-recreation",
    "/student-life/dress-code",
    "/office-of-academic-advising",
    "/office-of-career-services",
    "/library",
    "/transport",
    "/it-services",
    "/policies-and-procedures",
    "/academic-policies",
    "/code-of-conduct",
    "/announcements",
]

scraper = cloudscraper.create_scraper()

def scrape_page(url):
    try:
        resp = scraper.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["nav", "footer", "script", "style", "header"]):
            tag.decompose()
        main = soup.find("div", class_="page") or soup.find("main") or soup.find("article") or soup
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
    time.sleep(1)

with open("data/raw/bracu_pages.json", "w", encoding="utf-8") as f:
    json.dump(all_content, f, ensure_ascii=False, indent=2)

print(f"Scraped {len(all_content)} pages")
