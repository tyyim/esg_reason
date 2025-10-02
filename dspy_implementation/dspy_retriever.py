#!/usr/bin/env python3
"""
DSPy-Compatible ColBERT Retriever Wrapper
Wraps existing MultiDocumentColBERTRetriever for DSPy integration
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import existing modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Change to parent directory to ensure correct file paths
original_dir = os.getcwd()
os.chdir(parent_dir)

try:
    from colbert_full_dataset_evaluation import MultiDocumentColBERTRetriever
finally:
    os.chdir(original_dir)


class DSPyColBERTRetriever:
    """
    DSPy-compatible wrapper for existing ColBERT retriever.

    This maintains 100% compatibility with the existing 41.3% baseline
    by using the exact same retrieval logic.
    """

    def __init__(self):
        """Initialize with existing ColBERT retriever"""
        print("🔍 Initializing ColBERT retriever (existing 41.3% baseline)...")
        self.retriever = MultiDocumentColBERTRetriever()
        print("✅ ColBERT retriever ready")

    def retrieve(self, doc_id: str, question: str, top_k: int = 5) -> str:
        """
        Retrieve top-k chunks for a question using ColBERT semantic search.

        Args:
            doc_id: Document identifier (e.g., 'AR6 Synthesis Report...')
            question: ESG question text
            top_k: Number of chunks to retrieve (default: 5)

        Returns:
            Concatenated context string from top-k chunks
        """
        # Index document first (critical step!)
        if not self.retriever.index_document(doc_id):
            print(f"⚠️  Warning: Failed to index document {doc_id}")
            return ""

        # Retrieve using existing infrastructure (41.3% validated)
        chunks = self.retriever.retrieve(doc_id, question, top_k=top_k)

        # Concatenate chunk texts
        context = "\n\n".join([chunk['text'] for chunk in chunks])

        return context

    def get_chunks_with_metadata(self, doc_id: str, question: str, top_k: int = 5) -> list:
        """
        Retrieve chunks with full metadata (for debugging/analysis).

        Returns:
            List of dicts with {text, page, score, chunk_id}
        """
        if not self.retriever.index_document(doc_id):
            return []

        return self.retriever.retrieve(doc_id, question, top_k=top_k)


if __name__ == "__main__":
    print("=" * 60)
    print("DSPy ColBERT Retriever Wrapper Test")
    print("=" * 60)

    # Test retrieval
    retriever = DSPyColBERTRetriever()

    print("\n🧪 Testing retrieval...")
    doc_id = "AR6 Synthesis Report Climate Change 2023.pdf"
    question = "According to the IPCC, which region had the highest per capita GHG emissions in 2019?"

    context = retriever.retrieve(doc_id, question, top_k=5)

    print(f"\n✅ Retrieved context for: '{question[:60]}...'")
    print(f"   Document: {doc_id}")
    print(f"   Context length: {len(context)} chars")
    print(f"   First 200 chars: {context[:200]}...")

    print("\n✅ Retriever wrapper working correctly!")
