#!/usr/bin/env python3
"""
Run the MIPROv2 baseline module to generate predictions on dev set
"""
import json
import dspy
from src.database.vector_store import PostgresVectorStore
from dspy_implementation.dspy_signatures import ESGReasoning, AnswerExtraction

def main():
    print("Loading baseline module from MIPROv2 run...")

    # Load baseline module
    with open('dspy_implementation/optimized_modules/baseline_rag_20251012_023850.json', 'r') as f:
        module_data = json.load(f)

    # Configure DSPy
    from src.models.qwen_api import QwenAPIClient
    qwen_client = QwenAPIClient()
    qwen_lm = qwen_client.get_dspy_lm()
    dspy.settings.configure(lm=qwen_lm)

    # Initialize vector store
    vector_store = PostgresVectorStore(
        collection_name="MMESG",
        embedding_model="text-embedding-v4"
    )

    print("Creating baseline RAG module...")

    # Reconstruct baseline RAG module
    from dspy_implementation.dspy_rag import BaselineRAG
    baseline_rag = BaselineRAG(
        vector_store=vector_store,
        k=5
    )

    # Load the prompts from the saved module
    if 'reasoning_signature' in module_data:
        baseline_rag.reasoning.signature = module_data['reasoning_signature']
    if 'extraction_signature' in module_data:
        baseline_rag.extraction.signature = module_data['extraction_signature']

    print("Loading dev set...")
    with open('dspy_implementation/data_splits/dev_93.json', 'r') as f:
        dev_set = json.load(f)

    print(f"Generating predictions for {len(dev_set)} questions...")

    predictions = []
    for idx, example in enumerate(dev_set, 1):
        print(f"Processing {idx}/{len(dev_set)}: {example['question'][:60]}...")

        try:
            # Run baseline RAG
            result = baseline_rag(
                question=example['question'],
                doc_id=example['doc_id']
            )

            prediction = {
                'question': example['question'],
                'predicted_answer': result.extracted_answer,
                'ground_truth': example.get('answer'),
                'doc_id': example['doc_id'],
                'answer_format': example.get('answer_format'),
                'evidence_pages': example.get('evidence_pages', [])
            }
            predictions.append(prediction)

        except Exception as e:
            print(f"  Error: {e}")
            predictions.append({
                'question': example['question'],
                'predicted_answer': '',
                'ground_truth': example.get('answer'),
                'doc_id': example['doc_id'],
                'answer_format': example.get('answer_format'),
                'evidence_pages': example.get('evidence_pages', [])
            })

    # Save predictions
    with open('mipro_baseline_predictions.json', 'w') as f:
        json.dump(predictions, f, indent=2)

    print(f"\n✅ Saved predictions to: mipro_baseline_predictions.json")

    # Quick accuracy check
    correct = 0
    for pred, gold in zip(predictions, dev_set):
        if str(pred['predicted_answer']).lower().strip() == str(gold.get('answer', '')).lower().strip():
            correct += 1

    print(f"Quick accuracy: {correct}/{len(dev_set)} ({correct/len(dev_set)*100:.1f}%)")

if __name__ == '__main__':
    main()
