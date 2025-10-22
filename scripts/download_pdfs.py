#!/usr/bin/env python3
"""
Download ESG source documents from MMESGBench hyperlinks.

This script extracts hyperlinks from the ESG_source.pdf document and downloads
all 45 ESG documents to the local source_documents/ directory.
"""

import os
import requests
import fitz  # PyMuPDF
from pathlib import Path
from urllib.parse import urlparse
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
ESG_SOURCE_PDF = "./MMESGBench/dataset/ESG_source.pdf"
DOWNLOAD_DIR = os.getenv("PDF_STORAGE_PATH", "./source_documents/")
DELAY_BETWEEN_DOWNLOADS = 2  # seconds


def extract_hyperlinks_from_pdf(pdf_path: str) -> dict:
    """Extract hyperlinks from ESG_source.pdf"""
    doc_links = {}

    with fitz.open(pdf_path) as doc:
        for page in doc:
            links = page.get_links()
            text_blocks = page.get_text("dict")

            # Extract document names and their corresponding URLs
            for link in links:
                if link.get("uri"):
                    # Get text near the link to determine document name
                    rect = fitz.Rect(link["from"])
                    # Find the text block containing this link
                    for block in text_blocks["blocks"]:
                        if "lines" in block:
                            for line in block["lines"]:
                                for span in line["spans"]:
                                    span_rect = fitz.Rect(span["bbox"])
                                    if span_rect.intersects(rect):
                                        text = span["text"].strip()
                                        if text.endswith(".pdf"):
                                            doc_links[text] = link["uri"]

    return doc_links


def download_file(url: str, filename: str, download_dir: str) -> bool:
    """Download a file from URL to local directory"""
    file_path = os.path.join(download_dir, filename)

    # Skip if file already exists
    if os.path.exists(file_path):
        print(f"✅ {filename} already exists, skipping...")
        return True

    try:
        print(f"📥 Downloading {filename}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        # Check if it's actually a PDF
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and not url.endswith('.pdf'):
            print(f"⚠️  Warning: {filename} may not be a PDF (content-type: {content_type})")

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = os.path.getsize(file_path)
        print(f"✅ Downloaded {filename} ({file_size:,} bytes)")
        return True

    except requests.RequestException as e:
        print(f"❌ Failed to download {filename}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        return False


def main():
    """Main download function"""
    # Create download directory
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    print("🔍 Extracting hyperlinks from ESG_source.pdf...")

    # Extract hyperlinks from the PDF
    try:
        doc_links = extract_hyperlinks_from_pdf(ESG_SOURCE_PDF)
        print(f"📋 Found {len(doc_links)} document links")
    except Exception as e:
        print(f"❌ Error reading ESG_source.pdf: {e}")
        return

    # Download each document
    successful_downloads = 0
    failed_downloads = []

    for filename, url in doc_links.items():
        print(f"\n📄 Processing: {filename}")
        print(f"🔗 URL: {url}")

        if download_file(url, filename, DOWNLOAD_DIR):
            successful_downloads += 1
        else:
            failed_downloads.append((filename, url))

        # Delay between downloads to be respectful
        time.sleep(DELAY_BETWEEN_DOWNLOADS)

    # Summary
    print(f"\n📊 Download Summary:")
    print(f"✅ Successful: {successful_downloads}")
    print(f"❌ Failed: {len(failed_downloads)}")

    if failed_downloads:
        print(f"\n❌ Failed downloads:")
        for filename, url in failed_downloads:
            print(f"  - {filename}: {url}")
        print(f"\n💡 You may need to download these manually from their source websites.")

    print(f"\n📁 All downloaded files are in: {DOWNLOAD_DIR}")


if __name__ == "__main__":
    main()