#!/usr/bin/env python3
"""
Create Stratified Train/Dev/Test Splits for Phase 1 DSPy Optimization

Stratification Strategy:
- Evidence Type × Difficulty (5 evidence types × 3 difficulty levels = 15 cells)
- Evidence Types: Pure-text, Generalized-text, Table, Chart, Image
- Difficulty: Easy/Medium/Hard (performance-based terciles within each evidence type)
- Splits: 20/10/70 (186 train, 93 dev, 654 test)
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from collections import defaultdict


def load_dataset(dataset_path: str) -> List[Dict]:
    """Load authoritative corrected dataset"""
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    print(f"✅ Loaded {len(data)} questions from {dataset_path}")
    return data


def load_baseline_results(results_path: str) -> Dict:
    """Load baseline evaluation results for difficulty assessment"""
    with open(results_path, 'r') as f:
        results = json.load(f)
    print(f"✅ Loaded baseline results from {results_path}")
    print(f"   Baseline accuracy: {results.get('accuracy', 'N/A'):.1%}")
    return results


def extract_primary_evidence_type(evidence_sources: List[str]) -> str:
    """
    Extract primary evidence type from evidence_sources list

    Maps MMESGBench evidence types to 5 categories:
    - Pure-text (Plain-text)
    - Generalized-text (Sub-titles, Paragraphs, Lists, etc.)
    - Table (Tables)
    - Chart (Bar charts, Pie charts, Line charts, etc.)
    - Image (Photos, Diagrams, Maps, etc.)
    """
    if not evidence_sources or len(evidence_sources) == 0:
        return "Unknown"

    # Take first evidence source and extract main category
    first_source = evidence_sources[0]

    if "Plain-text" in first_source:
        return "Pure-text"
    elif any(x in first_source for x in ["Sub-titles", "Paragraph", "List", "Footnote"]):
        return "Generalized-text"
    elif "Table" in first_source:
        return "Table"
    elif any(x in first_source for x in ["chart", "Chart", "Graph", "graph"]):
        return "Chart"
    elif any(x in first_source for x in ["Photo", "Diagram", "Map", "Image", "Figure", "Logo"]):
        return "Image"
    else:
        # Fallback: categorize based on general patterns
        if "text" in first_source.lower():
            return "Generalized-text"
        else:
            return "Other"


def create_difficulty_assessment(dataset: List[Dict], baseline_results: Dict) -> Dict[str, str]:
    """
    Create difficulty assessment for each question based on baseline performance

    Uses performance-based terciles within each evidence type:
    - Easy: Questions answered correctly in baseline
    - Medium: Questions with partial evidence retrieved
    - Hard: Questions answered incorrectly

    For now, we'll use a simpler proxy based on document-level accuracy
    """
    # Extract per-question correctness from baseline results
    # Since we're using optimized_full_dataset_mmesgbench_with_f1.json,
    # which doesn't have per-question results, we'll use document-level accuracy as proxy

    document_accuracy = baseline_results.get('document_breakdown', {})

    difficulty_map = {}

    for item in dataset:
        doc_id = item['doc_id']
        question = item['question']
        question_key = f"{doc_id}::{question}"

        # Get document accuracy
        doc_acc = document_accuracy.get(doc_id, {}).get('accuracy', 0.5)

        # Simple difficulty heuristic based on document accuracy
        # This is a proxy until we have per-question baseline results
        if doc_acc >= 0.5:
            difficulty_map[question_key] = "Easy"
        elif doc_acc >= 0.3:
            difficulty_map[question_key] = "Medium"
        else:
            difficulty_map[question_key] = "Hard"

    return difficulty_map


def stratify_dataset(dataset: List[Dict], difficulty_map: Dict[str, str],
                     train_ratio: float = 0.20, dev_ratio: float = 0.10,
                     test_ratio: float = 0.70, seed: int = 42) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Create stratified splits based on Evidence Type × Difficulty

    Args:
        dataset: Full dataset
        difficulty_map: Question -> difficulty mapping
        train_ratio: Training set ratio (default 0.20)
        dev_ratio: Development set ratio (default 0.10)
        test_ratio: Test set ratio (default 0.70)
        seed: Random seed

    Returns:
        Tuple of (train_data, dev_data, test_data)
    """
    np.random.seed(seed)

    # Group questions by Evidence Type × Difficulty
    # Use question_id tuple to ensure uniqueness
    strata = defaultdict(list)

    evidence_type_counts = defaultdict(int)
    difficulty_counts = defaultdict(int)
    seen_questions = set()

    for idx, item in enumerate(dataset):
        # Create unique question identifier
        question_id = (item['doc_id'], item['question'])

        # Skip duplicates
        if question_id in seen_questions:
            print(f"   ⚠️ Skipping duplicate question: {question_id}")
            continue
        seen_questions.add(question_id)

        # Extract evidence type
        evidence_type = extract_primary_evidence_type(item.get('evidence_sources', []))
        evidence_type_counts[evidence_type] += 1

        # Get difficulty
        question_key = f"{item['doc_id']}::{item['question']}"
        difficulty = difficulty_map.get(question_key, "Medium")
        difficulty_counts[difficulty] += 1

        # Create stratum key
        stratum_key = f"{evidence_type}::{difficulty}"
        strata[stratum_key].append((idx, item))  # Store with index for debugging

    # Print stratification statistics
    total_unique = sum(len(questions) for questions in strata.values())
    print(f"\n📊 Stratification Statistics:")
    print(f"   Total unique questions: {total_unique}/{len(dataset)}")
    print(f"   Total strata: {len(strata)}")
    print(f"\n   Evidence Types:")
    for evidence_type, count in sorted(evidence_type_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / total_unique * 100
        print(f"      • {evidence_type}: {count} ({pct:.1f}%)")
    print(f"\n   Difficulty Levels:")
    for difficulty, count in sorted(difficulty_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / total_unique * 100
        print(f"      • {difficulty}: {count} ({pct:.1f}%)")

    # Create splits maintaining stratification
    train_data = []
    dev_data = []
    test_data = []

    for stratum_key, questions_with_idx in strata.items():
        # Shuffle questions within stratum
        np.random.shuffle(questions_with_idx)

        # Extract just the items (not indices)
        questions = [item for idx, item in questions_with_idx]

        n = len(questions)
        n_train = int(n * train_ratio)
        n_dev = int(n * dev_ratio)

        # Split with clear boundaries
        train_data.extend(questions[:n_train])
        dev_data.extend(questions[n_train:n_train + n_dev])
        test_data.extend(questions[n_train + n_dev:])

    # Shuffle final splits (with same seed for reproducibility)
    np.random.shuffle(train_data)
    np.random.shuffle(dev_data)
    np.random.shuffle(test_data)

    print(f"\n📋 Split Sizes:")
    print(f"   Train: {len(train_data)} ({len(train_data)/total_unique*100:.1f}%)")
    print(f"   Dev:   {len(dev_data)} ({len(dev_data)/total_unique*100:.1f}%)")
    print(f"   Test:  {len(test_data)} ({len(test_data)/total_unique*100:.1f}%)")

    return train_data, dev_data, test_data


def validate_splits(train_data: List[Dict], dev_data: List[Dict], test_data: List[Dict]):
    """Validate split quality"""
    print(f"\n🔍 Validating Splits:")

    # Check for data leakage (no duplicate questions)
    train_questions = {(item['doc_id'], item['question']) for item in train_data}
    dev_questions = {(item['doc_id'], item['question']) for item in dev_data}
    test_questions = {(item['doc_id'], item['question']) for item in test_data}

    train_dev_overlap = train_questions & dev_questions
    train_test_overlap = train_questions & test_questions
    dev_test_overlap = dev_questions & test_questions

    if train_dev_overlap or train_test_overlap or dev_test_overlap:
        print(f"   ⚠️ WARNING: Data leakage detected!")
        print(f"      Train-Dev overlap: {len(train_dev_overlap)}")
        print(f"      Train-Test overlap: {len(train_test_overlap)}")
        print(f"      Dev-Test overlap: {len(dev_test_overlap)}")
    else:
        print(f"   ✅ No data leakage: All splits are disjoint")

    # Check document diversity
    train_docs = {item['doc_id'] for item in train_data}
    dev_docs = {item['doc_id'] for item in dev_data}
    test_docs = {item['doc_id'] for item in test_data}

    print(f"\n   Document Coverage:")
    print(f"      Train: {len(train_docs)} unique documents")
    print(f"      Dev:   {len(dev_docs)} unique documents")
    print(f"      Test:  {len(test_docs)} unique documents")
    print(f"      Overlap (Train∩Dev∩Test): {len(train_docs & dev_docs & test_docs)} documents")

    # Check evidence type distribution
    def count_evidence_types(data):
        counts = defaultdict(int)
        for item in data:
            evidence_type = extract_primary_evidence_type(item.get('evidence_sources', []))
            counts[evidence_type] += 1
        return counts

    train_evidence = count_evidence_types(train_data)
    dev_evidence = count_evidence_types(dev_data)
    test_evidence = count_evidence_types(test_data)

    print(f"\n   Evidence Type Distribution:")
    all_evidence_types = set(train_evidence.keys()) | set(dev_evidence.keys()) | set(test_evidence.keys())
    for evidence_type in sorted(all_evidence_types):
        train_pct = train_evidence.get(evidence_type, 0) / len(train_data) * 100
        dev_pct = dev_evidence.get(evidence_type, 0) / len(dev_data) * 100
        test_pct = test_evidence.get(evidence_type, 0) / len(test_data) * 100
        print(f"      {evidence_type}:")
        print(f"         Train: {train_evidence.get(evidence_type, 0)} ({train_pct:.1f}%)")
        print(f"         Dev:   {dev_evidence.get(evidence_type, 0)} ({dev_pct:.1f}%)")
        print(f"         Test:  {test_evidence.get(evidence_type, 0)} ({test_pct:.1f}%)")


def save_splits(train_data: List[Dict], dev_data: List[Dict], test_data: List[Dict],
                output_dir: str):
    """Save splits to JSON files"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save splits
    train_file = output_path / "train.json"
    dev_file = output_path / "dev.json"
    test_file = output_path / "test.json"

    with open(train_file, 'w') as f:
        json.dump(train_data, f, ensure_ascii=False, indent=2)

    with open(dev_file, 'w') as f:
        json.dump(dev_data, f, ensure_ascii=False, indent=2)

    with open(test_file, 'w') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Splits saved to {output_dir}/")
    print(f"   • train.json: {len(train_data)} questions")
    print(f"   • dev.json: {len(dev_data)} questions")
    print(f"   • test.json: {len(test_data)} questions")


def main():
    parser = argparse.ArgumentParser(description="Create stratified train/dev/test splits")
    parser.add_argument('--input', default='mmesgbench_dataset_corrected.json',
                      help='Input dataset path')
    parser.add_argument('--baseline_results', default='optimized_full_dataset_mmesgbench_with_f1.json',
                      help='Baseline results for difficulty assessment')
    parser.add_argument('--output', default='splits/',
                      help='Output directory for splits')
    parser.add_argument('--train_ratio', type=float, default=0.20,
                      help='Training set ratio (default: 0.20)')
    parser.add_argument('--dev_ratio', type=float, default=0.10,
                      help='Development set ratio (default: 0.10)')
    parser.add_argument('--test_ratio', type=float, default=0.70,
                      help='Test set ratio (default: 0.70)')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed (default: 42)')

    args = parser.parse_args()

    print("=" * 80)
    print("Phase 1a: Stratified Train/Dev/Test Split Creation")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"   Dataset: {args.input}")
    print(f"   Baseline results: {args.baseline_results}")
    print(f"   Output directory: {args.output}")
    print(f"   Split ratios: {args.train_ratio:.0%}/{args.dev_ratio:.0%}/{args.test_ratio:.0%}")
    print(f"   Random seed: {args.seed}")

    # Load dataset
    dataset = load_dataset(args.input)

    # Load baseline results
    baseline_results = load_baseline_results(args.baseline_results)

    # Create difficulty assessment
    print(f"\n📊 Creating difficulty assessment...")
    difficulty_map = create_difficulty_assessment(dataset, baseline_results)

    # Create stratified splits
    print(f"\n🔀 Creating stratified splits...")
    train_data, dev_data, test_data = stratify_dataset(
        dataset, difficulty_map,
        args.train_ratio, args.dev_ratio, args.test_ratio,
        args.seed
    )

    # Validate splits
    validate_splits(train_data, dev_data, test_data)

    # Save splits
    save_splits(train_data, dev_data, test_data, args.output)

    print(f"\n✅ Stratified splits created successfully!")
    print(f"   Ready for Phase 1a: MIPROv2 optimization")


if __name__ == "__main__":
    main()
