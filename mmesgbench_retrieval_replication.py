#!/usr/bin/env python3
"""
MMESGBench Retrieval-Augmented Replication
Implementing both ColBERT (text) and ColPali (multimodal) RAG approaches
"""

import sys
import os
import json
import logging
import time
import fitz
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
from openai import OpenAI
from PIL import Image
from sentence_transformers import SentenceTransformer
from colpali_engine.models import ColQwen2, ColQwen2Processor
# Disabled flash attention for Apple Silicon compatibility
# from transformers.utils.import_utils import is_flash_attn_2_available
from uuid import uuid4

logger = logging.getLogger(__name__)

class MMESGBenchRetrievalReplicator:
    """Replicate MMESGBench's retrieval-augmented approaches"""

    def __init__(self, document_dir="./source_documents"):
        self.document_dir = document_dir

        # Initialize OpenAI client
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY not found in environment variables")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # Load extraction prompt
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

class ColBERTTextRetriever:
    """ColBERT-based text retrieval implementation"""

    def __init__(self, client):
        # Use sentence-transformers as ColBERT alternative for text retrieval
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.chunks = {}
        self.embeddings = {}
        self.client = client

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
                'score': similarities[idx],
                'chunk_id': chunk['chunk_id']
            })

        return results

    def generate_response(self, question: str, retrieved_chunks: List[Dict], extraction_prompt: str) -> Dict:
        """Generate response using retrieved chunks with Qwen Max (MMESGBench exact)"""
        # Combine top chunks as context
        context_text = "\n\n".join([chunk['text'] for chunk in retrieved_chunks[:5]])

        # Stage 1: Generate response with Qwen Max (MMESGBench Table 1)
        stage1_prompt = f"You are a helpful assistant. Please answer the following question based on the provided context:\n\nQuestion: {question}\n\nContext:\n{context_text}\n\nAnswer:"

        try:
            stage1_response = self.client.chat.completions.create(
                model="qwen-max",  # MMESGBench Table 1: ColBERT + Qwen Max
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
        stage2_prompt = f"Question: {question}\nAnalysis: {stage1_text}\n\n{extraction_prompt}"

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

class ColPaliVisualRetriever:
    """ColPali-based visual retrieval implementation (MMESGBench exact)"""

    def __init__(self, client):
        # Initialize ColPali model (Apple Silicon optimized)
        col_model_name = "vidore/colqwen2-v1.0"

        # Determine best device for Apple Silicon
        if torch.cuda.is_available():
            device_map = "cuda:0"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device_map = "mps"
        else:
            device_map = "cpu"

        logger.info(f"Using device: {device_map}")

        if device_map == "mps":
            # Apple Silicon optimized loading: CPU first, then move to MPS
            logger.info("Loading ColPali on CPU first, then moving to MPS...")
            self.col_model = ColQwen2.from_pretrained(
                col_model_name,
                torch_dtype=torch.float32,  # Use float32 for MPS compatibility
                device_map="cpu",  # Load on CPU first
            ).eval()

            # Move to MPS after loading
            logger.info("Moving ColPali model to MPS device...")
            self.col_model = self.col_model.to(torch.device("mps"))
        else:
            # Standard loading for CUDA/CPU
            self.col_model = ColQwen2.from_pretrained(
                col_model_name,
                torch_dtype=torch.bfloat16,
                device_map=device_map,
            ).eval()

        self.processor = ColQwen2Processor.from_pretrained(col_model_name, use_fast=True)

        self.image_paths = {}
        self.client = client

    def index_document(self, doc_id: str, pdf_path: str, max_pages: int = 120, resolution: int = 144) -> None:
        """Index document for visual retrieval (MMESGBench exact method)"""
        logger.info(f"Indexing document {doc_id} for visual retrieval")

        doc_name = Path(doc_id).stem
        tmp_dir = Path("./tmp")
        tmp_dir.mkdir(exist_ok=True)

        # Convert PDF to images (MMESGBench exact)
        images_paths = []
        with fitz.open(pdf_path) as pdf:
            num_pages = min(max_pages, pdf.page_count)
            for index in range(num_pages):
                page = pdf[index]
                tmp_path = tmp_dir / f"{doc_name}_{index+1}.png"

                if not tmp_path.exists():
                    pix = page.get_pixmap(dpi=resolution)
                    pix.save(str(tmp_path))

                images_paths.append(str(tmp_path))

        self.image_paths[doc_id] = images_paths
        logger.info(f"Created {len(images_paths)} page images for {doc_id}")

    def retrieve(self, doc_id: str, question: str, top_k: int = 5) -> Tuple[List[int], List[str], List[float]]:
        """Retrieve top-k relevant pages (MMESGBench exact method)"""
        if doc_id not in self.image_paths:
            return [], [], []

        images_paths = self.image_paths[doc_id]

        # MMESGBench exact retrieval logic
        query_input = self.processor.process_queries([question]).to(self.col_model.device)
        with torch.no_grad():
            query_embedding = self.col_model(**query_input)
            scores = []
            for img_path in images_paths:
                try:
                    pil_img = Image.open(img_path).convert("RGB")
                    image_input = self.processor.process_images([pil_img]).to(self.col_model.device)
                    with torch.no_grad():
                        image_embedding = self.col_model(**image_input)
                    score_matrix = self.processor.score_multi_vector(query_embedding, image_embedding)
                    score = score_matrix[0][0].item()
                    scores.append(score)
                except Exception as e:
                    logger.error(f"Error processing image {img_path}: {e}")
                    scores.append(float('-inf'))

        # Get top-k pages (MMESGBench exact)
        sorted_indices = np.argsort(scores)[::-1]
        top_k_0_based = sorted_indices[:top_k]
        top_k_pages = (top_k_0_based + 1).tolist()  # Convert to 1-based
        top_k_image_paths = [images_paths[i] for i in top_k_0_based]
        top_k_scores = [scores[i] for i in top_k_0_based]

        return top_k_pages, top_k_image_paths, top_k_scores

    def generate_response(self, question: str, retrieved_pages: Tuple[List[int], List[str], List[float]], extraction_prompt: str) -> Dict:
        """Generate response using retrieved pages with Qwen-VL Max (MMESGBench exact)"""
        pages, image_paths, scores = retrieved_pages

        if not image_paths:
            return {"response": "Failed", "extracted_response": "Failed", "predicted_answer": "Failed"}

        # Use top-5 images for multimodal generation
        top_images = image_paths[:5]

        # Create multimodal prompt with images
        images_content = []
        for img_path in top_images:
            images_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{self._encode_image(img_path)}"}
            })

        # Add text prompt (fixed format for Qwen-VL API)
        text_content = {
            "type": "text",
            "text": f"You are a helpful assistant. Please answer the following question based on the provided document pages:\n\nQuestion: {question}\n\nAnswer:"
        }

        messages = [{
            "role": "user",
            "content": [text_content] + images_content
        }]

        try:
            # Stage 1: Generate response with Qwen-VL Max (MMESGBench Table 1)
            stage1_response = self.client.chat.completions.create(
                model="qwen-vl-max",  # MMESGBench Table 1: ColPali + Qwen-VL Max
                messages=messages,
                temperature=0.0,
                max_tokens=1024,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            stage1_text = stage1_response.choices[0].message.content
        except Exception as e:
            logger.error(f"Stage 1 multimodal generation failed: {e}")
            return {"response": "Failed", "extracted_response": "Failed", "predicted_answer": "Failed"}

        # Stage 2: Extract answer with Qwen Max
        stage2_prompt = f"Question: {question}\nAnalysis: {stage1_text}\n\n{extraction_prompt}"

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

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API"""
        import base64
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

def main():
    """Main function to test both retrieval approaches"""
    print("🎯 MMESGBench Retrieval-Augmented Replication")
    print("Testing both ColBERT (text) and ColPali (multimodal) approaches")
    print("="*70)

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Test document
    test_pdf = "source_documents/AR6 Synthesis Report Climate Change 2023.pdf"
    doc_id = "AR6 Synthesis Report Climate Change 2023.pdf"

    if not os.path.exists(test_pdf):
        print(f"❌ Test PDF not found: {test_pdf}")
        return

    # Test question
    test_question = "According to the IPCC, which region had the highest per capita GHG emissions in 2019?"

    # Initialize replicator for API client
    replicator = MMESGBenchRetrievalReplicator()

    # Test ColBERT Text Retrieval
    print(f"\n📝 Testing ColBERT Text Retrieval (Qwen Max)")
    print("-" * 50)

    colbert_retriever = ColBERTTextRetriever(replicator.client)
    colbert_retriever.index_document(doc_id, test_pdf)
    text_results = colbert_retriever.retrieve(doc_id, test_question, top_k=5)

    print(f"Retrieved {len(text_results)} text chunks:")
    for i, result in enumerate(text_results):
        print(f"{i+1}. Page {result['page']} (Score: {result['score']:.3f})")
        print(f"   Text: {result['text'][:150]}...")

    # Test text generation
    print(f"\n🔄 Testing Text RAG Generation...")
    text_response = colbert_retriever.generate_response(test_question, text_results, replicator.extraction_prompt)
    print(f"Response: {text_response['response'][:200]}...")
    print(f"Predicted Answer: {text_response['predicted_answer']}")

    # Test ColPali Visual Retrieval
    device_available = torch.cuda.is_available() or (hasattr(torch.backends, 'mps') and torch.backends.mps.is_available())
    if device_available:
        print(f"\n🖼️  Testing ColPali Visual Retrieval (Qwen-VL Max)")
        print("-" * 50)

        colpali_retriever = ColPaliVisualRetriever(replicator.client)
        colpali_retriever.index_document(doc_id, test_pdf)
        pages, image_paths, scores = colpali_retriever.retrieve(doc_id, test_question, top_k=5)

        print(f"Retrieved {len(pages)} visual pages:")
        for i, (page, score) in enumerate(zip(pages, scores)):
            print(f"{i+1}. Page {page} (Score: {score:.3f})")

        # Test multimodal generation
        print(f"\n🔄 Testing Multimodal RAG Generation...")
        visual_response = colpali_retriever.generate_response(test_question, (pages, image_paths, scores), replicator.extraction_prompt)
        print(f"Response: {visual_response['response'][:200]}...")
        print(f"Predicted Answer: {visual_response['predicted_answer']}")
    else:
        print("\n⚠️  No GPU acceleration available (CUDA/MPS), skipping ColPali visual retrieval")

    print(f"\n✅ Retrieval approach testing completed!")

if __name__ == "__main__":
    main()