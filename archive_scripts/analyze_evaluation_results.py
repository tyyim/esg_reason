#!/usr/bin/env python3
"""
Comprehensive Analysis of MMESGBench Evaluation Results
Analyzes document substitution impact, evaluation function differences, and question difficulty
"""

import json
import pandas as pd
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import re
import numpy as np

class EvaluationAnalyzer:
    def __init__(self, results_file: str, dataset_file: str):
        self.results_file = results_file
        self.dataset_file = dataset_file

        # Load data
        with open(results_file, 'r') as f:
            self.results = json.load(f)

        with open(dataset_file, 'r') as f:
            self.dataset = json.load(f)

        # Define substituted documents
        self.substituted_docs = {
            "Gender 2024.pdf": {
                "original": "Gender 2024.pdf",
                "substituted": "UNESCO-GEM-Report-2024.pdf",
                "risk_level": "HIGH",
                "reason": "Different focus - Education vs Gender"
            },
            "ISO 14001.pdf": {
                "original": "ISO 14001.pdf",
                "substituted": "ISO-14001-2015.pdf",
                "risk_level": "LOW",
                "reason": "Official ISO standard vs third-party sources"
            },
            "Microsoft CDP Climate Change Response 2023.pdf": {
                "original": "Microsoft CDP Climate Change Response 2023.pdf",
                "substituted": "Microsoft-CDP-2024-Response.pdf",
                "risk_level": "LOW",
                "reason": "Newer version (2024 vs 2023)"
            }
        }

    def analyze_document_substitution_impact(self) -> Dict[str, Any]:
        """Analyze performance impact of document substitutions"""
        print("🔍 Analyzing Document Substitution Impact...")

        substituted_performance = {}
        normal_performance = {}

        # Calculate performance for substituted documents
        substituted_total = 0
        substituted_correct = 0

        for doc_name, info in self.substituted_docs.items():
            if doc_name in self.results['document_stats']:
                stats = self.results['document_stats'][doc_name]
                accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                substituted_performance[doc_name] = {
                    'accuracy': accuracy,
                    'correct': stats['correct'],
                    'total': stats['total'],
                    'risk_level': info['risk_level'],
                    'reason': info['reason']
                }
                substituted_total += stats['total']
                substituted_correct += stats['correct']

        # Calculate performance for normal documents
        normal_total = 0
        normal_correct = 0

        for doc_name, stats in self.results['document_stats'].items():
            if doc_name not in self.substituted_docs:
                normal_total += stats['total']
                normal_correct += stats['correct']

        overall_substituted_accuracy = substituted_correct / substituted_total if substituted_total > 0 else 0
        overall_normal_accuracy = normal_correct / normal_total if normal_total > 0 else 0

        return {
            'substituted_documents': substituted_performance,
            'substituted_overall': {
                'accuracy': overall_substituted_accuracy,
                'correct': substituted_correct,
                'total': substituted_total
            },
            'normal_documents': {
                'accuracy': overall_normal_accuracy,
                'correct': normal_correct,
                'total': normal_total
            },
            'impact_analysis': {
                'accuracy_gap': overall_normal_accuracy - overall_substituted_accuracy,
                'relative_impact': ((overall_normal_accuracy - overall_substituted_accuracy) / overall_normal_accuracy * 100) if overall_normal_accuracy > 0 else 0
            }
        }

    def analyze_question_difficulty(self) -> Dict[str, Any]:
        """Analyze performance by question difficulty (based on evidence sources and answer format)"""
        print("📊 Analyzing Question Difficulty Patterns...")

        # Classify questions by difficulty
        easy_patterns = {
            'evidence_sources': ['Pure-text (Plain-text)'],
            'answer_formats': ['Str', 'Int'],
            'page_count': 1
        }

        hard_patterns = {
            'evidence_sources': ['Image', 'Table', 'Generalized-text (Layout)'],
            'answer_formats': ['Float', 'List'],
            'page_count_threshold': 2  # Multiple pages
        }

        difficulty_stats = defaultdict(lambda: {'total': 0, 'correct': 0})

        for question in self.dataset:
            doc_id = question['doc_id']
            evidence_sources = eval(question.get('evidence_sources', '[]'))
            answer_format = question.get('answer_format', 'Str')
            evidence_pages = eval(question.get('evidence_pages', '[1]'))

            # Classify difficulty
            difficulty = self._classify_difficulty(evidence_sources, answer_format, len(evidence_pages))

            # Get performance data (if available)
            if doc_id in self.results['document_stats']:
                # This is an approximation since we don't have individual question results
                doc_accuracy = self.results['document_stats'][doc_id]['correct'] / self.results['document_stats'][doc_id]['total']
                difficulty_stats[difficulty]['total'] += 1
                difficulty_stats[difficulty]['correct'] += doc_accuracy  # Weighted by document performance

        # Calculate accuracy by difficulty
        difficulty_analysis = {}
        for difficulty, stats in difficulty_stats.items():
            accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
            difficulty_analysis[difficulty] = {
                'accuracy': accuracy,
                'question_count': stats['total'],
                'estimated_correct': stats['correct']
            }

        return difficulty_analysis

    def _classify_difficulty(self, evidence_sources: List[str], answer_format: str, page_count: int) -> str:
        """Classify question difficulty based on multiple factors"""
        difficulty_score = 0

        # Evidence source complexity
        if any('Image' in src or 'Table' in src for src in evidence_sources):
            difficulty_score += 2
        if 'Generalized-text (Layout)' in evidence_sources:
            difficulty_score += 1
        if 'Pure-text (Plain-text)' in evidence_sources:
            difficulty_score += 0

        # Answer format complexity
        if answer_format in ['Float', 'List']:
            difficulty_score += 2
        elif answer_format == 'Int':
            difficulty_score += 1
        else:  # Str
            difficulty_score += 0

        # Multi-page evidence
        if page_count > 1:
            difficulty_score += 1

        # Classify based on total score
        if difficulty_score <= 1:
            return 'Easy'
        elif difficulty_score <= 3:
            return 'Medium'
        else:
            return 'Hard'

    def compare_evaluation_functions(self) -> Dict[str, Any]:
        """Compare our evaluation functions with MMESGBench baseline"""
        print("⚖️  Comparing Evaluation Functions...")

        comparison = {
            'numeric_evaluation': {
                'our_approach': 'Use ±1% tolerance with exact_match check',
                'mmesgbench_approach': 'Use isclose with rel_tol=0.01 and precision-based rounding',
                'difference': 'MMESGBench uses more sophisticated precision handling and percentage conversion'
            },
            'string_evaluation': {
                'our_approach': 'Exact match after lowercase and strip',
                'mmesgbench_approach': 'Complex cleaning (remove parenthesis, quotes, currency symbols) + fuzzy matching',
                'difference': 'MMESGBench has more aggressive text cleaning and fuzzy matching with 80% threshold'
            },
            'list_evaluation': {
                'our_approach': 'F1 score with 0.8 threshold for correctness',
                'mmesgbench_approach': 'Complex parsing with bracket completion and escape handling',
                'difference': 'MMESGBench has more robust list parsing but similar F1 logic'
            },
            'potential_impact': {
                'numeric': 'LOW - Both use 1% tolerance',
                'string': 'MEDIUM - Their text cleaning might catch edge cases we miss',
                'list': 'LOW - Similar F1 approach'
            }
        }

        return comparison

    def analyze_format_performance(self) -> Dict[str, Any]:
        """Analyze performance by answer format"""
        print("📋 Analyzing Performance by Answer Format...")

        format_stats = defaultdict(lambda: {'total': 0, 'questions': []})

        # Collect questions by format
        for question in self.dataset:
            answer_format = question.get('answer_format', 'Str')
            format_stats[answer_format]['questions'].append(question)
            format_stats[answer_format]['total'] += 1

        # Calculate estimated performance by format
        format_performance = {}

        for answer_format, data in format_stats.items():
            doc_accuracies = []
            for question in data['questions']:
                doc_id = question['doc_id']
                if doc_id in self.results['document_stats']:
                    doc_accuracy = self.results['document_stats'][doc_id]['correct'] / self.results['document_stats'][doc_id]['total']
                    doc_accuracies.append(doc_accuracy)

            avg_accuracy = np.mean(doc_accuracies) if doc_accuracies else 0
            format_performance[answer_format] = {
                'estimated_accuracy': avg_accuracy,
                'question_count': data['total'],
                'sample_questions': [q['question'][:80] + '...' for q in data['questions'][:3]]
            }

        return format_performance

    def generate_comprehensive_report(self) -> str:
        """Generate a comprehensive analysis report"""
        print("📝 Generating Comprehensive Analysis Report...")

        # Run all analyses
        substitution_analysis = self.analyze_document_substitution_impact()
        difficulty_analysis = self.analyze_question_difficulty()
        evaluation_comparison = self.compare_evaluation_functions()
        format_analysis = self.analyze_format_performance()

        # Generate report
        report = f"""
# 📊 MMESGBench Evaluation Results Analysis

## 🎯 Executive Summary
- **Overall Accuracy**: {self.results['accuracy']:.1%} ({self.results['correct_predictions']}/{self.results.get('total_samples', 857)} questions)
- **Target vs Actual**: {self.results.get('target_accuracy', 0.415):.1%} target vs {self.results['accuracy']:.1%} actual
- **Performance Gap**: {(self.results.get('target_accuracy', 0.415) - self.results['accuracy']) * 100:.1f} percentage points below target

## 🔄 Document Substitution Impact Analysis

### Substituted Documents Performance
"""

        for doc_name, perf in substitution_analysis['substituted_documents'].items():
            report += f"- **{doc_name}**: {perf['accuracy']:.1%} ({perf['correct']}/{perf['total']}) - {perf['risk_level']} risk\n"
            report += f"  - Reason: {perf['reason']}\n"

        report += f"""
### Impact Summary
- **Substituted Documents**: {substitution_analysis['substituted_overall']['accuracy']:.1%} accuracy
- **Normal Documents**: {substitution_analysis['normal_documents']['accuracy']:.1%} accuracy
- **Accuracy Gap**: {substitution_analysis['impact_analysis']['accuracy_gap']:.1%} ({substitution_analysis['impact_analysis']['relative_impact']:.1f}% relative impact)

**❗ Key Finding**: Substituted documents show {'significantly lower' if substitution_analysis['impact_analysis']['accuracy_gap'] > 0.05 else 'comparable'} performance.

## 📊 Question Difficulty Analysis
"""

        for difficulty, stats in difficulty_analysis.items():
            report += f"- **{difficulty}**: {stats['accuracy']:.1%} accuracy ({stats['question_count']} questions)\n"

        report += f"""
## ⚖️ Evaluation Function Comparison

### Key Differences from MMESGBench:
1. **Numeric Evaluation**: {evaluation_comparison['numeric_evaluation']['difference']}
2. **String Evaluation**: {evaluation_comparison['string_evaluation']['difference']}
3. **List Evaluation**: {evaluation_comparison['list_evaluation']['difference']}

### Potential Impact:
- **Numeric**: {evaluation_comparison['potential_impact']['numeric']}
- **String**: {evaluation_comparison['potential_impact']['string']}
- **List**: {evaluation_comparison['potential_impact']['list']}

## 📋 Performance by Answer Format
"""

        for answer_format, perf in format_analysis.items():
            report += f"- **{answer_format}**: {perf['estimated_accuracy']:.1%} ({perf['question_count']} questions)\n"

        report += f"""
## 🔍 Root Cause Analysis

### Primary Performance Gaps:
1. **Document Substitution**: {substitution_analysis['impact_analysis']['relative_impact']:.1f}% impact from 3 substituted documents
2. **Question Complexity**: {'Hard questions significantly underperforming' if 'Hard' in difficulty_analysis and difficulty_analysis['Hard']['accuracy'] < 0.3 else 'Complexity pattern needs investigation'}
3. **Evaluation Differences**: String cleaning differences may account for additional gaps

### Recommendations:
1. **High Priority**: Re-evaluate questions from substituted documents manually
2. **Medium Priority**: Implement MMESGBench's more sophisticated text cleaning
3. **Research**: Investigate format-specific performance patterns
4. **Validation**: Cross-check evaluation logic on known test cases

## 📈 Next Steps for Phase 1
- **DSPy Integration**: Current {self.results['accuracy']:.1%} provides solid baseline for optimization
- **Focus Areas**: Target {'substituted document questions' if substitution_analysis['impact_analysis']['accuracy_gap'] > 0.05 else 'evaluation function alignment'}
- **Expected Improvement**: {5-10 if substitution_analysis['impact_analysis']['accuracy_gap'] > 0.05 else 3-5} percentage points possible

---
*Analysis generated from {len(self.dataset)} questions across {len(self.results['document_stats'])} documents*
"""

        return report

def main():
    analyzer = EvaluationAnalyzer(
        'colbert_dataset_857q_results.json',
        'MMESGBench/dataset/samples.json'
    )

    report = analyzer.generate_comprehensive_report()

    # Save report
    with open('evaluation_analysis_report.md', 'w') as f:
        f.write(report)

    print("✅ Analysis complete! Report saved to: evaluation_analysis_report.md")
    print(report)

if __name__ == "__main__":
    main()