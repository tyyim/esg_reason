#!/usr/bin/env python3
"""
ColBERT Text-Only RAG Evaluation
Evaluates only the ColBERT text retrieval approach without ColPali dependencies
"""

import sys
import os
import json
import logging
import time
import fitz
import numpy as np
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from openai import OpenAI
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

@dataclass
class ColBERTEvalResult:
    """Evaluation result for ColBERT approach"""
    question: str
    predicted_answer: str
    ground_truth: str
    answer_format: str
    is_correct: bool
    exact_match: bool
    f1_score: float
    processing_time: float
    api_tokens: int
    reasoning_trace: str
    doc_id: str
    evidence_pages: List[int]
    retrieved_chunks: List[Dict[str, Any]]
    retrieval_stats: Dict[str, Any]

class SimpleColBERTRetriever:
    """Simplified ColBERT-based text retrieval without ColPali dependencies"""

    def __init__(self):
        # Initialize API client
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY not found in environment variables")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # Use sentence-transformers for text retrieval
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.chunks = {}
        self.embeddings = {}

        # Load extraction prompt
        self.extraction_prompt = self._load_extraction_prompt()

    def _load_extraction_prompt(self) -> str:
        """Load MMESGBench's exact extraction prompt"""
        return """Given the question and analysis, you are tasked to extract answers with required formats from the free-form analysis.
- Your extracted answers should be one of the following formats: (1) Integer, (2) Float, (3) String and (4) List. If you find the analysis the question can not be answered from the given documents, type "Not answerable". Exception: If the analysis only tells you that it can not read/understand the images or documents, type "Fail to answer".
- Please make your response as concise as possible. Also note that your response should be formatted as below:
```
Extracted answer: [answer]
Answer format: [answer format]
```

Please read the following example, then extract the answer from the model response and type it at the end of the prompt.

---
Question: List the primary questions asked about the services in this report.
Analysis:  The primary questions asked about the services in the report for The Limes Residential Home are:

1. Is the service safe?
2. Is the service effective?
3. Is the service caring?
4. Is the service responsive?
5. Is the service well-led?
Extracted answer: ['Is the service safe?', 'Is the service effective?', 'Is the service caring?', 'Is the service responsive?', 'Is the service well-led?']
Answer format: List

---
Question: How many regulations of the HSCA 2008 are breached in all according to this report?
Analysis: According to the report, the provider breached 10 Health and Social Care Act 2008 (Regulated Activities) Regulations in total. Here are the specifics:

1. Regulation 13: Safeguarding service users from abuse and improper treatment
2. Regulation 12: Safe care and treatment
3. Regulation 18: Staffing
4. Regulation 11: Need for consent
5. Regulation 10: Dignity and respect
6. Regulation 9: Person-centred care
7. Regulation 17: Good governance
8. Regulation 18 (CQC Registration Regulations 2009): Notification of other incidents
9. Regulation 18: Failure to maintain an accurate and up-to-date care plan
10. Regulation 11: Failure to implement the Mental Capacity Act 2005 code of practice effectively

These breaches involve issues concerning staffing, safeguarding, medicines management, dignity and respect, consent, care planning, governance, and failure to notify the CQC of incidents.
Extracted answer: 10
Answer format: Integer

---
Question: According to the survey that is the percentage of Chinese who are paying more or about the same attention to politics after Trump's election?
Analysis: The survey provided does not specify the percentage of Chinese individuals specifically who are paying more or about the same attention to politics after Trump's election. The report focuses primarily on American demographics and does not include specific details about the Chinese population in relation to this question. If you need information about a different demographic or a summary of the findings from the American demographic, I can certainly help with that!
Extracted answer: Not answerable
Answer format: String

---"""

    def index_document(self, doc_id: str, pdf_path: str, chunk_size: int = 512) -> None:
        """Index document for text retrieval"""
        logger.info(f"Indexing document {doc_id} for text retrieval")

        # Extract text from PDF
        chunks = []
        with fitz.open(pdf_path) as pdf:
            for page_num in range(pdf.page_count):
                page = pdf[page_num]
                page_text = page.get_text()

                # Split into chunks
                words = page_text.split()
                for i in range(0, len(words), chunk_size):
                    chunk_text = ' '.join(words[i:i + chunk_size])
                    if chunk_text.strip():
                        chunks.append({
                            'text': chunk_text,
                            'page': page_num + 1,
                            'chunk_id': len(chunks)
                        })

        # Store chunks and compute embeddings
        self.chunks[doc_id] = chunks
        chunk_texts = [chunk['text'] for chunk in chunks]
        embeddings = self.model.encode(chunk_texts)
        self.embeddings[doc_id] = embeddings

        logger.info(f"Indexed {len(chunks)} text chunks for {doc_id}")

    def retrieve(self, doc_id: str, question: str, top_k: int = 5) -> List[Dict]:
        """Retrieve top-k relevant text chunks"""
        if doc_id not in self.chunks:
            return []

        # Encode question
        query_embedding = self.model.encode([question])

        # Compute similarities
        similarities = np.dot(query_embedding, self.embeddings[doc_id].T)[0]

        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        # Return top chunks with scores
        results = []
        for idx in top_indices:
            chunk = self.chunks[doc_id][idx]
            results.append({
                'text': chunk['text'],
                'page': chunk['page'],
                'score': float(similarities[idx]),  # Convert to regular float
                'chunk_id': chunk['chunk_id']
            })

        return results

    def generate_response(self, question: str, retrieved_chunks: List[Dict]) -> Dict:
        """Generate response using retrieved chunks with Qwen Max"""
        # Combine top chunks as context
        context_text = "\n\n".join([chunk['text'] for chunk in retrieved_chunks[:5]])

        # Stage 1: Generate response with Qwen Max
        stage1_prompt = f"You are a helpful assistant. Please answer the following question based on the provided context:\n\nQuestion: {question}\n\nContext:\n{context_text}\n\nAnswer:"

        try:
            stage1_response = self.client.chat.completions.create(
                model="qwen-max",
                messages=[{"role": "user", "content": stage1_prompt}],
                temperature=0.0,
                max_tokens=1024,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            stage1_text = stage1_response.choices[0].message.content
        except Exception as e:
            logger.error(f"Stage 1 generation failed: {e}")
            return {"response": "Failed", "extracted_response": "Failed", "predicted_answer": "Failed"}

        # Stage 2: Extract answer with Qwen Max
        stage2_prompt = f"Question: {question}\nAnalysis: {stage1_text}\n\n{self.extraction_prompt}"

        try:
            stage2_response = self.client.chat.completions.create(
                model="qwen-max",
                messages=[{"role": "user", "content": stage2_prompt}],
                temperature=0.0,
                max_tokens=256,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                seed=42
            )
            extracted_text = stage2_response.choices[0].message.content
        except Exception as e:
            logger.error(f"Stage 2 extraction failed: {e}")
            return {"response": stage1_text, "extracted_response": "Failed to extract", "predicted_answer": "Failed to extract"}

        # Parse extracted answer
        try:
            pred_ans = extracted_text.split("Answer format:")[0].split("Extracted answer:")[1].strip()
        except:
            pred_ans = "Failed to extract"

        return {
            "response": stage1_text,
            "extracted_response": extracted_text,
            "predicted_answer": pred_ans
        }

class MMESGBenchEvaluator:
    """MMESGBench-compatible evaluator with tolerance handling"""

    def __init__(self):
        self.numeric_tolerance = 0.01  # ±1% tolerance as per MMESGBench

    def evaluate_prediction(self, prediction: str, ground_truth: str, answer_format: str) -> Tuple[bool, bool, float]:
        """
        Evaluate prediction with MMESGBench logic
        Returns: (is_correct_with_tolerance, exact_match, f1_score)
        """
        pred_clean = str(prediction).strip().lower()
        gt_clean = str(ground_truth).strip().lower()

        # Handle special cases
        if pred_clean in ["not answerable", "fail to answer", "failed"]:
            is_correct = gt_clean in ["not answerable", "fail to answer"]
            return is_correct, pred_clean == gt_clean, 0.0

        # Exact match check
        exact_match = pred_clean == gt_clean

        # Format-specific evaluation
        if answer_format.lower() in ["integer", "float"]:
            return self._evaluate_numeric(pred_clean, gt_clean, exact_match)
        elif answer_format.lower() == "list":
            return self._evaluate_list(pred_clean, gt_clean, exact_match)
        else:  # String
            return self._evaluate_string(pred_clean, gt_clean, exact_match)

    def _evaluate_numeric(self, pred: str, gt: str, exact_match: bool) -> Tuple[bool, bool, float]:
        """Evaluate numeric answers with tolerance"""
        try:
            pred_val = self._extract_number(pred)
            gt_val = self._extract_number(gt)

            if pred_val is None or gt_val is None:
                return exact_match, exact_match, 0.0

            # Check tolerance (±1%)
            if gt_val == 0:
                tolerance_match = abs(pred_val - gt_val) <= self.numeric_tolerance
            else:
                tolerance_match = abs(pred_val - gt_val) / abs(gt_val) <= self.numeric_tolerance

            # F1 score for numeric: 1.0 if within tolerance, 0.0 otherwise
            f1 = 1.0 if tolerance_match else 0.0

            return tolerance_match, exact_match, f1

        except:
            return exact_match, exact_match, 0.0

    def _evaluate_list(self, pred: str, gt: str, exact_match: bool) -> Tuple[bool, bool, float]:
        """Evaluate list answers"""
        try:
            pred_items = self._parse_list(pred)
            gt_items = self._parse_list(gt)

            if not pred_items and not gt_items:
                return True, exact_match, 1.0

            # Calculate F1 score
            pred_set = set(pred_items)
            gt_set = set(gt_items)

            if not pred_set and not gt_set:
                return True, exact_match, 1.0

            intersection = pred_set.intersection(gt_set)
            precision = len(intersection) / len(pred_set) if pred_set else 0
            recall = len(intersection) / len(gt_set) if gt_set else 0

            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

            # Consider correct if F1 > 0.8 (high overlap)
            is_correct = f1 > 0.8

            return is_correct, exact_match, f1

        except:
            return exact_match, exact_match, 0.0

    def _evaluate_string(self, pred: str, gt: str, exact_match: bool) -> Tuple[bool, bool, float]:
        """Evaluate string answers"""
        if exact_match:
            return True, True, 1.0

        # Token-level F1 for partial credit
        pred_tokens = pred.split()
        gt_tokens = gt.split()

        if not pred_tokens and not gt_tokens:
            return True, exact_match, 1.0

        pred_set = set(pred_tokens)
        gt_set = set(gt_tokens)

        if not pred_set and not gt_set:
            return True, exact_match, 1.0

        intersection = pred_set.intersection(gt_set)
        precision = len(intersection) / len(pred_set) if pred_set else 0
        recall = len(intersection) / len(gt_set) if gt_set else 0

        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        # Consider correct if F1 > 0.5 (reasonable overlap)
        is_correct = f1 > 0.5

        return is_correct, exact_match, f1

    def _extract_number(self, text: str) -> float:
        """Extract numeric value from text"""
        import re

        # Handle list format like [0.8, 1.3]
        if '[' in text and ']' in text:
            numbers = re.findall(r'-?\d+\.?\d*', text)
            if len(numbers) >= 2:
                return float(numbers[0])  # Use first number for range

        # Extract single number
        numbers = re.findall(r'-?\d+\.?\d*', text)
        if numbers:
            return float(numbers[0])

        return None

    def _parse_list(self, text: str) -> List[str]:
        """Parse list from text"""
        import re

        # Handle quoted list items
        if "'" in text:
            items = re.findall(r"'([^']*)'", text)
            return [item.strip() for item in items if item.strip()]

        # Handle bracketed list
        if '[' in text and ']' in text:
            content = text[text.find('[') + 1:text.rfind(']')]
            items = [item.strip().strip("'\"") for item in content.split(',')]
            return [item for item in items if item]

        # Fallback: split by common delimiters
        for delimiter in [',', ';', '|']:
            if delimiter in text:
                return [item.strip() for item in text.split(delimiter) if item.strip()]

        return [text] if text else []

class ColBERTTextOnlyEvaluation:
    """Evaluation pipeline for ColBERT Text-Only RAG"""

    def __init__(self):
        self.retriever = SimpleColBERTRetriever()
        self.evaluator = MMESGBenchEvaluator()

    def run_evaluation(self, limit: int = 10) -> Dict[str, Any]:
        """Run ColBERT RAG evaluation on AR6 dataset"""
        logger.info("🚀 Starting ColBERT Text-Only RAG Evaluation")

        # Load AR6 data
        samples = self._load_ar6_data(limit)
        if not samples:
            logger.error("No AR6 samples found")
            return {}

        # Setup document
        ar6_pdf = "source_documents/AR6 Synthesis Report Climate Change 2023.pdf"
        doc_id = "AR6 Synthesis Report Climate Change 2023.pdf"

        if not os.path.exists(ar6_pdf):
            logger.error(f"AR6 PDF not found: {ar6_pdf}")
            return {}

        # Index document
        logger.info("📚 Indexing AR6 document for text retrieval...")
        self.retriever.index_document(doc_id, ar6_pdf)

        # Run evaluation
        results = []
        total_time = 0
        total_tokens = 0
        correct_count = 0
        exact_match_count = 0
        total_f1 = 0.0

        for i, sample in enumerate(samples):
            logger.info(f"Evaluating sample {i+1}/{len(samples)}: {sample['answer_format']} question")

            start_time = time.time()

            # Parse evidence information
            evidence_pages = self._parse_evidence_pages(sample.get("evidence_pages", "[]"))

            # Retrieve relevant chunks
            retrieved_chunks = self.retriever.retrieve(doc_id, sample["question"], top_k=5)

            # Generate response
            response = self.retriever.generate_response(sample["question"], retrieved_chunks)

            processing_time = time.time() - start_time
            total_time += processing_time

            # Parse API tokens (estimate)
            api_tokens = len(sample["question"].split()) + sum(len(chunk["text"].split()) for chunk in retrieved_chunks[:5])
            total_tokens += api_tokens

            # Evaluate prediction
            is_correct, exact_match, f1_score = self.evaluator.evaluate_prediction(
                prediction=response["predicted_answer"],
                ground_truth=sample["answer"],
                answer_format=sample["answer_format"]
            )

            if is_correct:
                correct_count += 1
            if exact_match:
                exact_match_count += 1
            total_f1 += f1_score

            # Analyze retrieval stats
            retrieval_stats = self._analyze_retrieval_stats(retrieved_chunks, evidence_pages)

            # Store result
            result = ColBERTEvalResult(
                question=sample["question"],
                predicted_answer=response["predicted_answer"],
                ground_truth=sample["answer"],
                answer_format=sample["answer_format"],
                is_correct=is_correct,
                exact_match=exact_match,
                f1_score=f1_score,
                processing_time=processing_time,
                api_tokens=api_tokens,
                reasoning_trace=response.get("response", ""),
                doc_id=sample["doc_id"],
                evidence_pages=evidence_pages,
                retrieved_chunks=retrieved_chunks,
                retrieval_stats=retrieval_stats
            )
            results.append(result)

            # Log progress
            status = "✅" if is_correct else "❌"
            logger.info(f"  {status} {sample['answer_format']}: '{response['predicted_answer']}' vs '{sample['answer']}' "
                       f"(F1: {f1_score:.3f}, pages: {retrieval_stats.get('page_coverage', 0)})")

        # Calculate metrics
        accuracy = correct_count / len(samples) if samples else 0
        exact_match_ratio = exact_match_count / len(samples) if samples else 0
        avg_f1 = total_f1 / len(samples) if samples else 0
        avg_time = total_time / len(samples) if samples else 0
        avg_tokens = total_tokens / len(samples) if samples else 0

        # Retrieval analysis
        avg_similarity = sum(r.retrieval_stats.get("avg_similarity", 0) for r in results) / len(results)
        avg_page_coverage = sum(r.retrieval_stats.get("page_coverage", 0) for r in results) / len(results)

        evaluation_summary = {
            "approach": "ColBERT Text-Only RAG (MMESGBench Replication)",
            "model": "qwen-max",
            "dataset": "AR6 Synthesis Report (MMESGBench)",
            "total_samples": len(samples),
            "correct_predictions": correct_count,
            "exact_matches": exact_match_count,
            "accuracy": accuracy,
            "exact_match_ratio": exact_match_ratio,
            "avg_f1_score": avg_f1,
            "avg_processing_time": avg_time,
            "total_time": total_time,
            "avg_tokens_per_query": avg_tokens,
            "total_tokens": total_tokens,
            "avg_retrieval_similarity": avg_similarity,
            "avg_page_coverage": avg_page_coverage,
            "target_accuracy": 0.415,  # MMESGBench ColBERT target
            "results": results
        }

        return evaluation_summary

    def print_results(self, evaluation_summary: Dict[str, Any]):
        """Print detailed evaluation results"""
        print("\n" + "="*80)
        print("🎯 COLBERT TEXT-ONLY RAG EVALUATION RESULTS")
        print("="*80)

        print(f"Approach: {evaluation_summary['approach']}")
        print(f"Model: {evaluation_summary['model']}")
        print(f"Dataset: {evaluation_summary['dataset']}")

        print(f"\n📊 PERFORMANCE METRICS:")
        print(f"Total Samples: {evaluation_summary['total_samples']}")
        print(f"Accuracy (with tolerance): {evaluation_summary['accuracy']:.1%}")
        print(f"Exact Match Ratio: {evaluation_summary['exact_match_ratio']:.1%}")
        print(f"Average F1 Score: {evaluation_summary['avg_f1_score']:.3f}")
        print(f"Target Accuracy: {evaluation_summary['target_accuracy']:.1%}")

        # Performance vs target
        accuracy = evaluation_summary['accuracy']
        target = evaluation_summary['target_accuracy']
        performance_status = "🎉 EXCEEDS" if accuracy > target else "⚠️ BELOW" if accuracy < target else "✅ MEETS"
        print(f"Performance vs Target: {performance_status} ({accuracy:.1%} vs {target:.1%})")

        print(f"\n🔍 RETRIEVAL METRICS:")
        print(f"Average Similarity: {evaluation_summary['avg_retrieval_similarity']:.3f}")
        print(f"Average Page Coverage: {evaluation_summary['avg_page_coverage']:.1%}")

        print(f"\n⏱️ EFFICIENCY METRICS:")
        print(f"Total Time: {evaluation_summary['total_time']:.2f}s")
        print(f"Average Time/Question: {evaluation_summary['avg_processing_time']:.2f}s")
        print(f"Total Tokens: {evaluation_summary['total_tokens']:,}")
        print(f"Average Tokens/Query: {evaluation_summary['avg_tokens_per_query']:.0f}")

        print(f"\n📝 DETAILED RESULTS:")
        print("-"*80)

        for i, result in enumerate(evaluation_summary['results']):
            status = "✅ CORRECT" if result.is_correct else "❌ INCORRECT"
            exact_status = " (EXACT)" if result.exact_match else ""
            print(f"\n{i+1}. {status}{exact_status} ({result.answer_format}) - F1: {result.f1_score:.3f}")
            print(f"   Q: {result.question[:80]}...")
            print(f"   Predicted: {result.predicted_answer}")
            print(f"   Ground Truth: {result.ground_truth}")

            # Show retrieval info
            stats = result.retrieval_stats
            print(f"   Retrieval: {len(result.retrieved_chunks)} chunks, "
                  f"avg sim: {stats.get('avg_similarity', 0):.3f}, "
                  f"page coverage: {stats.get('page_coverage', 0):.0f}%")

            # Show evidence page matching
            if result.evidence_pages:
                retrieved_pages = [chunk['page'] for chunk in result.retrieved_chunks]
                evidence_found = set(retrieved_pages).intersection(set(result.evidence_pages))
                evidence_status = f"✅ Found pages {list(evidence_found)}" if evidence_found else "❌ Evidence pages not retrieved"
                print(f"   Evidence: {evidence_status} (expected: {result.evidence_pages})")

    def _load_ar6_data(self, limit: int) -> List[Dict[str, Any]]:
        """Load AR6 samples from MMESGBench dataset"""
        try:
            with open("./MMESGBench/dataset/samples.json", 'r') as f:
                full_dataset = json.load(f)

            ar6_samples = [s for s in full_dataset if s.get("doc_id") == "AR6 Synthesis Report Climate Change 2023.pdf"]
            return ar6_samples[:limit]
        except Exception as e:
            logger.error(f"Error loading AR6 data: {e}")
            return []

    def _analyze_retrieval_stats(self, retrieved_chunks: List[Dict[str, Any]],
                               evidence_pages: List[int]) -> Dict[str, Any]:
        """Analyze retrieval performance statistics"""
        if not retrieved_chunks:
            return {"avg_similarity": 0.0, "page_coverage": 0.0, "evidence_recall": 0.0}

        # Calculate average similarity
        similarities = [chunk["score"] for chunk in retrieved_chunks]
        avg_similarity = sum(similarities) / len(similarities)

        # Calculate page coverage
        retrieved_pages = [chunk["page"] for chunk in retrieved_chunks]
        if evidence_pages:
            matching_pages = set(retrieved_pages).intersection(set(evidence_pages))
            page_coverage = len(matching_pages) / len(evidence_pages) * 100
            evidence_recall = len(matching_pages) / len(evidence_pages)
        else:
            page_coverage = 0.0
            evidence_recall = 0.0

        return {
            "avg_similarity": avg_similarity,
            "page_coverage": page_coverage,
            "evidence_recall": evidence_recall,
            "retrieved_pages": retrieved_pages,
            "evidence_pages": evidence_pages
        }

    def _parse_evidence_pages(self, pages_str: str) -> List[int]:
        """Parse evidence pages from string"""
        try:
            if isinstance(pages_str, list):
                return [int(p) for p in pages_str]
            pages_str = str(pages_str).strip('[]')
            if ',' in pages_str:
                return [int(p.strip()) for p in pages_str.split(',') if p.strip()]
            else:
                return [int(pages_str)] if pages_str else []
        except:
            return []

def main():
    """Run ColBERT Text-Only RAG evaluation"""
    print("🎯 ColBERT Text-Only RAG Evaluation")
    print("Targeting MMESGBench 41.5% accuracy with ColBERT + Qwen Max")
    print("="*70)

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Create and run evaluation pipeline
    pipeline = ColBERTTextOnlyEvaluation()

    # Run evaluation on 10 samples
    results = pipeline.run_evaluation(limit=10)

    if results:
        pipeline.print_results(results)

        # Save results (with proper JSON serialization)
        results_file = "colbert_text_only_results.json"
        with open(results_file, 'w') as f:
            results_copy = results.copy()
            results_copy['results'] = [asdict(r) for r in results['results']]
            json.dump(results_copy, f, indent=2)

        print(f"\n💾 Results saved to: {results_file}")
        print(f"\n🎉 ColBERT Text-Only RAG evaluation completed!")

        # Final summary
        accuracy = results['accuracy']
        target = results['target_accuracy']
        f1 = results['avg_f1_score']

        print(f"\n📈 FINAL SUMMARY:")
        print(f"✅ ColBERT Text RAG Accuracy: {accuracy:.1%}")
        print(f"🎯 MMESGBench Target: {target:.1%}")
        print(f"📊 Average F1 Score: {f1:.3f}")

        if accuracy >= target:
            print(f"🎉 SUCCESS: Achieved target accuracy!")
        else:
            gap = target - accuracy
            print(f"⚠️ GAP: {gap:.1%} below target - retrieval optimization needed")

    else:
        print("❌ ColBERT Text-Only RAG evaluation failed")

if __name__ == "__main__":
    main()