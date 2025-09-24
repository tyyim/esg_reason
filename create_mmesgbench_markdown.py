#!/usr/bin/env python3
"""
Create MMESGBench-compatible markdown files from PDFs
Since MMESGBench uses pre-converted markdown files but doesn't provide conversion code,
we need to reverse-engineer their approach to create compatible .md files
"""

import sys
import os
import fitz
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MMESGMarkdownConverter:
    """Convert PDFs to MMESGBench-compatible markdown format"""

    def __init__(self, output_dir="./MMESGBench_markdowns"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def convert_pdf_to_markdown(self, pdf_path: str, doc_id: str) -> str:
        """
        Convert PDF to markdown following MMESGBench approach
        Since we don't have their conversion code, we'll create equivalent markdown
        that produces similar 60-line chunks
        """
        markdown_lines = []

        try:
            with fitz.open(pdf_path) as pdf:
                logger.info(f"Converting {doc_id} ({pdf.page_count} pages) to markdown")

                for page_num in range(pdf.page_count):
                    page = pdf[page_num]

                    # Extract text preserving structure
                    page_text = page.get_text()

                    if page_text.strip():
                        # Add page marker (similar to how markdown might represent pages)
                        markdown_lines.append(f"# Page {page_num + 1}\n")

                        # Split text into lines and clean up
                        text_lines = page_text.split('\n')

                        for line in text_lines:
                            cleaned_line = line.strip()
                            if cleaned_line:
                                # Add line with newline character (important for chunk counting)
                                markdown_lines.append(cleaned_line + '\n')
                            else:
                                # Preserve empty lines for structure
                                markdown_lines.append('\n')

                        # Add separation between pages
                        markdown_lines.append('\n')

        except Exception as e:
            logger.error(f"Error converting {doc_id}: {e}")
            return None

        # Join all lines into markdown content
        markdown_content = ''.join(markdown_lines)
        return markdown_content

    def save_markdown_file(self, markdown_content: str, doc_id: str) -> str:
        """Save markdown content to file"""
        # Convert PDF filename to markdown filename
        md_filename = doc_id.replace('.pdf', '.md')
        md_path = self.output_dir / md_filename

        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            logger.info(f"Saved markdown file: {md_path}")
            return str(md_path)

        except Exception as e:
            logger.error(f"Error saving markdown file: {e}")
            return None

    def test_chunk_compatibility(self, md_path: str, chunk_size: int = 60) -> list:
        """
        Test if our markdown produces correct chunks
        Replicate MMESGBench's exact chunking logic
        """
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # MMESGBench exact chunking logic
            chunks = ["".join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size)]

            logger.info(f"Created {len(chunks)} chunks from {md_path}")
            return chunks

        except Exception as e:
            logger.error(f"Error testing chunk compatibility: {e}")
            return []

    def analyze_evidence_content(self, chunks: list, evidence_keywords: dict) -> dict:
        """
        Analyze if our chunks contain the expected evidence
        evidence_keywords: {question_id: [keywords to search for]}
        """
        results = {}

        for q_id, keywords in evidence_keywords.items():
            found_chunks = []

            for i, chunk in enumerate(chunks):
                for keyword in keywords:
                    if keyword.lower() in chunk.lower():
                        found_chunks.append({
                            'chunk_id': i,
                            'keyword': keyword,
                            'snippet': chunk[:200] + '...'
                        })
                        break

            results[q_id] = found_chunks

        return results

def main():
    """Convert AR6 PDF to MMESGBench-compatible markdown"""
    print("🔄 Creating MMESGBench-compatible markdown files")
    print("="*60)

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Initialize converter
    converter = MMESGMarkdownConverter()

    # Convert AR6 document
    ar6_pdf = "source_documents/AR6 Synthesis Report Climate Change 2023.pdf"
    doc_id = "AR6 Synthesis Report Climate Change 2023.pdf"

    if not os.path.exists(ar6_pdf):
        print(f"❌ PDF not found: {ar6_pdf}")
        return

    # Convert PDF to markdown
    print(f"📄 Converting {doc_id} to markdown...")
    markdown_content = converter.convert_pdf_to_markdown(ar6_pdf, doc_id)

    if not markdown_content:
        print("❌ Failed to convert PDF to markdown")
        return

    # Save markdown file
    md_path = converter.save_markdown_file(markdown_content, doc_id)

    if not md_path:
        print("❌ Failed to save markdown file")
        return

    print(f"✅ Successfully created: {md_path}")

    # Test chunk compatibility
    print(f"\n🧪 Testing chunk compatibility...")
    chunks = converter.test_chunk_compatibility(md_path, chunk_size=60)

    if chunks:
        print(f"✅ Created {len(chunks)} chunks (60 lines each)")

        # Test evidence content for known questions
        evidence_keywords = {
            'Q1_North_America': ['North America', 'per capita GHG emissions', 'highest'],
            'Q2_Population_Flooding': ['19.62', 'population exposed', 'coastal flooding', 'SSP2-4.5'],
            'Q3_Net_Zero': ['2050', 'net zero', 'CO2 emissions', 'SSP1-1.9'],
            'Q5_Working_Groups': ['3', 'three', 'Working Groups', 'AR6'],
            'Q6_Temperature_Range': ['0.8', '1.3', 'temperature increase', '1850-1900', '2010-2019']
        }

        print(f"\n🔍 Analyzing evidence content...")
        evidence_results = converter.analyze_evidence_content(chunks, evidence_keywords)

        for q_id, findings in evidence_results.items():
            if findings:
                print(f"✅ {q_id}: Found in {len(findings)} chunks")
                for finding in findings[:2]:  # Show first 2 matches
                    print(f"   - Chunk {finding['chunk_id']}: '{finding['keyword']}' -> {finding['snippet'][:100]}...")
            else:
                print(f"❌ {q_id}: Not found in any chunks")

    # Show sample chunks for verification
    print(f"\n📋 Sample chunks for verification:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- Chunk {i+1} (lines {i*60+1}-{min((i+1)*60, len(chunk.split()))} ---")
        print(chunk[:300] + "..." if len(chunk) > 300 else chunk)

    print(f"\n🎉 Markdown conversion completed!")
    print(f"Next step: Use {md_path} in MMESGBench replication for exact chunk matching")

if __name__ == "__main__":
    main()