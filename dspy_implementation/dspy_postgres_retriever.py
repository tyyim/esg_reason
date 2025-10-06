#!/usr/bin/env python3
"""
PostgreSQL-based DSPy Retriever using pgvector
Queries Evidence table for semantic similarity search
"""

import sys
from pathlib import Path
from typing import List, Dict
import logging

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from sqlalchemy import text
from src.database.connection import get_db_session
from src.database.models import Evidence, Document
from src.models.qwen_api import QwenEmbeddingClient

logger = logging.getLogger(__name__)


class DSPyPostgresRetriever:
    """
    PostgreSQL + pgvector retriever for DSPy integration.

    Queries the Evidence table using vector similarity search to find
    relevant document chunks for ESG questions.
    """

    def __init__(self):
        """Initialize PostgreSQL retriever with Qwen embeddings"""
        print("🔍 Initializing PostgreSQL retriever (pgvector + Qwen embeddings)...")
        self.embedding_client = QwenEmbeddingClient()
        print("✅ PostgreSQL retriever ready")

    def retrieve(self, doc_id: str, question: str, top_k: int = 5) -> str:
        """
        Retrieve top-k chunks for a question using pgvector similarity search.

        Args:
            doc_id: Document identifier (e.g., 'AR6 Synthesis Report...')
            question: ESG question text
            top_k: Number of chunks to retrieve (default: 5)

        Returns:
            Concatenated context string from top-k chunks
        """
        try:
            # Generate question embedding
            question_embedding = self.embedding_client.embed_text(question)
            if not question_embedding:
                logger.error(f"Failed to generate embedding for question")
                return ""

            # Query database for similar evidence chunks
            with get_db_session() as session:
                # Use pgvector's <=> operator for cosine distance
                # Lower distance = higher similarity
                query = text("""
                    SELECT
                        e.text_content,
                        e.page_number,
                        e.evidence_type,
                        e.embeddings <=> :query_embedding AS distance
                    FROM evidence e
                    WHERE e.doc_id = :doc_id
                        AND e.text_content IS NOT NULL
                        AND e.text_content != ''
                    ORDER BY e.embeddings <=> :query_embedding
                    LIMIT :top_k
                """)

                result = session.execute(
                    query,
                    {
                        'query_embedding': str(question_embedding),
                        'doc_id': doc_id,
                        'top_k': top_k
                    }
                )

                chunks = []
                for row in result:
                    text_content = row[0]
                    page_number = row[1]
                    evidence_type = row[2]
                    distance = row[3]

                    # Convert distance to similarity score (1 - distance)
                    similarity = 1 - distance

                    chunks.append({
                        'text': text_content,
                        'page': page_number,
                        'type': evidence_type,
                        'score': similarity
                    })

                if not chunks:
                    logger.warning(f"No chunks found for {doc_id}")
                    return ""

                # Concatenate chunk texts
                context = "\n\n".join([
                    f"[Page {chunk['page']}, {chunk['type']}, score: {chunk['score']:.3f}]\n{chunk['text']}"
                    for chunk in chunks
                ])

                logger.debug(f"Retrieved {len(chunks)} chunks for {doc_id}")
                return context

        except Exception as e:
            logger.error(f"Retrieval error for {doc_id}: {e}")
            return ""

    def get_chunks_with_metadata(self, doc_id: str, question: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve chunks with full metadata (for debugging/analysis).

        Returns:
            List of dicts with {text, page, type, score}
        """
        try:
            question_embedding = self.embedding_client.embed_text(question)
            if not question_embedding:
                return []

            with get_db_session() as session:
                query = text("""
                    SELECT
                        e.text_content,
                        e.page_number,
                        e.evidence_type,
                        e.embeddings <=> :query_embedding AS distance
                    FROM evidence e
                    WHERE e.doc_id = :doc_id
                        AND e.text_content IS NOT NULL
                        AND e.text_content != ''
                    ORDER BY e.embeddings <=> :query_embedding
                    LIMIT :top_k
                """)

                result = session.execute(
                    query,
                    {
                        'query_embedding': str(question_embedding),
                        'doc_id': doc_id,
                        'top_k': top_k
                    }
                )

                chunks = []
                for row in result:
                    chunks.append({
                        'text': row[0],
                        'page': row[1],
                        'type': row[2],
                        'score': 1 - row[3]  # Convert distance to similarity
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
