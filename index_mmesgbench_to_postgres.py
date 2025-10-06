#!/usr/bin/env python3
"""
Index MMESGBench Documents to PostgreSQL
Creates MMESG collection with all 45 corrected documents
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

# Add parent directory
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import config


def load_corrected_documents() -> List[str]:
    """Load unique document list from corrected dataset"""
    with open('mmesgbench_dataset_corrected.json', 'r') as f:
        data = json.load(f)

    # Get unique doc_ids (these are the corrected names)
    doc_ids = sorted(set(item['doc_id'] for item in data))

    print(f"✅ Found {len(doc_ids)} unique documents in corrected dataset")
    return doc_ids


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

                # Split into chunks using RecursiveCharacterTextSplitter
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


def index_documents_to_postgres(doc_ids: List[str], collection_name: str = "MMESG"):
    """
    Index all documents to PostgreSQL using LangChain PGVector

    Args:
        doc_ids: List of document IDs to index
        collection_name: Collection name (default: MMESG from .env)
    """
    print("\n" + "=" * 80)
    print(f"Indexing {len(doc_ids)} documents to PostgreSQL")
    print("=" * 80)

    # Initialize embeddings
    print("\n📋 Initializing Qwen embeddings...")
    embeddings = DashScopeEmbeddings(
        model="text-embedding-v4",
        dashscope_api_key=config.qwen.api_key
    )
    print("✅ Embeddings initialized")

    # Prepare connection string
    connection_string = config.database.url

    # Process each document
    all_documents = []
    successful_docs = 0
    failed_docs = []

    for doc_id in tqdm(doc_ids, desc="Processing documents"):
        # Find PDF file
        pdf_path = Path('source_documents') / doc_id

        if not pdf_path.exists():
            print(f"\n⚠️  File not found: {doc_id}")
            failed_docs.append(doc_id)
            continue

        # Extract chunks
        chunks = extract_text_from_pdf(pdf_path, chunk_size=512)

        if not chunks:
            print(f"\n⚠️  No chunks extracted from: {doc_id}")
            failed_docs.append(doc_id)
            continue

        # Convert to LangChain Documents
        for chunk in chunks:
            doc = Document(
                page_content=chunk['text'],
                metadata={
                    'source': doc_id,
                    'page': chunk['page'],
                    'chunk_id': chunk['chunk_id']
                }
            )
            all_documents.append(doc)

        successful_docs += 1

    print(f"\n📊 Extraction Summary:")
    print(f"   Successful: {successful_docs}/{len(doc_ids)} documents")
    print(f"   Total chunks: {len(all_documents)}")

    if failed_docs:
        print(f"   Failed documents: {len(failed_docs)}")
        for doc in failed_docs[:10]:
            print(f"      - {doc}")

    if not all_documents:
        print("\n❌ No documents to index!")
        return

    # Create vector store and index documents
    print(f"\n🔄 Creating/updating PGVector collection: {collection_name}")
    print(f"   Connection: {connection_string.split('@')[1] if '@' in connection_string else 'localhost'}")

    try:
        # Create vector store (will create collection if doesn't exist)
        vector_store = PGVector.from_documents(
            documents=all_documents,
            embedding=embeddings,
            collection_name=collection_name,
            connection_string=connection_string,
            pre_delete_collection=False  # Don't delete existing collection
        )

        print(f"\n✅ Successfully indexed {len(all_documents)} chunks to PostgreSQL!")
        print(f"   Collection: {collection_name}")
        print(f"   Documents: {successful_docs}")
        print(f"   Chunks: {len(all_documents)}")

        # Save indexing metadata
        metadata = {
            'collection_name': collection_name,
            'total_documents': successful_docs,
            'total_chunks': len(all_documents),
            'failed_documents': failed_docs,
            'embedding_model': 'text-embedding-v4',
            'chunk_size': 512,
            'chunk_overlap': 50
        }

        with open('mmesg_postgres_index_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"\n💾 Metadata saved to: mmesg_postgres_index_metadata.json")

    except Exception as e:
        print(f"\n❌ Error creating vector store: {e}")
        import traceback
        traceback.print_exc()


def verify_indexing(collection_name: str = "MMESG"):
    """Verify documents were indexed correctly"""
    print("\n" + "=" * 80)
    print("Verifying Indexing")
    print("=" * 80)

    from sqlalchemy import text
    from src.database.connection import get_db_session

    with get_db_session() as session:
        # Check collection exists
        result = session.execute(
            text('SELECT uuid FROM langchain_pg_collection WHERE name = :name'),
            {'name': collection_name}
        )
        row = result.fetchone()

        if not row:
            print(f"❌ Collection '{collection_name}' not found!")
            return

        coll_uuid = row[0]
        print(f"✅ Collection '{collection_name}' exists (UUID: {coll_uuid})")

        # Count total records
        result = session.execute(
            text('SELECT COUNT(*) FROM langchain_pg_embedding WHERE collection_id = :uuid'),
            {'uuid': str(coll_uuid)}
        )
        total_count = result.scalar()
        print(f"   Total chunks: {total_count}")

        # Count unique documents
        result = session.execute(
            text('''SELECT COUNT(DISTINCT cmetadata->>'source')
                    FROM langchain_pg_embedding
                    WHERE collection_id = :uuid'''),
            {'uuid': str(coll_uuid)}
        )
        doc_count = result.scalar()
        print(f"   Unique documents: {doc_count}")

        # Show sample documents
        result = session.execute(
            text('''SELECT DISTINCT cmetadata->>'source' as source
                    FROM langchain_pg_embedding
                    WHERE collection_id = :uuid
                    LIMIT 10'''),
            {'uuid': str(coll_uuid)}
        )
        samples = [row[0] for row in result]
        print(f"\n   Sample documents:")
        for doc in samples:
            print(f"      - {doc}")


def main():
    """Main indexing pipeline"""
    print("=" * 80)
    print("MMESGBench Document Indexing to PostgreSQL")
    print("=" * 80)

    # Load corrected document list
    print("\n📂 Loading corrected document list...")
    doc_ids = load_corrected_documents()

    # Get collection name from environment
    collection_name = config.database.collection_name
    print(f"\n🏷️  Collection name: {collection_name}")

    # Index documents
    index_documents_to_postgres(doc_ids, collection_name)

    # Verify indexing
    verify_indexing(collection_name)

    print("\n" + "=" * 80)
    print("✅ Indexing Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
