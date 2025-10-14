#!/usr/bin/env python3
"""
DSPy Dataset Wrapper for MMESGBench
Handles dataset loading, corrections mapping, and train/dev/test splits
"""

import json
import random
from typing import List, Dict, Any
from pathlib import Path
import dspy

class MMESGBenchDataset:
    """Wrapper for MMESGBench dataset with corrected documents"""

    def __init__(self, dataset_path: str = "mmesgbench_dataset_corrected.json"):
        """
        Initialize dataset from authoritative corrected dataset

        Args:
            dataset_path: Path to corrected dataset (relative to project root)
        """
        # Get project root (parent of dspy_implementation)
        project_root = Path(__file__).parent.parent

        # Make path absolute from project root
        self.dataset_path = project_root / dataset_path

        # Load authoritative corrected dataset
        self.data = self._load_dataset()

        print(f"✅ Loaded {len(self.data)} questions from authoritative corrected dataset")
        print(f"   Dataset: {dataset_path}")
        print(f"   DSPy baseline: 45.1% (421/933)")

        # Automatically create splits
        splits = self.create_splits()
        self.train_set = splits['train']
        self.dev_set = splits['dev']
        self.test_set = splits['test']

    def _load_dataset(self) -> List[Dict]:
        """Load authoritative corrected MMESGBench dataset"""
        with open(self.dataset_path, 'r') as f:
            data = json.load(f)
        return data

    def to_dspy_examples(self, split_data: List[Dict]) -> List[dspy.Example]:
        """
        Convert dataset to DSPy Example objects

        Args:
            split_data: List of dataset items

        Returns:
            List of dspy.Example objects
        """
        examples = []

        for item in split_data:
            example = dspy.Example(
                doc_id=item['doc_id'],
                question=item['question'],
                answer=str(item['answer']),
                answer_format=item['answer_format'],
                evidence_pages=item.get('evidence_pages', ''),
                evidence_sources=item.get('evidence_sources', ''),
                doc_type=item.get('doc_type', '')
            ).with_inputs('doc_id', 'question', 'answer_format')

            examples.append(example)

        return examples

    def create_splits(self, train_ratio: float = 0.2, dev_ratio: float = 0.1,
                     test_ratio: float = 0.7, seed: int = 42) -> Dict[str, List[dspy.Example]]:
        """
        Create stratified train/dev/test splits

        Args:
            train_ratio: Proportion for training (default: 0.2 = 20%)
            dev_ratio: Proportion for development (default: 0.1 = 10%)
            test_ratio: Proportion for test (default: 0.7 = 70%)
            seed: Random seed for reproducibility

        Returns:
            Dictionary with 'train', 'dev', 'test' splits as DSPy Examples
        """
        assert abs(train_ratio + dev_ratio + test_ratio - 1.0) < 1e-6, \
            "Split ratios must sum to 1.0"

        # Shuffle data with seed
        random.seed(seed)
        shuffled_data = random.sample(self.data, len(self.data))

        # Calculate split sizes
        n_total = len(shuffled_data)
        n_train = int(n_total * train_ratio)
        n_dev = int(n_total * dev_ratio)
        n_test = n_total - n_train - n_dev

        # Create splits
        train_data = shuffled_data[:n_train]
        dev_data = shuffled_data[n_train:n_train + n_dev]
        test_data = shuffled_data[n_train + n_dev:]

        print(f"\n📊 Dataset splits created:")
        print(f"   Train: {len(train_data)} questions ({train_ratio*100:.0f}%)")
        print(f"   Dev:   {len(dev_data)} questions ({dev_ratio*100:.0f}%)")
        print(f"   Test:  {len(test_data)} questions ({test_ratio*100:.0f}%)")

        # Convert to DSPy Examples
        splits = {
            'train': self.to_dspy_examples(train_data),
            'dev': self.to_dspy_examples(dev_data),
            'test': self.to_dspy_examples(test_data)
        }

        # Save splits to JSON for reproducibility
        self._save_splits(train_data, dev_data, test_data)

        return splits

    def _save_splits(self, train_data: List[Dict], dev_data: List[Dict],
                    test_data: List[Dict]):
        """Save dataset splits to JSON files"""
        splits_dir = Path("dspy_implementation/data_splits")
        splits_dir.mkdir(parents=True, exist_ok=True)

        # Save each split
        with open(splits_dir / f"train_{len(train_data)}.json", 'w') as f:
            json.dump(train_data, f, ensure_ascii=False, indent=2)

        with open(splits_dir / f"dev_{len(dev_data)}.json", 'w') as f:
            json.dump(dev_data, f, ensure_ascii=False, indent=2)

        with open(splits_dir / f"test_{len(test_data)}.json", 'w') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

        print(f"   Splits saved to: {splits_dir}/")

    def get_dataset_stats(self) -> Dict:
        """Get statistics about the dataset"""
        # Count evidence types
        evidence_types = {}
        answer_formats = {}
        documents = {}

        for item in self.data:
            # Evidence types
            for evidence in item.get('evidence_sources', []):
                evidence_types[evidence] = evidence_types.get(evidence, 0) + 1

            # Answer formats
            fmt = item.get('answer_format', 'Unknown')
            answer_formats[fmt] = answer_formats.get(fmt, 0) + 1

            # Documents
            doc = item.get('doc_id', 'Unknown')
            documents[doc] = documents.get(doc, 0) + 1

        stats = {
            'total_questions': len(self.data),
            'evidence_types': evidence_types,
            'answer_formats': answer_formats,
            'num_documents': len(documents),
            'documents': documents
        }

        return stats


if __name__ == "__main__":
    print("=" * 60)
    print("MMESGBench Authoritative Dataset Loading")
    print("=" * 60)

    # Load dataset
    dataset = MMESGBenchDataset()

    # Create splits
    splits = dataset.create_splits()

    # Show statistics
    stats = dataset.get_dataset_stats()
    print(f"\n📋 Dataset Statistics:")
    print(f"   Total questions: {stats['total_questions']}")
    print(f"   Documents: {stats['num_documents']}")
    print(f"\n   Evidence Types:")
    for evidence_type, count in sorted(stats['evidence_types'].items(), key=lambda x: x[1], reverse=True):
        print(f"      • {evidence_type}: {count}")
    print(f"\n   Answer Formats:")
    for fmt, count in sorted(stats['answer_formats'].items(), key=lambda x: x[1], reverse=True):
        print(f"      • {fmt}: {count}")

    print(f"\n✅ Dataset ready for DSPy training with 45.1% baseline!")
