#!/usr/bin/env python3
"""
MMESGBench Replication using Markdown Files
Now using our converted markdown file to exactly match their approach
"""

import sys
import os
import json
import logging
import time
from typing import Dict, List, Any, Tuple
from openai import OpenAI

logger = logging.getLogger(__name__)


class MMESGBenchMarkdownReplicator:
    """Exact MMESGBench replication using markdown files like they do"""

    def __init__(self, markdown_dir="./MMESGBench_markdowns"):
        self.markdown_dir = markdown_dir

        # Initialize OpenAI client with exact MMESGBench settings
        import os
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY not found in environment variables")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # Load extraction prompt exactly as MMESGBench does
        self.extraction_prompt = self.load_extraction_prompt()

    def load_extraction_prompt(self) -> str:
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

---
Question: How many quotations from male respondent over 50 years old are included in this report?
Analysis: The image you've provided appears to be a screenshot of a document with multiple charts. However, the text is too small and blurry to read accurately. If you can provide a clearer image or more context, I might be able to help you with your question.
Extracted answer: Fail to answer
Answer format: String

---"""

    def load_md_chunks(self, md_path: str, chunk_size: int = 60) -> List[str]:
        """
        MMESGBench's EXACT chunk loading function
        Replicated from their llm.py line 31-35
        """
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        chunks = ["".join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size)]
        return chunks

    def get_response_basic(self, question: str, context: str,
                          max_new_tokens: int = 1024, temperature: float = 0.0) -> str:
        """
        Stage 1: Generate response using MMESGBench's basic prompt
        """
        # MMESGBench basic prompt (from Mixtral/ChatGLM models)
        prompt = f"""You are a helpful assistant. Answer the following question based on the context provided.

Context:
{context}

Question: {question}
Answer:"""

        try:
            response = self.client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_new_tokens
            )

            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                return "Failed"

        except Exception as e:
            logger.error(f"Error in Stage 1 response: {e}")
            return "Failed"

    def extract_answer(self, question: str, analysis: str) -> str:
        """
        Stage 2: Extract structured answer using MMESGBench's exact method
        """
        try:
            response = self.client.chat.completions.create(
                model="qwen-max",
                messages=[
                    {
                        "role": "user",
                        "content": self.extraction_prompt,
                    },
                    {
                        "role": "assistant",
                        "content": f"\n\nQuestion:{question}\nAnalysis:{analysis}\n"
                    }
                ],
                temperature=0.0,
                max_tokens=256,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                seed=42
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in answer extraction: {e}")
            return "Failed to extract"

    def parse_extracted_answer(self, extracted_response: str) -> Tuple[str, float]:
        """Parse the structured extraction response exactly like MMESGBench"""
        try:
            pred_ans = extracted_response.split("Answer format:")[0].split("Extracted answer:")[1].strip()
            return pred_ans, 1.0
        except:
            return "Failed to extract", 0.0

    def run_markdown_based_evaluation(self, samples: List[Dict],
                                     chunk_size: int = 60,
                                     max_tokens: int = 1024,
                                     temperature: float = 0.0) -> List[Dict]:
        """
        Run evaluation exactly following MMESGBench's llm.py methodology
        Using markdown files like they do
        """
        logger.info("🎯 Running MMESGBench Markdown-Based Replication")

        results = []

        for i, sample in enumerate(samples):
            logger.info(f"Processing sample {i+1}/{len(samples)}: {sample.get('answer_format', 'Unknown')} question")

            # Load markdown file exactly like MMESGBench does
            md_path = os.path.join(self.markdown_dir, sample["doc_id"].replace(".pdf", ".md"))

            if not os.path.exists(md_path):
                logger.error(f"Markdown file not found: {md_path}")
                continue

            # Load chunks using their exact function
            chunks = self.load_md_chunks(md_path, chunk_size)
            logger.info(f"Loaded {len(chunks)} chunks from {md_path}")

            # Stage 1: Sequential chunk processing until success (their exact approach)
            response = "Failed"
            for chunk_idx, chunk in enumerate(chunks):
                response = self.get_response_basic(
                    question=sample["question"],
                    context=chunk,
                    max_new_tokens=max_tokens,
                    temperature=temperature
                )
                if response != "Failed":
                    logger.info(f"Success on chunk {chunk_idx+1}/{len(chunks)}")
                    break

            # Stage 2: Answer extraction (their exact method)
            extracted_response = self.extract_answer(sample["question"], response)

            # Parse extracted answer (their exact parsing)
            pred_ans, confidence = self.parse_extracted_answer(extracted_response)

            # Evaluate using simple scoring
            try:
                # Simple exact match for now
                if pred_ans.lower().strip() == sample["answer"].lower().strip():
                    score = 1.0
                elif pred_ans == "Not answerable" or pred_ans == "Fail to answer":
                    score = 0.0
                else:
                    # Try basic matching
                    if sample["answer"] in pred_ans or pred_ans in sample["answer"]:
                        score = 1.0
                    else:
                        score = 0.0
            except:
                score = 0.0

            result = {
                "question": sample["question"],
                "response": response,
                "extracted_response": extracted_response,
                "predicted_answer": pred_ans,
                "ground_truth": sample["answer"],
                "answer_format": sample["answer_format"],
                "score": score,
                "doc_id": sample["doc_id"],
                "evidence_pages": sample.get("evidence_pages", []),
                "confidence": confidence,
                "successful_chunk": chunk_idx if response != "Failed" else -1
            }

            results.append(result)

            # Log progress
            status = "✅" if score > 0.5 else "❌"
            logger.info(f"  {status} {sample['answer_format']}: '{pred_ans}' vs '{sample['answer']}' (score: {score:.2f})")

        return results

    def print_markdown_results(self, results: List[Dict]):
        """Print results showing markdown-based processing"""
        correct = sum(1 for r in results if r['score'] > 0.5)
        total = len(results)
        accuracy = correct / total if total > 0 else 0

        print("\n" + "="*80)
        print("🎯 MMESGBENCH MARKDOWN-BASED REPLICATION RESULTS")
        print("="*80)

        print(f"Using MMESGBench-compatible markdown files")
        print(f"Total Samples: {total}")
        print(f"Correct Predictions: {correct}")
        print(f"Accuracy: {accuracy:.2%}")

        print(f"\n📝 DETAILED RESULTS:")
        print("-"*80)

        for i, result in enumerate(results):
            status = "✅ CORRECT" if result['score'] > 0.5 else "❌ INCORRECT"
            print(f"\n{i+1}. {status} ({result['answer_format']})")
            print(f"   Q: {result['question'][:80]}...")
            print(f"   Successful chunk: {result['successful_chunk']+1 if result['successful_chunk'] >= 0 else 'None'}")
            print(f"   Analysis: {result['response'][:100]}...")
            print(f"   Extraction: {result['extracted_response'][:100]}...")
            print(f"   Predicted: {result['predicted_answer']}")
            print(f"   Ground Truth: {result['ground_truth']}")
            print(f"   Score: {result['score']:.2f}")


def main():
    """Main function to run markdown-based MMESGBench replication"""
    print("🎯 MMESGBench Markdown-Based Exact Replication")
    print("Using our converted markdown files like MMESGBench does")
    print("="*70)

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Load AR6 samples
    try:
        with open("./MMESGBench/dataset/samples.json", 'r') as f:
            full_dataset = json.load(f)

        ar6_samples = [s for s in full_dataset if s.get("doc_id") == "AR6 Synthesis Report Climate Change 2023.pdf"]
        samples = ar6_samples[:10]

        print(f"Loaded {len(samples)} AR6 samples for markdown-based replication")

    except Exception as e:
        print(f"❌ Error loading samples: {e}")
        return

    # Run markdown-based replication
    replicator = MMESGBenchMarkdownReplicator()

    # MMESGBench exact parameters
    results = replicator.run_markdown_based_evaluation(
        samples=samples,
        chunk_size=60,        # Their exact chunk size
        max_tokens=1024,      # Their exact max_tokens
        temperature=0.0       # Their exact temperature
    )

    # Print results
    replicator.print_markdown_results(results)

    # Save results
    output_file = "mmesgbench_markdown_replication_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "methodology": "markdown_based_mmesgbench_replication",
            "markdown_dir": "./MMESGBench_markdowns",
            "parameters": {
                "chunk_size": 60,
                "max_tokens": 1024,
                "temperature": 0.0,
                "stage1_model": "qwen-plus",
                "stage2_model": "qwen-max",
                "extraction_seed": 42
            },
            "results": results
        }, f, indent=2)

    print(f"\n💾 Markdown-based replication results saved to: {output_file}")
    print("🎉 MMESGBench markdown-based replication completed!")


if __name__ == "__main__":
    main()