import os
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URLS = {
    "docs": "https://pytorch.org/docs/stable/",
    "tutorials": "https://pytorch.org/tutorials/"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PyTorchDocBot/1.0; +https://github.com/isaacdonis)"
}

RAW_DATA_DIR = os.path.join("data", "raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)


def get_all_links(base_url):
    seen = set()
    to_visit = [base_url]
    visited = []

    domain = urlparse(base_url).netloc

    while to_visit:
        url = to_visit.pop()
        if url in seen:
            print(f"[SKIP] Already seen: {url}")
            continue

        print(f"[FETCH] {url}")
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                print(f"[WARN] Skipped (status {response.status_code}): {url}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            visited.append((url, soup.prettify()))

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                joined = urljoin(url, href)
                if urlparse(joined).netloc != domain:
                    continue
                if '#' in joined:
                    joined = joined.split('#')[0]
                if joined.startswith(base_url) and joined not in seen:
                    print(f"  ↪ Queued: {joined}")
                    to_visit.append(joined)

        except Exception as e:
            print(f"[ERROR] Failed to fetch {url}: {e}")
        seen.add(url)

    return visited


def save_pages(pages, subfolder):
    output_dir = os.path.join(RAW_DATA_DIR, subfolder)

    # create the data output folder if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    for i, (url, html) in enumerate(tqdm(pages, desc=f"Saving {subfolder} pages")):
        slug = url.replace(BASE_URLS[subfolder], "").strip(
            "/").replace("/", "_") or "index"
        filename = os.path.join(output_dir, f"{slug}.html")
        print(f"[SAVE] {slug}.html -> {filename}")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)


def main():
    for key, base_url in BASE_URLS.items():
        print(f"\n🚀 Starting crawl for '{key}' at {base_url}")
        pages = get_all_links(base_url)
        print(f"✅ Finished crawling '{key}': {len(pages)} pages collected")
        save_pages(pages, key)
        print(f"📁 Saved all '{key}' pages to data/raw/{key}/")
        time.sleep(1)


if __name__ == "__main__":
    main()
