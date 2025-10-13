#!/usr/bin/env python3
"""
Resumable MMESGBench Document Indexing to PostgreSQL
Checkpoint-enabled: Can resume from any interruption
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Set
import fitz  # PyMuPDF
from tqdm import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import PGVector
from langchain_community.embeddings import DashScopeEmbeddings
from langchain.schema import Document
from sqlalchemy import create_engine, text

# Add parent directory
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import config

CHECKPOINT_FILE = "mmesg_indexing_checkpoint.json"


def load_corrected_documents() -> List[str]:
    """Load unique document list from corrected dataset"""
    with open('mmesgbench_dataset_corrected.json', 'r') as f:
        data = json.load(f)

    doc_ids = sorted(set(item['doc_id'] for item in data))
    print(f"✅ Found {len(doc_ids)} unique documents in corrected dataset")
    return doc_ids


def load_checkpoint() -> Dict:
    """Load checkpoint from previous run"""
    if Path(CHECKPOINT_FILE).exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {"completed_docs": [], "failed_docs": [], "total_chunks": 0}


def save_checkpoint(checkpoint: Dict):
    """Save checkpoint after each document"""
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def get_indexed_documents(collection_name: str, connection_string: str) -> Set[str]:
    """Query database to find which documents are already indexed"""
    try:
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            # Get collection UUID
            result = conn.execute(
                text('SELECT uuid FROM langchain_pg_collection WHERE name = :name'),
                {'name': collection_name}
            )
            row = result.fetchone()

            if not row:
                print(f"   Collection '{collection_name}' doesn't exist yet")
                return set()

            coll_uuid = row[0]

            # Get unique doc_ids from metadata
            result = conn.execute(
                text('''
                    SELECT DISTINCT cmetadata->>'source' as source
                    FROM langchain_pg_embedding
                    WHERE collection_id = :uuid
                '''),
                {'uuid': str(coll_uuid)}
            )

            indexed_docs = {row[0] for row in result if row[0]}
            print(f"   Found {len(indexed_docs)} documents already indexed in database")
            return indexed_docs

    except Exception as e:
        print(f"   ⚠️  Error checking indexed documents: {e}")
        return set()


def extract_text_from_pdf(pdf_path: Path, chunk_size: int = 512) -> List[Dict]:
    """Extract text chunks from PDF with metadata"""
    chunks = []

    try:
        with fitz.open(pdf_path) as pdf:
            for page_num in range(pdf.page_count):
                page = pdf[page_num]
                page_text = page.get_text()

                if not page_text.strip():
                    continue

                # Split into chunks
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=50,
                    length_function=len,
                )

                page_chunks = text_splitter.split_text(page_text)

                for i, chunk_text in enumerate(page_chunks):
                    if chunk_text.strip():
                        chunks.append({
                            'text': chunk_text,
                            'page': page_num + 1,
                            'chunk_id': len(chunks),
                            'source': pdf_path.name
                        })

        return chunks

    except Exception as e:
        print(f"   ❌ Error extracting text: {e}")
        return []


def index_single_document(
    doc_id: str,
    embeddings: DashScopeEmbeddings,
    vector_store: PGVector = None,
    collection_name: str = "MMESG",
    connection_string: str = None
) -> tuple[PGVector, int]:
    """
    Index a single document to PostgreSQL

    Returns:
        (vector_store, num_chunks) - Updated vector store and number of chunks indexed
    """
    # Find PDF file
    pdf_path = Path('source_documents') / doc_id

    if not pdf_path.exists():
        raise FileNotFoundError(f"File not found: {doc_id}")

    # Extract chunks
    chunks = extract_text_from_pdf(pdf_path, chunk_size=512)

    if not chunks:
        raise ValueError(f"No chunks extracted from: {doc_id}")

    # Convert to LangChain Documents
    documents = []
    for chunk in chunks:
        doc = Document(
            page_content=chunk['text'],
            metadata={
                'source': doc_id,
                'page': chunk['page'],
                'chunk_id': chunk['chunk_id']
            }
        )
        documents.append(doc)

    # Index to vector store
    if vector_store is None:
        # First document: create vector store
        vector_store = PGVector.from_documents(
            documents=documents,
            embedding=embeddings,
            collection_name=collection_name,
            connection_string=connection_string,
            pre_delete_collection=False
        )
    else:
        # Subsequent documents: add to existing store
        vector_store.add_documents(documents)

    return vector_store, len(chunks)


def main():
    """Main resumable indexing pipeline"""
    print("=" * 80)
    print("MMESGBench Resumable Document Indexing to PostgreSQL")
    print("=" * 80)

    # Load configuration
    collection_name = config.database.collection_name
    connection_string = config.database.url
    print(f"\n🏷️  Collection: {collection_name}")
    print(f"   Database: {connection_string.split('@')[1] if '@' in connection_string else 'localhost'}")

    # Load document list
    print("\n📂 Loading corrected document list...")
    all_doc_ids = load_corrected_documents()

    # Load checkpoint
    print("\n🔄 Checking for previous progress...")
    checkpoint = load_checkpoint()
    completed_docs = set(checkpoint.get('completed_docs', []))
    failed_docs = set(checkpoint.get('failed_docs', []))
    total_chunks = checkpoint.get('total_chunks', 0)

    if completed_docs:
        print(f"   ✅ Checkpoint found: {len(completed_docs)} documents already processed")

    # Check database for indexed documents
    indexed_in_db = get_indexed_documents(collection_name, connection_string)

    # Combine checkpoint and database check
    already_done = completed_docs | indexed_in_db

    if already_done:
        print(f"   📊 Total documents already indexed: {len(already_done)}")

    # Filter out completed documents
    remaining_docs = [doc for doc in all_doc_ids if doc not in already_done]

    if not remaining_docs:
        print("\n✅ All documents already indexed!")
        print(f"   Total: {len(all_doc_ids)} documents")
        print(f"   Total chunks: {total_chunks}")
        return

    print(f"\n📋 Documents to process: {len(remaining_docs)}/{len(all_doc_ids)}")
    if len(already_done) > 0:
        print(f"   (Skipping {len(already_done)} already indexed)")

    # Initialize embeddings
    print("\n🔧 Initializing Qwen embeddings...")
    embeddings = DashScopeEmbeddings(
        model="text-embedding-v4",
        dashscope_api_key=config.qwen.api_key
    )
    print("✅ Embeddings initialized")

    # Initialize vector store (will be created on first document)
    vector_store = None
    if indexed_in_db:
        # Collection exists, initialize connection to it
        vector_store = PGVector(
            collection_name=collection_name,
            connection_string=connection_string,
            embedding_function=embeddings
        )
        print(f"✅ Connected to existing collection")

    # Process documents one by one with checkpoint
    print("\n" + "=" * 80)
    print("Processing Documents (with checkpoint after each)")
    print("=" * 80)

    successful_count = 0
    new_chunks = 0

    for doc_id in tqdm(remaining_docs, desc="Indexing documents"):
        try:
            # Index document
            vector_store, num_chunks = index_single_document(
                doc_id=doc_id,
                embeddings=embeddings,
                vector_store=vector_store,
                collection_name=collection_name,
                connection_string=connection_string
            )

            # Update counters
            successful_count += 1
            new_chunks += num_chunks
            total_chunks += num_chunks

            # Update checkpoint
            checkpoint['completed_docs'].append(doc_id)
            checkpoint['total_chunks'] = total_chunks

            # Remove from failed if it was there
            if doc_id in failed_docs:
                checkpoint['failed_docs'].remove(doc_id)

            save_checkpoint(checkpoint)

        except Exception as e:
            print(f"\n   ❌ Failed to index {doc_id}: {e}")

            # Mark as failed in checkpoint
            if doc_id not in checkpoint['failed_docs']:
                checkpoint['failed_docs'].append(doc_id)
            save_checkpoint(checkpoint)

            continue

    # Final summary
    print("\n" + "=" * 80)
    print("Indexing Complete!")
    print("=" * 80)
    print(f"✅ Successfully indexed in this run: {successful_count} documents")
    print(f"   New chunks indexed: {new_chunks}")
    print(f"   Total chunks in collection: {total_chunks}")

    if checkpoint['failed_docs']:
        print(f"\n⚠️  Failed documents: {len(checkpoint['failed_docs'])}")
        for doc in checkpoint['failed_docs'][:10]:
            print(f"      - {doc}")

    print(f"\n💾 Checkpoint saved to: {CHECKPOINT_FILE}")
    print("\n✅ You can safely resume this script if interrupted!")


if __name__ == "__main__":
    main()
