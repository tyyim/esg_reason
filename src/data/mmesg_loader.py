"""
MMESGBench dataset loader implementation following the technical specification.
Creates a small sample for prototype testing with PostgreSQL integration.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from src.utils.config import config
from src.database.connection import get_db_session, db_manager
from src.database.models import Document, QAAnnotation
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class MMESGSampleLoader:
    """Load and manage MMESGBench dataset samples for prototype testing"""

    def __init__(self, sample_size: int = 10):
        self.sample_size = sample_size
        self.dataset_path = "./MMESGBench/dataset/samples.json"
        self.pdf_storage_path = config.storage.pdf_storage_path

    def load_sample_data(self) -> List[Dict[str, Any]]:
        """Load a small sample from MMESGBench for testing"""
        try:
            with open(self.dataset_path, 'r') as f:
                full_dataset = json.load(f)

            # Take first N samples for prototype
            sample_data = full_dataset[:self.sample_size]
            logger.info(f"Loaded {len(sample_data)} samples from MMESGBench")
            return sample_data

        except FileNotFoundError:
            logger.error(f"Dataset file not found at {self.dataset_path}")
            # Return mock data for testing if file not available
            return self._create_mock_sample()
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            return []

    def _create_mock_sample(self) -> List[Dict[str, Any]]:
        """Create mock sample data for testing when dataset file is not available"""
        mock_data = [
            {
                "doc_id": "AR6 Synthesis Report Climate Change 2023.pdf",
                "doc_type": "Government & International Organization Documents",
                "question": "According to the IPCC, which region had the highest per capita GHG emissions in 2019?",
                "answer": "North America",
                "evidence_pages": "[61]",
                "evidence_sources": "['Table']",
                "answer_format": "Str"
            },
            {
                "doc_id": "AR6 Synthesis Report Climate Change 2023.pdf",
                "doc_type": "Government & International Organization Documents",
                "question": "Using the IPCC report, calculate the total additional population exposed to coastal flooding events by 2040 under SSP2-4.5 scenario.",
                "answer": "19.62",
                "evidence_pages": "[116]",
                "evidence_sources": "['Image', 'Generalized-text (Layout)']",
                "answer_format": "Float"
            },
            {
                "doc_id": "AR6 Synthesis Report Climate Change 2023.pdf",
                "doc_type": "Government & International Organization Documents",
                "question": "According to IPCC's projections, by when are CO2 emissions expected to reach net zero under the 'very low GHG emissions' scenario (SSP1-1.9)?",
                "answer": "2050",
                "evidence_pages": "[25]",
                "evidence_sources": "['Pure-text (Plain-text)']",
                "answer_format": "Int"
            }
        ]
        logger.warning("Using mock data for testing")
        return mock_data

    def store_samples_in_db(self, samples: List[Dict[str, Any]]) -> bool:
        """Store sample data in PostgreSQL database using existing models"""
        try:
            with get_db_session() as session:
                documents_added = set()

                for sample in samples:
                    doc_id = sample["doc_id"]

                    # Add document if not exists
                    if doc_id not in documents_added:
                        existing_doc = session.query(Document).filter_by(doc_id=doc_id).first()
                        if not existing_doc:
                            document = Document(
                                doc_id=doc_id,
                                doc_type=sample["doc_type"],
                                file_path=os.path.join(self.pdf_storage_path, doc_id)
                            )
                            session.add(document)
                            logger.info(f"Added document: {doc_id}")
                        documents_added.add(doc_id)

                    # Add QA annotation
                    existing_qa = session.query(QAAnnotation).filter_by(
                        doc_id=doc_id,
                        question=sample["question"]
                    ).first()

                    if not existing_qa:
                        qa_annotation = QAAnnotation(
                            doc_id=doc_id,
                            question=sample["question"],
                            answer=sample["answer"],
                            answer_format=sample["answer_format"],
                            evidence_pages=self._parse_evidence_pages(sample["evidence_pages"]),
                            evidence_sources=self._parse_evidence_sources(sample["evidence_sources"]),
                            split="test"  # Mark as test data for prototype
                        )
                        session.add(qa_annotation)
                        logger.info(f"Added QA annotation for doc: {doc_id}")

                session.commit()
                logger.info(f"Successfully stored {len(samples)} samples in database")
                return True

        except Exception as e:
            logger.error(f"Error storing samples in database: {e}")
            return False

    def _parse_evidence_pages(self, pages_str: str) -> List[int]:
        """Parse evidence pages from string format like '[61]' to list of integers"""
        try:
            # Remove brackets and parse
            pages_str = pages_str.strip('[]')
            if ',' in pages_str:
                return [int(p.strip()) for p in pages_str.split(',')]
            else:
                return [int(pages_str)] if pages_str else []
        except (ValueError, TypeError):
            logger.warning(f"Could not parse evidence pages: {pages_str}")
            return []

    def _parse_evidence_sources(self, sources_str: str) -> List[str]:
        """Parse evidence sources from string format like "['Table']" to list of strings"""
        try:
            # Use json.loads to parse the string representation of a list
            return json.loads(sources_str.replace("'", '"'))
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Could not parse evidence sources: {sources_str}")
            return []

    def get_sample_by_answer_format(self, answer_format: str) -> List[Dict[str, Any]]:
        """Get samples filtered by answer format for specific testing"""
        samples = self.load_sample_data()
        return [s for s in samples if s.get("answer_format") == answer_format]

    def get_multimodal_samples(self) -> List[Dict[str, Any]]:
        """Get samples that require multimodal processing (charts, tables, images)"""
        samples = self.load_sample_data()
        multimodal_sources = {'Chart', 'Table', 'Image'}

        return [
            s for s in samples
            if any(source in str(s.get("evidence_sources", "")) for source in multimodal_sources)
        ]

    def create_train_test_split(self, train_ratio: float = 0.7) -> Dict[str, List[Dict[str, Any]]]:
        """Create train/test split for prototype evaluation"""
        samples = self.load_sample_data()
        split_index = int(len(samples) * train_ratio)

        return {
            "train": samples[:split_index],
            "test": samples[split_index:]
        }


def test_loader():
    """Test function to verify the loader works correctly"""
    loader = MMESGSampleLoader(sample_size=5)

    # Test loading
    samples = loader.load_sample_data()
    print(f"Loaded {len(samples)} samples")

    # Test database storage
    if samples:
        success = loader.store_samples_in_db(samples)
        print(f"Database storage: {'Success' if success else 'Failed'}")

    # Test filtering
    multimodal = loader.get_multimodal_samples()
    print(f"Found {len(multimodal)} multimodal samples")

    return samples


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Test the loader
    test_samples = test_loader()
    for i, sample in enumerate(test_samples):
        print(f"\nSample {i+1}:")
        print(f"  Doc: {sample['doc_id']}")
        print(f"  Question: {sample['question'][:80]}...")
        print(f"  Answer: {sample['answer']}")
        print(f"  Format: {sample['answer_format']}")