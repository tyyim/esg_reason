#!/usr/bin/env python3
"""
Extract questions from substituted documents for manual review
"""

import json

def extract_substituted_questions():
    """Extract questions from the 3 substituted documents"""

    # Load results
    with open('optimized_full_dataset_mmesgbench_rescored.json', 'r') as f:
        results = json.load(f)

    # Define substituted documents based on our analysis
    substituted_docs = [
        "Microsoft CDP Climate Change Response 2023.pdf",  # 2024->2023 version
        "ISO 14001.pdf",  # Various->Official standard
        "Gender 2024.pdf"  # UNESCO Gender->Education report
    ]

    print("🔍 Extracting questions from substituted documents...")

    substituted_questions = {}

    for result in results['detailed_results']:
        doc_id = result['doc_id']

        if doc_id in substituted_docs:
            if doc_id not in substituted_questions:
                substituted_questions[doc_id] = []

            substituted_questions[doc_id].append({
                'question': result['question'],
                'predicted_answer': result['predicted_answer'],
                'ground_truth': result['ground_truth'],
                'answer_format': result['answer_format'],
                'score': result['score'],
                'correct': result['score'] == 1.0
            })

    # Print summary
    print(f"\n📊 Summary of Substituted Document Questions:")
    total_questions = 0
    total_correct = 0

    for doc, questions in substituted_questions.items():
        correct = sum(1 for q in questions if q['correct'])
        total = len(questions)
        accuracy = correct / total * 100 if total > 0 else 0

        total_questions += total
        total_correct += correct

        print(f"\n📄 {doc}:")
        print(f"   Questions: {total}")
        print(f"   Correct: {correct}")
        print(f"   Accuracy: {accuracy:.1f}%")

        # Show risk level
        if "Gender" in doc:
            print(f"   Risk Level: HIGH (Education vs Gender domain shift)")
        elif "Microsoft" in doc:
            print(f"   Risk Level: LOW (2024 vs 2023 version)")
        elif "ISO" in doc:
            print(f"   Risk Level: LOW (Official vs third-party source)")

    overall_accuracy = total_correct / total_questions * 100 if total_questions > 0 else 0
    print(f"\n🎯 Overall Substituted Documents:")
    print(f"   Total Questions: {total_questions}")
    print(f"   Total Correct: {total_correct}")
    print(f"   Overall Accuracy: {overall_accuracy:.1f}%")

    # Save for Notion page creation
    with open('substituted_questions_for_review.json', 'w') as f:
        json.dump(substituted_questions, f, indent=2)

    print(f"\n✅ Questions saved to: substituted_questions_for_review.json")
    return substituted_questions

if __name__ == "__main__":
    extract_substituted_questions()