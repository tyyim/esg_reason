"""
Real MMESGBench data loader for actual evaluation.
Loads data for a specific PDF document and integrates with PostgreSQL.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from src.utils.config import config
from src.database.connection import get_db_session
from src.database.models import Document, QAAnnotation

logger = logging.getLogger(__name__)


class RealMMESGLoader:
    """Load actual MMESGBench data for a specific PDF"""

    def __init__(self, target_doc: str = "AR6 Synthesis Report Climate Change 2023.pdf"):
        self.target_doc = target_doc
        self.dataset_path = "./MMESGBench/dataset/samples.json"

    def load_single_doc_data(self) -> List[Dict[str, Any]]:
        """Load all questions for a single PDF document"""
        try:
            with open(self.dataset_path, 'r') as f:
                full_dataset = json.load(f)

            # Filter by target document
            doc_samples = [
                sample for sample in full_dataset
                if sample.get("doc_id") == self.target_doc
            ]

            logger.info(f"Found {len(doc_samples)} questions for document: {self.target_doc}")

            # Log sample distribution
            formats = {}
            for sample in doc_samples:
                fmt = sample.get("answer_format", "Unknown")
                formats[fmt] = formats.get(fmt, 0) + 1

            logger.info(f"Answer format distribution: {formats}")
            return doc_samples

        except FileNotFoundError:
            logger.error(f"Dataset file not found at {self.dataset_path}")
            return []
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            return []

    def get_document_info(self) -> Dict[str, Any]:
        """Get document information"""
        samples = self.load_single_doc_data()
        if not samples:
            return {}

        # Get document type from first sample
        doc_type = samples[0].get("doc_type", "Unknown")

        # Collect all evidence pages
        evidence_pages = set()
        evidence_sources = set()

        for sample in samples:
            pages = self._parse_evidence_pages(sample.get("evidence_pages", "[]"))
            evidence_pages.update(pages)

            sources = self._parse_evidence_sources(sample.get("evidence_sources", "[]"))
            evidence_sources.update(sources)

        return {
            "doc_id": self.target_doc,
            "doc_type": doc_type,
            "total_questions": len(samples),
            "evidence_pages": sorted(list(evidence_pages)),
            "evidence_sources": list(evidence_sources),
            "page_count": max(evidence_pages) if evidence_pages else 0
        }

    def store_in_database(self) -> bool:
        """Store document and QA data in PostgreSQL with MMESG collection"""
        try:
            samples = self.load_single_doc_data()
            if not samples:
                logger.error("No samples to store")
                return False

            doc_info = self.get_document_info()

            with get_db_session() as session:
                # Store document
                existing_doc = session.query(Document).filter_by(doc_id=self.target_doc).first()
                if not existing_doc:
                    document = Document(
                        doc_id=self.target_doc,
                        doc_type=doc_info["doc_type"],
                        page_count=doc_info["page_count"],
                        file_path=os.path.join(config.storage.pdf_storage_path, self.target_doc)
                    )
                    session.add(document)
                    logger.info(f"Added document: {self.target_doc}")

                # Store QA annotations
                stored_count = 0
                for sample in samples:
                    existing_qa = session.query(QAAnnotation).filter_by(
                        doc_id=self.target_doc,
                        question=sample["question"]
                    ).first()

                    if not existing_qa:
                        qa_annotation = QAAnnotation(
                            doc_id=self.target_doc,
                            question=sample["question"],
                            answer=sample["answer"],
                            answer_format=sample["answer_format"],
                            evidence_pages=self._parse_evidence_pages(sample.get("evidence_pages", "[]")),
                            evidence_sources=self._parse_evidence_sources(sample.get("evidence_sources", "[]")),
                            split="test"
                        )
                        session.add(qa_annotation)
                        stored_count += 1

                session.commit()
                logger.info(f"Stored {stored_count} QA annotations in database")
                return True

        except Exception as e:
            logger.error(f"Error storing data in database: {e}")
            return False

    def get_samples_by_format(self, answer_format: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get samples filtered by answer format"""
        samples = self.load_single_doc_data()
        filtered = [s for s in samples if s.get("answer_format") == answer_format]
        return filtered[:limit]

    def get_test_subset(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get a balanced test subset with different answer formats"""
        samples = self.load_single_doc_data()

        # Group by answer format
        by_format = {}
        for sample in samples:
            fmt = sample.get("answer_format", "Unknown")
            if fmt not in by_format:
                by_format[fmt] = []
            by_format[fmt].append(sample)

        # Take balanced samples
        test_samples = []
        per_format = max(1, limit // len(by_format))

        for fmt, format_samples in by_format.items():
            test_samples.extend(format_samples[:per_format])
            if len(test_samples) >= limit:
                break

        return test_samples[:limit]

    def _parse_evidence_pages(self, pages_str: str) -> List[int]:
        """Parse evidence pages from string format"""
        try:
            if isinstance(pages_str, list):
                return [int(p) for p in pages_str]

            pages_str = str(pages_str).strip('[]')
            if ',' in pages_str:
                return [int(p.strip()) for p in pages_str.split(',') if p.strip()]
            else:
                return [int(pages_str)] if pages_str else []
        except (ValueError, TypeError):
            logger.warning(f"Could not parse evidence pages: {pages_str}")
            return []

    def _parse_evidence_sources(self, sources_str: str) -> List[str]:
        """Parse evidence sources from string format"""
        try:
            if isinstance(sources_str, list):
                return sources_str

            # Handle string representation of list
            sources_str = str(sources_str)
            if sources_str.startswith('[') and sources_str.endswith(']'):
                return json.loads(sources_str.replace("'", '"'))
            else:
                return [sources_str] if sources_str else []
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Could not parse evidence sources: {sources_str}")
            return []


def analyze_document_data():
    """Analyze the document data before processing"""
    loader = RealMMESGLoader()

    print("📊 MMESGBench Document Analysis")
    print("=" * 50)

    samples = loader.load_single_doc_data()
    doc_info = loader.get_document_info()

    print(f"Document: {doc_info['doc_id']}")
    print(f"Type: {doc_info['doc_type']}")
    print(f"Total Questions: {doc_info['total_questions']}")
    print(f"Evidence Pages: {len(doc_info['evidence_pages'])} pages")
    print(f"Page Range: {min(doc_info['evidence_pages'])} - {max(doc_info['evidence_pages'])}")
    print(f"Evidence Sources: {doc_info['evidence_sources']}")

    # Analyze answer formats
    formats = {}
    for sample in samples:
        fmt = sample.get("answer_format", "Unknown")
        formats[fmt] = formats.get(fmt, 0) + 1

    print(f"\nAnswer Format Distribution:")
    for fmt, count in formats.items():
        print(f"  {fmt}: {count} questions")

    # Show sample questions for each format
    print(f"\nSample Questions:")
    for fmt in formats.keys():
        format_samples = loader.get_samples_by_format(fmt, 1)
        if format_samples:
            sample = format_samples[0]
            print(f"\n{fmt} Example:")
            print(f"  Q: {sample['question'][:80]}...")
            print(f"  A: {sample['answer']}")
            print(f"  Pages: {sample.get('evidence_pages', 'N/A')}")

    return doc_info


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    analyze_document_data()