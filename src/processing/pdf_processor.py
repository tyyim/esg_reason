"""
PDF processing pipeline based on MMESGBench approach.
Implements both text extraction and image-based processing.
"""

import os
import fitz
import logging
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
from pathlib import Path
from src.utils.config import config
from src.models.qwen_api import QwenEmbeddingClient
from src.database.connection import get_db_session
from src.database.models import Document, Evidence

logger = logging.getLogger(__name__)


class MMESGPDFProcessor:
    """PDF processor following MMESGBench methodology"""

    def __init__(self):
        self.embedding_client = QwenEmbeddingClient()
        self.pdf_storage_path = config.storage.pdf_storage_path
        self.processed_data_path = config.storage.processed_data_path

        # MMESGBench parameters
        self.max_pages = 120  # From colpali.py
        self.resolution = 144  # DPI from colpali.py
        self.chunk_size = 60  # Lines per chunk from llm.py

        # Ensure directories exist
        os.makedirs(self.processed_data_path, exist_ok=True)
        os.makedirs(os.path.join(self.processed_data_path, "images"), exist_ok=True)
        os.makedirs(os.path.join(self.processed_data_path, "chunks"), exist_ok=True)

    def process_pdf_document(self, doc_id: str, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Process a PDF document following MMESGBench approach

        Args:
            doc_id: Document ID (filename)
            force_reprocess: Whether to reprocess if already exists

        Returns:
            Processing results summary
        """
        pdf_path = os.path.join(self.pdf_storage_path, doc_id)

        if not os.path.exists(pdf_path):
            logger.error(f"PDF not found: {pdf_path}")
            return {"error": f"PDF not found: {pdf_path}"}

        logger.info(f"Processing PDF: {doc_id}")

        try:
            with fitz.open(pdf_path) as pdf:
                # Get document info
                page_count = min(self.max_pages, pdf.page_count)
                doc_info = {
                    "doc_id": doc_id,
                    "total_pages": pdf.page_count,
                    "processed_pages": page_count,
                    "file_size": os.path.getsize(pdf_path)
                }

                # Process text chunks
                text_chunks = self._extract_text_chunks(pdf, doc_id, page_count)

                # Process page images
                page_images = self._extract_page_images(pdf, doc_id, page_count)

                # Store in database
                db_result = self._store_in_database(doc_info, text_chunks, page_images)

                result = {
                    "doc_id": doc_id,
                    "success": True,
                    "processed_pages": page_count,
                    "text_chunks": len(text_chunks),
                    "page_images": len(page_images),
                    "database_stored": db_result,
                    "embeddings_generated": sum(1 for chunk in text_chunks if chunk.get("embedding"))
                }

                logger.info(f"Successfully processed {doc_id}: {result}")
                return result

        except Exception as e:
            logger.error(f"Error processing PDF {doc_id}: {e}")
            return {"error": str(e), "success": False}

    def _extract_text_chunks(self, pdf: fitz.Document, doc_id: str, page_count: int) -> List[Dict[str, Any]]:
        """Extract text chunks from PDF following MMESGBench approach exactly"""
        logger.info(f"Extracting text chunks from {doc_id} using MMESGBench strategy")

        # Step 1: Extract all text as continuous markdown (following MMESGBench)
        all_text_lines = []
        page_line_mapping = {}  # Track which lines belong to which pages
        current_line_num = 0

        for page_num in range(page_count):
            try:
                page = pdf[page_num]
                page_text = page.get_text()

                if page_text.strip():
                    page_lines = page_text.split('\n')
                    page_start_line = current_line_num

                    for line in page_lines:
                        all_text_lines.append(line)
                        page_line_mapping[current_line_num] = page_num + 1
                        current_line_num += 1

            except Exception as e:
                logger.error(f"Error extracting text from page {page_num + 1}: {e}")

        logger.info(f"Extracted {len(all_text_lines)} total lines from {doc_id}")

        # Step 2: Create chunks exactly like MMESGBench (60 lines per chunk)
        chunks = []
        chunk_num = 1

        # MMESGBench chunking: ["".join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size)]
        for i in range(0, len(all_text_lines), self.chunk_size):
            chunk_lines = all_text_lines[i:i + self.chunk_size]
            chunk_text = '\n'.join(chunk_lines).strip()

            if chunk_text:
                # Determine primary page for this chunk (page with most lines)
                line_indices = range(i, min(i + self.chunk_size, len(all_text_lines)))
                page_counts = {}
                for line_idx in line_indices:
                    if line_idx in page_line_mapping:
                        page = page_line_mapping[line_idx]
                        page_counts[page] = page_counts.get(page, 0) + 1

                primary_page = max(page_counts.items(), key=lambda x: x[1])[0] if page_counts else 1

                # Generate embedding for chunk
                try:
                    embedding = self.embedding_client.embed_text(chunk_text)

                    chunk_data = {
                        "doc_id": doc_id,
                        "page_number": primary_page,
                        "chunk_id": f"{doc_id}_chunk_{chunk_num}",
                        "text_content": chunk_text,
                        "line_start": i,
                        "line_end": min(i + self.chunk_size, len(all_text_lines)),
                        "char_count": len(chunk_text),
                        "line_count": len(chunk_lines),
                        "embedding": embedding,
                        "evidence_type": "text",
                        "pages_spanned": list(set(page_line_mapping[idx] for idx in line_indices if idx in page_line_mapping))
                    }
                    chunks.append(chunk_data)
                    chunk_num += 1

                except Exception as e:
                    logger.error(f"Error generating embedding for chunk {chunk_num}: {e}")

        logger.info(f"Created {len(chunks)} text chunks using MMESGBench strategy (60 lines per chunk)")
        return chunks

    def _extract_page_images(self, pdf: fitz.Document, doc_id: str, page_count: int) -> List[Dict[str, Any]]:
        """Extract page images following ColPali approach"""
        logger.info(f"Extracting page images from {doc_id}")

        doc_name = doc_id.replace('.pdf', '')
        images = []

        for page_num in range(page_count):
            try:
                page = pdf[page_num]

                # Convert to image with specified resolution (following colpali.py)
                pix = page.get_pixmap(dpi=self.resolution)

                # Save image
                image_filename = f"{doc_name}_page_{page_num + 1}.png"
                image_path = os.path.join(self.processed_data_path, "images", image_filename)
                pix.save(image_path)

                # Get image info
                img = Image.open(image_path)

                image_data = {
                    "doc_id": doc_id,
                    "page_number": page_num + 1,
                    "image_path": image_path,
                    "image_filename": image_filename,
                    "width": img.width,
                    "height": img.height,
                    "dpi": self.resolution,
                    "evidence_type": "image",
                    "file_size": os.path.getsize(image_path)
                }
                images.append(image_data)

            except Exception as e:
                logger.error(f"Error processing image for page {page_num + 1} of {doc_id}: {e}")

        logger.info(f"Extracted {len(images)} page images from {doc_id}")
        return images

    def _store_in_database(self, doc_info: Dict[str, Any], text_chunks: List[Dict[str, Any]],
                          page_images: List[Dict[str, Any]]) -> bool:
        """Store processed content in PostgreSQL database"""
        try:
            with get_db_session() as session:
                # Store or update document
                existing_doc = session.query(Document).filter_by(doc_id=doc_info["doc_id"]).first()
                if existing_doc:
                    existing_doc.page_count = doc_info["processed_pages"]
                    existing_doc.file_size = doc_info["file_size"]
                else:
                    document = Document(
                        doc_id=doc_info["doc_id"],
                        doc_type="ESG Document",  # Default type
                        page_count=doc_info["processed_pages"],
                        file_path=os.path.join(self.pdf_storage_path, doc_info["doc_id"]),
                        file_size=doc_info["file_size"]
                    )
                    session.add(document)

                # Store text chunks as evidence
                for chunk in text_chunks:
                    if chunk.get("embedding"):  # Only store chunks with embeddings
                        evidence = Evidence(
                            doc_id=chunk["doc_id"],
                            page_number=chunk["page_number"],
                            evidence_type="text",
                            text_content=chunk["text_content"],
                            embeddings=chunk["embedding"],
                            embedding_model=self.embedding_client.embedding_model
                        )
                        session.add(evidence)

                # Store page images as evidence
                for image in page_images:
                    evidence = Evidence(
                        doc_id=image["doc_id"],
                        page_number=image["page_number"],
                        evidence_type="image",
                        image_path=image["image_path"],
                        embedding_model=None  # No embedding for images yet
                    )
                    session.add(evidence)

                session.commit()
                logger.info(f"Stored {len(text_chunks)} text chunks and {len(page_images)} images in database")
                return True

        except Exception as e:
            logger.error(f"Error storing in database: {e}")
            return False

    def get_processing_stats(self, doc_id: str) -> Dict[str, Any]:
        """Get processing statistics for a document"""
        try:
            with get_db_session() as session:
                # Get document info
                doc = session.query(Document).filter_by(doc_id=doc_id).first()
                if not doc:
                    return {"error": "Document not found"}

                # Count evidence by type
                text_evidence_count = session.query(Evidence).filter_by(
                    doc_id=doc_id, evidence_type="text"
                ).count()

                image_evidence_count = session.query(Evidence).filter_by(
                    doc_id=doc_id, evidence_type="image"
                ).count()

                # Count embeddings
                embedded_evidence_count = session.query(Evidence).filter(
                    Evidence.doc_id == doc_id,
                    Evidence.embeddings.isnot(None)
                ).count()

                return {
                    "doc_id": doc_id,
                    "page_count": doc.page_count,
                    "file_size": doc.file_size,
                    "text_chunks": text_evidence_count,
                    "page_images": image_evidence_count,
                    "embedded_chunks": embedded_evidence_count,
                    "processed_at": doc.processed_at
                }

        except Exception as e:
            logger.error(f"Error getting stats for {doc_id}: {e}")
            return {"error": str(e)}

    def retrieve_relevant_chunks(self, question: str, doc_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve most relevant text chunks for a question using vector similarity"""
        try:
            # Generate question embedding
            question_embedding = self.embedding_client.embed_text(question)
            if not question_embedding:
                logger.error("Failed to generate question embedding")
                return []

            with get_db_session() as session:
                # Get all text evidence with embeddings for the document
                evidence_records = session.query(Evidence).filter(
                    Evidence.doc_id == doc_id,
                    Evidence.evidence_type == "text",
                    Evidence.embeddings.isnot(None)
                ).all()

                if not evidence_records:
                    logger.warning(f"No embedded text evidence found for {doc_id}")
                    return []

                # Calculate similarities
                similarities = []
                for evidence in evidence_records:
                    similarity = self._cosine_similarity(question_embedding, evidence.embeddings)
                    similarities.append({
                        "evidence_id": evidence.id,
                        "page_number": evidence.page_number,
                        "text_content": evidence.text_content,
                        "similarity": similarity
                    })

                # Sort by similarity and return top_k
                similarities.sort(key=lambda x: x["similarity"], reverse=True)
                return similarities[:top_k]

        except Exception as e:
            logger.error(f"Error retrieving chunks for {doc_id}: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            import numpy as np
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)

            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return np.dot(vec1, vec2) / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0


def test_pdf_processor():
    """Test the PDF processor with AR6 document"""
    print("🧪 Testing PDF Processor (MMESGBench approach)")
    print("="*60)

    processor = MMESGPDFProcessor()
    ar6_doc = "AR6 Synthesis Report Climate Change 2023.pdf"

    # Check if PDF exists
    pdf_path = os.path.join(processor.pdf_storage_path, ar6_doc)
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        print("Please download the AR6 report and place it in the source_documents folder")
        return

    print(f"✅ Found PDF: {ar6_doc}")

    # Process the document
    print("\n📄 Processing PDF document...")
    result = processor.process_pdf_document(ar6_doc, force_reprocess=True)

    if result.get("success"):
        print(f"✅ Processing completed successfully!")
        print(f"   Pages processed: {result['processed_pages']}")
        print(f"   Text chunks: {result['text_chunks']}")
        print(f"   Page images: {result['page_images']}")
        print(f"   Embeddings generated: {result['embeddings_generated']}")
        print(f"   Database stored: {result['database_stored']}")

        # Get processing stats
        print(f"\n📊 Processing Statistics:")
        stats = processor.get_processing_stats(ar6_doc)
        for key, value in stats.items():
            print(f"   {key}: {value}")

        # Test retrieval
        print(f"\n🔍 Testing Retrieval:")
        test_question = "Which region had the highest per capita GHG emissions?"
        relevant_chunks = processor.retrieve_relevant_chunks(test_question, ar6_doc, top_k=3)

        print(f"Question: {test_question}")
        print(f"Found {len(relevant_chunks)} relevant chunks:")
        for i, chunk in enumerate(relevant_chunks):
            print(f"   {i+1}. Page {chunk['page_number']}, similarity: {chunk['similarity']:.3f}")
            print(f"      Text: {chunk['text_content'][:100]}...")

    else:
        print(f"❌ Processing failed: {result}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_pdf_processor()