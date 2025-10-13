#!/usr/bin/env python3
"""
Index IPCC AR6 WG3 document in small batches to avoid timeouts
"""

import json
import sys
from pathlib import Path
from typing import List, Dict
import fitz  # PyMuPDF
from tqdm import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import PGVector
from langchain_community.embeddings import DashScopeEmbeddings
from langchain.schema import Document
import time

sys.path.insert(0, str(Path(__file__).parent))
from src.utils.config import config

IPCC_CHECKPOINT = "ipcc_indexing_checkpoint.json"
BATCH_SIZE = 50  # Small batches to avoid timeout


def load_checkpoint() -> Dict:
    """Load checkpoint"""
    if Path(IPCC_CHECKPOINT).exists():
        with open(IPCC_CHECKPOINT, 'r') as f:
            return json.load(f)
    return {"chunks_indexed": 0, "total_chunks": 0}


def save_checkpoint(checkpoint: Dict):
    """Save checkpoint"""
    with open(IPCC_CHECKPOINT, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def extract_text_from_pdf(pdf_path: Path, chunk_size: int = 512) -> List[Dict]:
    """Extract text chunks from PDF"""
    chunks = []

    with fitz.open(pdf_path) as pdf:
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            page_text = page.get_text()

            if not page_text.strip():
                continue

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=50,
                length_function=len,
            )

            page_chunks = text_splitter.split_text(page_text)

            for chunk_text in page_chunks:
                if chunk_text.strip():
                    chunks.append({
                        'text': chunk_text,
                        'page': page_num + 1,
                        'chunk_id': len(chunks),
                        'source': pdf_path.name
                    })

    return chunks


def main():
    """Index IPCC document in small batches"""
    print("=" * 80)
    print("IPCC AR6 WG3 Batched Indexing")
    print("=" * 80)

    doc_id = "ipcc-ar6-wg3.pdf"
    pdf_path = Path('source_documents') / doc_id

    if not pdf_path.exists():
        print(f"❌ File not found: {doc_id}")
        return

    # Load checkpoint
    checkpoint = load_checkpoint()
    chunks_done = checkpoint.get('chunks_indexed', 0)

    # Extract all chunks (fast, no API calls)
    print(f"\n📄 Extracting text from {doc_id}...")
    all_chunks = extract_text_from_pdf(pdf_path, chunk_size=512)
    total_chunks = len(all_chunks)
    checkpoint['total_chunks'] = total_chunks

    print(f"✅ Extracted {total_chunks:,} chunks")
    print(f"   Already indexed: {chunks_done:,}")
    print(f"   Remaining: {total_chunks - chunks_done:,}")

    if chunks_done >= total_chunks:
        print("\n✅ All chunks already indexed!")
        return

    # Initialize embeddings
    print("\n🔧 Initializing Qwen embeddings...")
    embeddings = DashScopeEmbeddings(
        model="text-embedding-v4",
        dashscope_api_key=config.qwen.api_key
    )

    # Connect to existing vector store
    collection_name = config.database.collection_name
    connection_string = config.database.url

    print(f"🔗 Connecting to collection: {collection_name}")
    vector_store = PGVector(
        collection_name=collection_name,
        connection_string=connection_string,
        embedding_function=embeddings
    )

    # Process in small batches
    print(f"\n📊 Processing in batches of {BATCH_SIZE} chunks...")

    for i in tqdm(range(chunks_done, total_chunks, BATCH_SIZE), desc="Indexing batches"):
        batch_chunks = all_chunks[i:i+BATCH_SIZE]

        # Convert to LangChain Documents
        documents = []
        for chunk in batch_chunks:
            doc = Document(
                page_content=chunk['text'],
                metadata={
                    'source': doc_id,
                    'page': chunk['page'],
                    'chunk_id': chunk['chunk_id']
                }
            )
            documents.append(doc)

        try:
            # Add batch to vector store
            vector_store.add_documents(documents)

            # Update checkpoint
            checkpoint['chunks_indexed'] = min(i + BATCH_SIZE, total_chunks)
            save_checkpoint(checkpoint)

            # Small delay to avoid rate limiting
            time.sleep(1)

        except Exception as e:
            print(f"\n❌ Failed at chunk {i}: {e}")
            save_checkpoint(checkpoint)
            print(f"💾 Progress saved. Resume by running this script again.")
            return

    # Final update
    checkpoint['chunks_indexed'] = total_chunks
    save_checkpoint(checkpoint)

    print("\n" + "=" * 80)
    print("✅ IPCC Document Indexing Complete!")
    print("=" * 80)
    print(f"   Total chunks indexed: {total_chunks:,}")
    print(f"   Document: {doc_id}")


if __name__ == "__main__":
    main()
