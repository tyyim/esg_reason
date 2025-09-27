#!/usr/bin/env python3
"""
Autonomous ColBERT Evaluator
Timeout-free evaluation system with parallel API processing and automatic batch management.
Designed to run independently without Bash tool timeouts.
"""

import asyncio
import aiohttp
import json
import logging
import time
import fitz
import numpy as np
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import signal
import sys
import os
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('autonomous_evaluation.log'),
        logging.StreamHandler()
    ]
)
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
    question_id: int

class AutonomousColBERTEvaluator:
    """Autonomous evaluation system with parallel processing and no timeout dependencies"""

    def __init__(self, api_key: str, batch_size: int = 25, max_parallel: int = 8):
        self.api_key = api_key
        self.batch_size = batch_size
        self.max_parallel = max_parallel
        self.session = None
        self.semaphore = asyncio.Semaphore(max_parallel)

        # Initialize sentence transformer
        logger.info("Loading SentenceTransformer model...")
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        logger.info("Model loaded successfully")

        # Document storage
        self.chunks = {}  # doc_id -> chunks
        self.embeddings = {}  # doc_id -> embeddings

        # Progress tracking
        self.start_time = None
        self.total_questions = 0
        self.completed_questions = 0

        # System prompts
        self.system_prompt = "You are a helpful assistant specializing in ESG and climate finance analysis."
        self.extraction_prompt = """
Please extract the exact answer from the analysis above.

Instructions:
- Your extracted answers should be one of the following formats: (1) Integer, (2) Float, (3) String and (4) List. If you find the analysis the question can not be answered from the given documents, type "Not answerable". Exception: If the analysis only tells you that it can not read/understand the images or documents, type "Fail to answer".
- Please make your response as concise as possible. Also note that your response should be formatted as below:

```
Extracted answer: [Your answer here]
Answer format: [Integer/Float/String/List/Not answerable]
```
"""

    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
        timeout = aiohttp.ClientTimeout(total=120)  # 2 minute timeout per request
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def load_dataset(self, dataset_path: str = "./MMESGBench/dataset/samples.json") -> List[Dict]:
        """Load the MMESGBench dataset"""
        try:
            with open(dataset_path, 'r') as f:
                data = json.load(f)

            # Convert to list format
            samples = []
            for sample_id, sample_data in data.items():
                sample_data['sample_id'] = sample_id
                samples.append(sample_data)

            logger.info(f"Loaded {len(samples)} questions from {len(set(s['doc_id'] for s in samples))} documents")
            return samples

        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            return []

    def find_document_path(self, doc_id: str) -> str:
        """Find the full path to a document"""
        base_paths = [
            "./source_documents/",
            "./downloaded_documents/",
            "./documents/",
            "./"
        ]

        for base_path in base_paths:
            full_path = Path(base_path) / doc_id
            if full_path.exists():
                return str(full_path)

        # Log error but don't crash - return empty path
        logger.error(f"Document not found: {doc_id}")
        return ""

    def index_document(self, doc_id: str) -> bool:
        """Index a document for retrieval (lazy loading)"""
        if doc_id in self.chunks:
            return True

        doc_path = self.find_document_path(doc_id)
        if not doc_path:
            return False

        try:
            # Extract text from PDF
            chunks = []
            doc = fitz.open(doc_path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()

                # Split into smaller chunks (roughly 200 words each)
                words = text.split()
                chunk_size = 200

                for i in range(0, len(words), chunk_size):
                    chunk_words = words[i:i + chunk_size]
                    chunk_text = ' '.join(chunk_words)

                    if len(chunk_text.strip()) > 50:  # Only keep substantial chunks
                        chunks.append({
                            'text': chunk_text,
                            'page': page_num + 1,
                            'chunk_id': len(chunks)
                        })

            doc.close()

            if not chunks:
                logger.warning(f"No chunks extracted from {doc_id}")
                return False

            # Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks from {doc_id}")
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = self.model.encode(chunk_texts, convert_to_tensor=True, show_progress_bar=False)

            # Store
            self.chunks[doc_id] = chunks
            self.embeddings[doc_id] = embeddings

            logger.info(f"Indexed {len(chunks)} text chunks for {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to index {doc_id}: {e}")
            return False

    def retrieve_chunks(self, question: str, doc_id: str, top_k: int = 5) -> List[Dict]:
        """Retrieve top-k most similar chunks for a question"""
        if doc_id not in self.chunks:
            if not self.index_document(doc_id):
                return []

        # Generate question embedding
        question_embedding = self.model.encode([question], convert_to_tensor=True)

        # Calculate similarities
        doc_embeddings = self.embeddings[doc_id]
        similarities = np.dot(question_embedding.cpu().numpy(), doc_embeddings.cpu().numpy().T)[0]

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # Return top chunks with similarity scores
        retrieved_chunks = []
        for idx in top_indices:
            chunk = self.chunks[doc_id][idx].copy()
            chunk['similarity'] = float(similarities[idx])
            retrieved_chunks.append(chunk)

        return retrieved_chunks

    async def generate_response_async(self, question: str, context_chunks: List[Dict]) -> Dict[str, Any]:
        """Generate response using Qwen API with async processing and retries"""

        # Prepare context
        context_text = "\n\n".join([
            f"Page {chunk['page']}: {chunk['text']}"
            for chunk in context_chunks
        ])

        # Stage 1: Generate comprehensive response
        stage1_prompt = f"You are a helpful assistant. Please answer the following question based on the provided context:\n\nQuestion: {question}\n\nContext:\n{context_text}\n\nAnswer:"

        # Retry logic for Stage 1
        stage1_text = None
        for attempt in range(3):
            try:
                async with self.semaphore:  # Limit concurrent requests
                    stage1_text = await self._make_api_request(stage1_prompt, max_tokens=1024)
                    break
            except Exception as e:
                logger.warning(f"Stage 1 attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    logger.error(f"Stage 1 failed after 3 attempts: {e}")
                    return {"response": "Failed", "extracted_response": "Failed", "predicted_answer": "Failed"}
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # Stage 2: Extract answer
        stage2_prompt = f"Question: {question}\nAnalysis: {stage1_text}\n\n{self.extraction_prompt}"

        # Retry logic for Stage 2
        extracted_text = None
        for attempt in range(3):
            try:
                async with self.semaphore:  # Limit concurrent requests
                    extracted_text = await self._make_api_request(stage2_prompt, max_tokens=256)
                    break
            except Exception as e:
                logger.warning(f"Stage 2 attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    logger.error(f"Stage 2 failed after 3 attempts: {e}")
                    return {"response": stage1_text, "extracted_response": "Failed to extract", "predicted_answer": "Failed to extract"}
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

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

    async def _make_api_request(self, prompt: str, max_tokens: int = 1024) -> str:
        """Make async API request to Qwen with proper error handling"""
        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

        payload = {
            "model": "qwen-max",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": max_tokens,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                return result['choices'][0]['message']['content']
            else:
                error_text = await response.text()
                raise Exception(f"API request failed with status {response.status}: {error_text}")

    def calculate_metrics(self, predicted: str, ground_truth: str, answer_format: str) -> Tuple[bool, bool, float]:
        """Calculate evaluation metrics (is_correct, exact_match, f1_score)"""
        # Basic exact match
        exact_match = predicted.strip().lower() == ground_truth.strip().lower()

        if answer_format in ["Integer", "Float"]:
            # Numeric comparison with tolerance
            try:
                pred_val = self._extract_number(predicted)
                gt_val = self._extract_number(ground_truth)

                if pred_val is None or gt_val is None:
                    return exact_match, exact_match, 0.0

                # ±1% tolerance for numeric values
                tolerance = abs(gt_val) * 0.01 if gt_val != 0 else 0.01
                is_correct = abs(pred_val - gt_val) <= tolerance
                f1_score = 1.0 if is_correct else 0.0

                return is_correct, exact_match, f1_score

            except:
                return exact_match, exact_match, 0.0

        elif answer_format == "List":
            # List comparison with F1 scoring
            try:
                pred_items = self._parse_list(predicted)
                gt_items = self._parse_list(ground_truth)

                if not pred_items and not gt_items:
                    return True, exact_match, 1.0

                if not pred_items or not gt_items:
                    return exact_match, exact_match, 0.0

                # Calculate F1 score for lists
                pred_set = set([item.lower().strip() for item in pred_items])
                gt_set = set([item.lower().strip() for item in gt_items])

                intersection = pred_set.intersection(gt_set)

                if len(pred_set) == 0:
                    precision = 0.0
                else:
                    precision = len(intersection) / len(pred_set)

                if len(gt_set) == 0:
                    recall = 0.0
                else:
                    recall = len(intersection) / len(gt_set)

                if precision + recall == 0:
                    f1_score = 0.0
                else:
                    f1_score = 2 * (precision * recall) / (precision + recall)

                is_correct = f1_score > 0.5  # Consider correct if F1 > 0.5

                return is_correct, exact_match, f1_score

            except:
                return exact_match, exact_match, 0.0

        else:
            # String comparison
            is_correct = exact_match
            f1_score = 1.0 if exact_match else 0.0
            return is_correct, exact_match, f1_score

    def _extract_number(self, text: str) -> float:
        """Extract numeric value from text"""
        import re
        # Remove common non-numeric characters and extract number
        cleaned = re.sub(r'[^\d.-]', '', text.strip())
        try:
            return float(cleaned)
        except:
            return None

    def _parse_list(self, text: str) -> List[str]:
        """Parse list from text representation"""
        import re
        # Handle various list formats
        text = text.strip()

        if text.startswith('[') and text.endswith(']'):
            # JSON-like list
            try:
                import ast
                return ast.literal_eval(text)
            except:
                # Fallback to manual parsing
                content = text[1:-1]
                items = [item.strip().strip('"').strip("'") for item in content.split(',')]
                return [item for item in items if item]

        # Try splitting by common delimiters
        for delimiter in [',', ';', '\n']:
            if delimiter in text:
                items = [item.strip() for item in text.split(delimiter)]
                return [item for item in items if item]

        # Single item
        return [text] if text else []

    async def evaluate_question_async(self, sample: Dict) -> ColBERTEvalResult:
        """Evaluate a single question asynchronously"""
        start_time = time.time()

        question = sample['question']
        ground_truth = sample['answer']
        answer_format = sample['answer_format']
        doc_id = sample['doc_id']
        question_id = sample.get('sample_id', 0)

        # Retrieve relevant chunks
        retrieved_chunks = self.retrieve_chunks(question, doc_id, top_k=5)

        if not retrieved_chunks:
            logger.warning(f"No chunks retrieved for question {question_id}")
            # Create failed result
            return ColBERTEvalResult(
                question=question,
                predicted_answer="No chunks retrieved",
                ground_truth=str(ground_truth),
                answer_format=answer_format,
                is_correct=False,
                exact_match=False,
                f1_score=0.0,
                processing_time=time.time() - start_time,
                api_tokens=0,
                reasoning_trace="No chunks retrieved",
                doc_id=doc_id,
                evidence_pages=[],
                retrieved_chunks=[],
                retrieval_stats={"similarity": 0.0, "num_chunks": 0},
                question_id=question_id
            )

        # Generate response
        response_data = await self.generate_response_async(question, retrieved_chunks)
        predicted_answer = response_data["predicted_answer"]

        # Calculate metrics
        is_correct, exact_match, f1_score = self.calculate_metrics(
            predicted_answer, str(ground_truth), answer_format
        )

        # Extract evidence pages
        evidence_pages = list(set([chunk['page'] for chunk in retrieved_chunks]))

        # Calculate retrieval stats
        similarities = [chunk['similarity'] for chunk in retrieved_chunks]
        retrieval_stats = {
            "similarity": np.mean(similarities) if similarities else 0.0,
            "num_chunks": len(retrieved_chunks)
        }

        processing_time = time.time() - start_time

        return ColBERTEvalResult(
            question=question,
            predicted_answer=predicted_answer,
            ground_truth=str(ground_truth),
            answer_format=answer_format,
            is_correct=is_correct,
            exact_match=exact_match,
            f1_score=f1_score,
            processing_time=processing_time,
            api_tokens=len(response_data["response"].split()) + len(response_data["extracted_response"].split()),  # Rough estimate
            reasoning_trace=response_data["response"],
            doc_id=doc_id,
            evidence_pages=evidence_pages,
            retrieved_chunks=retrieved_chunks,
            retrieval_stats=retrieval_stats,
            question_id=question_id
        )

    async def process_batch_async(self, batch: List[Dict]) -> List[ColBERTEvalResult]:
        """Process a batch of questions in parallel"""
        logger.info(f"Processing batch of {len(batch)} questions...")

        # Create tasks for parallel execution
        tasks = [self.evaluate_question_async(sample) for sample in batch]

        # Execute with progress tracking
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)

            # Update progress
            self.completed_questions += 1
            if self.completed_questions % 5 == 0:  # Log every 5 questions
                elapsed = time.time() - self.start_time
                rate = self.completed_questions / elapsed
                eta = (self.total_questions - self.completed_questions) / rate if rate > 0 else 0

                logger.info(f"Progress: {self.completed_questions}/{self.total_questions} "
                           f"({self.completed_questions/self.total_questions*100:.1f}%) "
                           f"Rate: {rate:.2f} q/s, ETA: {timedelta(seconds=int(eta))}")

        return results

    def save_checkpoint(self, results: List[ColBERTEvalResult], checkpoint_file: str):
        """Save evaluation checkpoint"""
        try:
            checkpoint_data = {
                "completed_questions": len(results),
                "total_questions": self.total_questions,
                "results": [asdict(result) for result in results],
                "timestamp": datetime.now().isoformat(),
                "approach": "Autonomous ColBERT"
            }

            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

            logger.info(f"Checkpoint saved: {len(results)}/{self.total_questions} questions")

        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")

    def load_checkpoint(self, checkpoint_file: str) -> Tuple[List[ColBERTEvalResult], int]:
        """Load evaluation checkpoint"""
        if not os.path.exists(checkpoint_file):
            return [], 0

        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)

            results = []
            for result_dict in checkpoint_data.get("results", []):
                # Convert dict back to ColBERTEvalResult dataclass
                results.append(ColBERTEvalResult(**result_dict))

            completed_idx = checkpoint_data.get("completed_questions", 0)
            logger.info(f"Loaded checkpoint: {completed_idx} questions completed")
            return results, completed_idx

        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return [], 0

    async def run_autonomous_evaluation(self,
                                       dataset_path: str = "./MMESGBench/dataset/samples.json",
                                       checkpoint_file: str = "autonomous_colbert_checkpoint.json",
                                       results_file: str = "autonomous_colbert_results.json") -> Dict[str, Any]:
        """Run autonomous evaluation with parallel processing and batch management"""

        logger.info("🚀 Starting Autonomous ColBERT Evaluation")
        self.start_time = time.time()

        # Load dataset
        samples = self.load_dataset(dataset_path)
        if not samples:
            logger.error("Failed to load dataset")
            return {}

        self.total_questions = len(samples)
        logger.info(f"📊 Loaded {len(samples)} questions from {len(set(s['doc_id'] for s in samples))} documents")

        # Load checkpoint if exists
        results, start_idx = self.load_checkpoint(checkpoint_file)

        if start_idx >= len(samples):
            logger.info("✅ All questions already completed!")
            return self._compile_final_results(results)

        if start_idx > 0:
            logger.info(f"📂 Resuming from question {start_idx + 1}/{len(samples)}")
            self.completed_questions = start_idx

        # Process remaining questions in batches
        remaining_samples = samples[start_idx:]

        try:
            for batch_start in range(0, len(remaining_samples), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(remaining_samples))
                batch = remaining_samples[batch_start:batch_end]

                logger.info(f"📦 Processing batch {batch_start // self.batch_size + 1}: "
                           f"questions {start_idx + batch_start + 1}-{start_idx + batch_end}")

                # Process batch asynchronously
                batch_results = await self.process_batch_async(batch)
                results.extend(batch_results)

                # Save checkpoint after each batch
                self.save_checkpoint(results, checkpoint_file)

                # Brief pause between batches to be respectful to API
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("🛑 Evaluation interrupted by user")
            self.save_checkpoint(results, checkpoint_file)
            return self._compile_final_results(results)

        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}")
            self.save_checkpoint(results, checkpoint_file)
            raise

        # Final checkpoint and results
        self.save_checkpoint(results, checkpoint_file)
        final_results = self._compile_final_results(results)

        # Save final results
        with open(results_file, 'w') as f:
            json.dump(final_results, f, indent=2)

        logger.info(f"💾 Results saved to: {results_file}")
        logger.info("🎉 Autonomous ColBERT evaluation completed!")

        return final_results

    def _compile_final_results(self, results: List[ColBERTEvalResult]) -> Dict[str, Any]:
        """Compile final results and statistics"""
        if not results:
            return {}

        # Calculate overall metrics
        total_samples = len(results)
        correct_samples = sum(1 for r in results if r.is_correct)
        exact_matches = sum(1 for r in results if r.exact_match)

        accuracy = correct_samples / total_samples if total_samples > 0 else 0.0
        exact_match_ratio = exact_matches / total_samples if total_samples > 0 else 0.0
        avg_f1 = np.mean([r.f1_score for r in results])

        # Calculate timing and efficiency
        total_time = sum(r.processing_time for r in results)
        avg_time = total_time / total_samples if total_samples > 0 else 0.0
        total_tokens = sum(r.api_tokens for r in results)
        avg_tokens = total_tokens / total_samples if total_samples > 0 else 0.0

        # Calculate retrieval metrics
        avg_similarity = np.mean([r.retrieval_stats.get('similarity', 0) for r in results])

        # Document-level performance
        doc_performance = {}
        for result in results:
            doc_id = result.doc_id
            if doc_id not in doc_performance:
                doc_performance[doc_id] = {"correct": 0, "total": 0}
            doc_performance[doc_id]["total"] += 1
            if result.is_correct:
                doc_performance[doc_id]["correct"] += 1

        # Sort documents by performance
        doc_stats = []
        for doc_id, stats in doc_performance.items():
            accuracy_pct = stats["correct"] / stats["total"] * 100
            doc_stats.append({
                "document": doc_id,
                "accuracy": accuracy_pct,
                "correct": stats["correct"],
                "total": stats["total"]
            })
        doc_stats.sort(key=lambda x: x["accuracy"], reverse=True)

        return {
            "approach": "Autonomous ColBERT with Parallel Processing",
            "model": "qwen-max",
            "dataset": "MMESGBench Full Dataset",
            "performance_metrics": {
                "total_samples": total_samples,
                "accuracy": accuracy,
                "exact_match_ratio": exact_match_ratio,
                "avg_f1_score": avg_f1,
                "target_accuracy": 0.415,
                "performance_vs_target": "ABOVE" if accuracy >= 0.415 else "BELOW"
            },
            "retrieval_metrics": {
                "avg_similarity": avg_similarity
            },
            "efficiency_metrics": {
                "total_time_seconds": total_time,
                "avg_time_per_question": avg_time,
                "total_tokens": total_tokens,
                "avg_tokens_per_query": avg_tokens
            },
            "document_performance": {
                "documents_processed": len(doc_performance),
                "top_5_performing": doc_stats[:5],
                "bottom_5_performing": doc_stats[-5:] if len(doc_stats) > 5 else []
            },
            "detailed_results": [asdict(result) for result in results]
        }

def signal_handler(signum, frame):
    """Handle graceful shutdown"""
    logger.info("🛑 Received shutdown signal, saving progress...")
    sys.exit(0)

async def main():
    """Main execution function"""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Configuration
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error("DASHSCOPE_API_KEY environment variable not found")
        return

    # Set environment variables for optimal performance
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    # Create evaluator
    evaluator = AutonomousColBERTEvaluator(
        api_key=api_key,
        batch_size=25,  # Process 25 questions per batch
        max_parallel=8  # 8 parallel API calls
    )

    # Run evaluation
    async with evaluator:
        results = await evaluator.run_autonomous_evaluation()

        if results:
            # Print summary
            metrics = results["performance_metrics"]
            efficiency = results["efficiency_metrics"]

            print("\n" + "="*80)
            print("🎯 AUTONOMOUS COLBERT EVALUATION RESULTS")
            print("="*80)
            print(f"📊 Accuracy: {metrics['accuracy']:.1%} ({metrics['total_samples']} questions)")
            print(f"🎯 Target: {metrics['target_accuracy']:.1%}")
            print(f"📈 Status: {metrics['performance_vs_target']}")
            print(f"⏱️  Total Time: {efficiency['total_time_seconds']:.1f}s")
            print(f"🚀 Average Speed: {efficiency['avg_time_per_question']:.2f}s per question")
            print(f"🔢 Total Tokens: {efficiency['total_tokens']:,}")
            print("✅ Evaluation completed successfully!")
            print("="*80)

if __name__ == "__main__":
    asyncio.run(main())