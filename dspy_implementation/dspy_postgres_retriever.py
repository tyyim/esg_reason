#!/usr/bin/env python3
"""
PostgreSQL-based DSPy Retriever using pgvector + LangChain
Queries langchain_pg_embedding table for semantic similarity search
"""

import sys
from pathlib import Path
from typing import List, Dict
import logging
import time

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from langchain_community.vectorstores import PGVector
from langchain_community.embeddings import DashScopeEmbeddings
from src.utils.config import config

logger = logging.getLogger(__name__)


class DSPyPostgresRetriever:
    """
    PostgreSQL + pgvector retriever for DSPy integration.

    Uses LangChain's PGVector to query langchain_pg_embedding table
    for semantic similarity search.
    """

    def __init__(self, collection_name: str = None):
        """
        Initialize PostgreSQL retriever with Qwen embeddings

        Args:
            collection_name: Collection name (default: from config)
        """
        print("🔍 Initializing PostgreSQL retriever (LangChain PGVector + Qwen embeddings)...")

        # Get collection name from config or parameter
        self.collection_name = collection_name or config.database.collection_name

        # Initialize embeddings
        self.embeddings = DashScopeEmbeddings(
            model=config.qwen.embedding_model,
            dashscope_api_key=config.qwen.api_key
        )

        # Initialize vector store
        self.vector_store = PGVector(
            collection_name=self.collection_name,
            connection_string=config.database.url,
            embedding_function=self.embeddings
        )

        print(f"✅ PostgreSQL retriever ready (collection: {self.collection_name})")

    def retrieve(self, doc_id: str, question: str, top_k: int = 5, max_retries: int = 3) -> str:
        """
        Retrieve top-k chunks for a question using LangChain PGVector similarity search.
        Includes retry logic with exponential backoff for connection errors.

        Args:
            doc_id: Document identifier (e.g., 'AR6 Synthesis Report...')
            question: ESG question text
            top_k: Number of chunks to retrieve (default: 5)
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Concatenated context string from top-k chunks
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                # Search with document filter
                docs = self.vector_store.similarity_search_with_score(
                    query=question,
                    k=top_k,
                    filter={'source': doc_id}
                )

                if not docs:
                    logger.warning(f"No chunks found for {doc_id}")
                    return ""

                # Format context
                context_parts = []
                for doc, score in docs:
                    page = doc.metadata.get('page', 'unknown')
                    text = doc.page_content

                    # LangChain returns distance, convert to similarity (lower distance = higher similarity)
                    similarity = 1 / (1 + score)  # Convert distance to similarity

                    context_parts.append(
                        f"[Page {page}, score: {similarity:.3f}]\n{text}"
                    )

                context = "\n\n".join(context_parts)
                logger.debug(f"Retrieved {len(docs)} chunks for {doc_id}")
                return context

            except Exception as e:
                last_error = e

                # Check if it's a connection error that we should retry
                error_str = str(e)
                is_connection_error = (
                    'Connection reset by peer' in error_str or
                    'Connection aborted' in error_str or
                    'ConnectionResetError' in error_str
                )

                if is_connection_error and attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    logger.warning(f"Retrieval connection error for {doc_id} (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Either not a connection error, or max retries reached
                    logger.error(f"Retrieval error for {doc_id}: {e}")
                    return ""

        # If we get here, all retries failed
        logger.error(f"All {max_retries} retry attempts failed for {doc_id}: {last_error}")
        return ""

    def get_chunks_with_metadata(self, doc_id: str, question: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve chunks with full metadata (for debugging/analysis).

        Returns:
            List of dicts with {text, page, score}
        """
        try:
            docs = self.vector_store.similarity_search_with_score(
                query=question,
                k=top_k,
                filter={'source': doc_id}
            )

            chunks = []
            for doc, score in docs:
                similarity = 1 / (1 + score)
                chunks.append({
                    'text': doc.page_content,
                    'page': doc.metadata.get('page', 'unknown'),
                    'score': similarity
                })

            return chunks

        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("PostgreSQL DSPy Retriever Test")
    print("=" * 60)

    # Test retrieval
    retriever = DSPyPostgresRetriever()

    print("\n🧪 Testing retrieval...")
    doc_id = "AR6 Synthesis Report Climate Change 2023.pdf"
    question = "According to the IPCC, which region had the highest per capita GHG emissions in 2019?"

    context = retriever.retrieve(doc_id, question, top_k=5)

    print(f"\n✅ Retrieved context for: '{question[:60]}...'")
    print(f"   Document: {doc_id}")
    print(f"   Context length: {len(context)} chars")

    if context:
        print(f"   First 300 chars: {context[:300]}...")
        print("\n✅ Retriever working correctly!")
    else:
        print("\n⚠️  No context retrieved - check database has indexed documents")
