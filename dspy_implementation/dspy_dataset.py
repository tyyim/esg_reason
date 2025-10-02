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

    def __init__(self, dataset_path: str = "MMESGBench/dataset/samples.json",
                 corrections_path: str = "dspy_implementation/document_corrections_mapping.json"):
        """
        Initialize dataset with corrections mapping

        Args:
            dataset_path: Path to MMESGBench samples.json (relative to project root)
            corrections_path: Path to document corrections mapping (relative to project root)
        """
        # Get project root (parent of dspy_implementation)
        project_root = Path(__file__).parent.parent

        # Make paths absolute from project root
        self.dataset_path = project_root / dataset_path
        self.corrections_path = project_root / corrections_path

        # Load dataset and corrections
        self.raw_data = self._load_dataset()
        self.corrections = self._load_corrections()

        # Apply corrections
        self.data = self._apply_corrections(self.raw_data)

        print(f"✅ Loaded {len(self.data)} questions from MMESGBench")
        print(f"✅ Applied {len(self.corrections['corrections'])} document corrections")
        print(f"   Baseline: {self.corrections['baseline_accuracy']*100:.1f}% "
              f"({self.corrections['baseline_questions_correct']}/{self.corrections['total_questions']})")

        # Automatically create splits
        splits = self.create_splits()
        self.train_set = splits['train']
        self.dev_set = splits['dev']
        self.test_set = splits['test']

    def _load_dataset(self) -> List[Dict]:
        """Load MMESGBench dataset"""
        with open(self.dataset_path, 'r') as f:
            data = json.load(f)
        return data

    def _load_corrections(self) -> Dict:
        """Load document corrections mapping"""
        with open(self.corrections_path, 'r') as f:
            corrections = json.load(f)
        return corrections

    def _apply_corrections(self, data: List[Dict]) -> List[Dict]:
        """Apply document corrections to dataset"""
        corrected_data = []

        # Create mapping of corrected documents
        correction_map = {}
        for corr in self.corrections['corrections']:
            if corr['type'] in ['document_replacement', 'filename_validated']:
                correction_map[corr['original']] = corr['corrected']

        for item in data:
            # Apply document name corrections if needed
            if item['doc_id'] in correction_map:
                item['doc_id'] = correction_map[item['doc_id']]

            corrected_data.append(item)

        return corrected_data

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

    def create_splits(self, train_ratio: float = 0.8, dev_ratio: float = 0.1,
                     test_ratio: float = 0.1, seed: int = 42) -> Dict[str, List[dspy.Example]]:
        """
        Create stratified train/dev/test splits

        Args:
            train_ratio: Proportion for training (default: 0.8)
            dev_ratio: Proportion for development (default: 0.1)
            test_ratio: Proportion for test (default: 0.1)
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

    def get_corrected_documents_stats(self) -> Dict:
        """Get statistics about corrected documents"""
        stats = {
            'total_corrections': len(self.corrections['corrections']),
            'questions_affected': self.corrections['total_questions_affected'],
            'overall_improvement': self.corrections['overall_impact'],
            'corrections_detail': []
        }

        for corr in self.corrections['corrections']:
            stats['corrections_detail'].append({
                'document': corr['corrected'],
                'questions': corr['questions_affected'],
                'accuracy_improvement': corr['improvement']
            })

        return stats


if __name__ == "__main__":
    print("=" * 60)
    print("MMESGBench Dataset Loading with Corrections")
    print("=" * 60)

    # Load dataset
    dataset = MMESGBenchDataset()

    # Create splits
    splits = dataset.create_splits()

    # Show statistics
    stats = dataset.get_corrected_documents_stats()
    print(f"\n📋 Document Corrections Summary:")
    for detail in stats['corrections_detail']:
        print(f"   • {detail['document']}: {detail['questions']} questions ({detail['accuracy_improvement']})")

    print(f"\n✅ Dataset ready for DSPy training!")
    print(f"   Total improvement: {stats['overall_improvement']}")
