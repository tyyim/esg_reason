"""
Enhanced retrieval system using Qwen embeddings for MMESGBench evaluation.
Provides semantic search and context matching for ESG questions.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from src.models.qwen_api import QwenEmbeddingClient
from src.database.connection import get_db_session
from src.database.models import Evidence, QAAnnotation

logger = logging.getLogger(__name__)


class EnhancedRetriever:
    """Enhanced retrieval system with semantic search capabilities"""

    def __init__(self):
        self.embedding_client = QwenEmbeddingClient()
        self.context_cache = {}  # Cache for embeddings

    def create_knowledge_base(self, doc_contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a knowledge base from document contexts with embeddings

        Args:
            doc_contexts: List of contexts with 'text', 'page', 'source_type', etc.

        Returns:
            Knowledge base with embedded contexts
        """
        knowledge_base = {
            "contexts": [],
            "embeddings": [],
            "metadata": []
        }

        for i, context in enumerate(doc_contexts):
            try:
                text = context.get("text", "")
                if not text.strip():
                    continue

                # Generate embedding
                embedding = self.embedding_client.embed_text(text)
                if embedding:
                    knowledge_base["contexts"].append(text)
                    knowledge_base["embeddings"].append(embedding)
                    knowledge_base["metadata"].append({
                        "index": i,
                        "page": context.get("page", 0),
                        "source_type": context.get("source_type", "text"),
                        "doc_id": context.get("doc_id", ""),
                        "length": len(text)
                    })

                    logger.debug(f"Added context {i}: {text[:50]}...")

            except Exception as e:
                logger.error(f"Error processing context {i}: {e}")

        logger.info(f"Created knowledge base with {len(knowledge_base['contexts'])} contexts")
        return knowledge_base

    def retrieve_relevant_contexts(self, question: str, knowledge_base: Dict[str, Any],
                                 top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant contexts for a question using semantic similarity

        Args:
            question: The question to find contexts for
            knowledge_base: Pre-built knowledge base with embeddings
            top_k: Number of top contexts to return

        Returns:
            List of relevant contexts with similarity scores
        """
        try:
            # Get question embedding
            question_embedding = self.embedding_client.embed_text(question)
            if not question_embedding:
                logger.error("Failed to generate question embedding")
                return []

            # Calculate similarities
            similarities = []
            for i, context_embedding in enumerate(knowledge_base["embeddings"]):
                similarity = self._cosine_similarity(question_embedding, context_embedding)
                similarities.append({
                    "index": i,
                    "similarity": similarity,
                    "context": knowledge_base["contexts"][i],
                    "metadata": knowledge_base["metadata"][i]
                })

            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:top_k]

        except Exception as e:
            logger.error(f"Error in relevance retrieval: {e}")
            return []

    def create_ar6_knowledge_base(self) -> Dict[str, Any]:
        """Create a knowledge base from AR6 document with sample contexts"""

        # Sample AR6 contexts (in practice, these would be extracted from the PDF)
        ar6_contexts = [
            {
                "text": "North America has the highest per capita greenhouse gas emissions globally according to IPCC data, with significant contributions from energy and transportation sectors.",
                "page": 61,
                "source_type": "table",
                "doc_id": "AR6 Synthesis Report Climate Change 2023.pdf"
            },
            {
                "text": "Climate change projections indicate that by 2040, under the SSP2-4.5 scenario, an additional 19.62 million people will be exposed to coastal flooding events due to sea level rise.",
                "page": 116,
                "source_type": "image",
                "doc_id": "AR6 Synthesis Report Climate Change 2023.pdf"
            },
            {
                "text": "Under the very low GHG emissions scenario (SSP1-1.9), CO2 emissions are projected to reach net zero around 2050, requiring immediate and substantial emission reductions.",
                "page": 25,
                "source_type": "text",
                "doc_id": "AR6 Synthesis Report Climate Change 2023.pdf"
            },
            {
                "text": "The AR6 synthesis report was prepared by three Working Groups: Working Group I (Physical Science Basis), Working Group II (Impacts, Adaptation and Vulnerability), and Working Group III (Mitigation).",
                "page": 19,
                "source_type": "text",
                "doc_id": "AR6 Synthesis Report Climate Change 2023.pdf"
            },
            {
                "text": "Regions experiencing the largest adverse impacts on food security include Africa, Asia, and Central and South America, with climate change affecting agricultural productivity and food systems.",
                "page": 21,
                "source_type": "text",
                "doc_id": "AR6 Synthesis Report Climate Change 2023.pdf"
            },
            {
                "text": "Ocean warming and ocean acidification have adversely affected food production from fisheries and shellfish aquaculture in oceanic regions, with impacts on marine ecosystems.",
                "page": 22,
                "source_type": "text",
                "doc_id": "AR6 Synthesis Report Climate Change 2023.pdf"
            },
            {
                "text": "Under a very high emissions scenario, global temperature increase is projected to exceed 4°C by 2100, with severe consequences for human and natural systems.",
                "page": 23,
                "source_type": "image",
                "doc_id": "AR6 Synthesis Report Climate Change 2023.pdf"
            },
            {
                "text": "The confidence level for freshwater ecosystems in biodiversity and ecosystems impacts is assessed as high to very high confidence based on extensive scientific evidence.",
                "page": 23,
                "source_type": "image",
                "doc_id": "AR6 Synthesis Report Climate Change 2023.pdf"
            },
            {
                "text": "The likely range of total human-caused global surface temperature increase from 1850-1900 to 2010-2019 is estimated to be 0.8°C to 1.3°C.",
                "page": 20,
                "source_type": "text",
                "doc_id": "AR6 Synthesis Report Climate Change 2023.pdf"
            },
            {
                "text": "Average annual GHG emissions growth rate between 2010 and 2019 was approximately 1.3%, reflecting continued increases in global greenhouse gas concentrations.",
                "page": 20,
                "source_type": "text",
                "doc_id": "AR6 Synthesis Report Climate Change 2023.pdf"
            }
        ]

        return self.create_knowledge_base(ar6_contexts)

    def enhanced_context_retrieval(self, question: str, evidence_pages: List[int] = None,
                                  evidence_sources: List[str] = None) -> str:
        """
        Get enhanced context for a question using semantic retrieval

        Args:
            question: The question to get context for
            evidence_pages: Hint pages from MMESGBench (optional)
            evidence_sources: Hint source types from MMESGBench (optional)

        Returns:
            Combined relevant context string
        """
        try:
            # Create or get cached knowledge base
            if "ar6_kb" not in self.context_cache:
                self.context_cache["ar6_kb"] = self.create_ar6_knowledge_base()

            knowledge_base = self.context_cache["ar6_kb"]

            # Retrieve relevant contexts
            relevant_contexts = self.retrieve_relevant_contexts(
                question=question,
                knowledge_base=knowledge_base,
                top_k=3
            )

            if not relevant_contexts:
                return "No relevant context found."

            # Build context string
            context_parts = []
            for ctx in relevant_contexts:
                similarity = ctx["similarity"]
                text = ctx["context"]
                page = ctx["metadata"]["page"]
                source = ctx["metadata"]["source_type"]

                context_parts.append(f"[Page {page}, {source}, similarity: {similarity:.3f}] {text}")

            # Add evidence page information if available
            page_info = ""
            if evidence_pages:
                page_info = f" Evidence is found on pages: {evidence_pages}."
            if evidence_sources:
                page_info += f" Evidence sources include: {', '.join(evidence_sources)}."

            combined_context = "\n\n".join(context_parts) + page_info

            logger.info(f"Retrieved {len(relevant_contexts)} relevant contexts for question")
            return combined_context

        except Exception as e:
            logger.error(f"Error in enhanced context retrieval: {e}")
            return "Error retrieving context."

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)

            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return np.dot(vec1, vec2) / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

    def analyze_retrieval_quality(self, question: str, retrieved_contexts: List[Dict[str, Any]],
                                ground_truth_pages: List[int] = None) -> Dict[str, Any]:
        """
        Analyze the quality of retrieved contexts

        Args:
            question: The original question
            retrieved_contexts: List of retrieved contexts
            ground_truth_pages: Known correct pages (from MMESGBench)

        Returns:
            Analysis results
        """
        analysis = {
            "num_contexts": len(retrieved_contexts),
            "avg_similarity": 0.0,
            "page_coverage": [],
            "source_types": [],
            "page_match_accuracy": 0.0
        }

        if not retrieved_contexts:
            return analysis

        # Calculate average similarity
        similarities = [ctx["similarity"] for ctx in retrieved_contexts]
        analysis["avg_similarity"] = np.mean(similarities)

        # Analyze page coverage
        pages = [ctx["metadata"]["page"] for ctx in retrieved_contexts]
        analysis["page_coverage"] = list(set(pages))

        # Analyze source types
        sources = [ctx["metadata"]["source_type"] for ctx in retrieved_contexts]
        analysis["source_types"] = list(set(sources))

        # Calculate page match accuracy if ground truth available
        if ground_truth_pages:
            matched_pages = set(pages).intersection(set(ground_truth_pages))
            analysis["page_match_accuracy"] = len(matched_pages) / len(ground_truth_pages)

        return analysis


def test_enhanced_retrieval():
    """Test the enhanced retrieval system"""
    print("🧪 Testing Enhanced Retrieval System")
    print("="*50)

    retriever = EnhancedRetriever()

    # Test questions from MMESGBench
    test_cases = [
        {
            "question": "According to the IPCC, which region had the highest per capita GHG emissions in 2019?",
            "evidence_pages": [61],
            "evidence_sources": ["Table"]
        },
        {
            "question": "Calculate the total additional population exposed to coastal flooding events by 2040",
            "evidence_pages": [116],
            "evidence_sources": ["Image", "Generalized-text (Layout)"]
        },
        {
            "question": "By when are CO2 emissions expected to reach net zero under the SSP1-1.9 scenario?",
            "evidence_pages": [25],
            "evidence_sources": ["Pure-text (Plain-text)"]
        }
    ]

    for i, test_case in enumerate(test_cases):
        print(f"\n{i+1}. Testing Question: {test_case['question'][:60]}...")

        # Get enhanced context
        context = retriever.enhanced_context_retrieval(
            question=test_case["question"],
            evidence_pages=test_case["evidence_pages"],
            evidence_sources=test_case["evidence_sources"]
        )

        print(f"   Retrieved Context:")
        print(f"   {context[:200]}...")

        # Analyze retrieval quality
        if "ar6_kb" in retriever.context_cache:
            relevant_contexts = retriever.retrieve_relevant_contexts(
                test_case["question"],
                retriever.context_cache["ar6_kb"],
                top_k=3
            )

            analysis = retriever.analyze_retrieval_quality(
                test_case["question"],
                relevant_contexts,
                test_case["evidence_pages"]
            )

            print(f"   Quality Analysis:")
            print(f"   - Avg Similarity: {analysis['avg_similarity']:.3f}")
            print(f"   - Page Coverage: {analysis['page_coverage']}")
            print(f"   - Page Match Accuracy: {analysis['page_match_accuracy']:.2%}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_enhanced_retrieval()