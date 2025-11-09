"""
DC + RAG Integration for MMESGBench
Combines PostgreSQL retrieval with Dynamic Cheatsheet test-time learning
Does NOT use DSPy framework - this is pure DC implementation
"""
import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dspy_implementation.dspy_postgres_retriever import DSPyPostgresRetriever
from dspy_implementation.dc_module.dc_wrapper import DCWrapper
from dspy_implementation.dc_module.dc_prompts import GENERATOR_PROMPT, CURATOR_PROMPT, CURATOR_PROMPT_RS
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from langchain_community.embeddings import DashScopeEmbeddings
import os


class DCRAGModule:
    """
    Dynamic Cheatsheet + RAG for MMESGBench
    
    Architecture:
        Question -> PostgreSQL Retrieval -> DC Generator -> Answer
                                              |
                                              v
                                         DC Curator (updates cheatsheet)
    
    Note: This is NOT a DSPy module - uses DC's native framework
    """
    
    def __init__(self, model_name="qwen2.5-7b-instruct", variant="cumulative"):
        """
        Initialize DC-RAG module
        
        Args:
            model_name: Model to use (default: qwen2.5-7b-instruct)
            variant: DC variant - "cumulative" or "retrieval_synthesis"
        """
        self.retriever = DSPyPostgresRetriever()
        self.dc = DCWrapper(model_name)
        self.cheatsheet = "(empty)"  # Start with empty cheatsheet
        self.variant = variant
        self.model_name = model_name
        
        # DC-RS specific: QA history and embeddings
        if variant == "retrieval_synthesis":
            self.qa_history = []  # List of {question, answer, context} dicts
            self.qa_embeddings = []  # Corresponding embeddings
            # Initialize embedding model (same as retriever uses)
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("DASHSCOPE_API_KEY environment variable not set")
            self.embedding_model = DashScopeEmbeddings(
                model="text-embedding-v4",
                dashscope_api_key=api_key
            )
            print(f"✅ DC-RS: Embedding model initialized (text-embedding-v4)")
        
        print(f"✅ DC-RAG Module initialized")
        print(f"   Model: {model_name}")
        print(f"   Variant: {variant}")
        if variant == "cumulative":
            print(f"   Mode: DC-CU (Cumulative cheatsheet)")
        else:
            print(f"   Mode: DC-RS (Retrieval & Synthesis)")
        print(f"   Cheatsheet: Empty (will evolve with each question)")
    
    def _format_input(self, question, context, answer_format):
        """Format input for DC generator"""
        return f"""
Retrieved Context from ESG Document:
{context}

Question: {question}
Expected Answer Format: {answer_format}

Please analyze the context and provide the answer in the specified format.
"""
    
    def _format_curator_input(self, question, context, answer, answer_format):
        """Format input for DC curator"""
        # Truncate context for curator to avoid token limits
        context_excerpt = context[:500] + "..." if len(context) > 500 else context
        return f"""
Question: {question}
Format: {answer_format}
Answer: {answer}
Context: {context_excerpt}
"""
    
    def _retrieve_similar_qas(self, current_question, top_k=5):
        """
        Retrieve top-K similar Q&As from history (DC-RS only)
        
        Args:
            current_question: Current question to find similar examples for
            top_k: Number of similar Q&As to retrieve
        
        Returns:
            List of similar Q&A dicts
        """
        if len(self.qa_history) == 0:
            return []
        
        # Get embedding for current question
        current_embedding = self.embedding_model.embed_query(current_question)
        
        # Compute similarities with all past questions
        similarities = cosine_similarity(
            [current_embedding],
            self.qa_embeddings
        )[0]
        
        # Get top-K indices (most similar)
        top_k_indices = np.argsort(similarities)[::-1][:min(top_k, len(similarities))]
        
        # Return corresponding Q&As with similarity scores
        similar_qas = []
        for idx in top_k_indices:
            qa = self.qa_history[idx].copy()
            qa['similarity'] = similarities[idx]
            similar_qas.append(qa)
        
        return similar_qas
    
    def _format_retrieved_qas(self, similar_qas):
        """Format retrieved Q&As for DC-RS curator prompt"""
        if not similar_qas:
            return "(empty - no previous Q&As yet)"
        
        formatted = "### PREVIOUS SOLUTIONS (START)\n\n"
        formatted += "Note: The question-answer pairs listed below are from previous questions in this evaluation run.\n"
        formatted += "They are meant to help you identify patterns, strategies, and insights for the cheatsheet.\n\n"
        
        for i, qa in enumerate(similar_qas, 1):
            similarity = qa.get('similarity', 0.0)
            context_excerpt = qa['context'][:300] + "..." if len(qa['context']) > 300 else qa['context']
            
            formatted += f"#### Previous Question #{i} (Similarity: {similarity:.3f}):\n\n"
            formatted += f"{qa['question']}\n\n"
            formatted += f"#### Answer to Previous Question #{i}:\n\n"
            formatted += f"Format: {qa['format']}\n"
            formatted += f"Answer: {qa['answer']}\n"
            formatted += f"Context Excerpt: {context_excerpt}\n"
            formatted += "---\n\n"
        
        formatted += "### PREVIOUS SOLUTIONS (END)\n"
        return formatted
    
    def forward(self, question, doc_id, answer_format):
        """
        Process question with DC + RAG
        
        Args:
            question: ESG question
            doc_id: Document identifier
            answer_format: Expected format (Int/Float/Str/List/null)
        
        Returns:
            str: Predicted answer
        """
        # Step 1: RAG Retrieval (same as DSPy baseline)
        context = self.retriever.retrieve(doc_id, question, top_k=5)
        
        if not context:
            print(f"⚠️  Retrieval failed for doc: {doc_id}")
            return "ERROR: Retrieval failed"
        
        # Step 2: DC Generation + Curation (variant-specific)
        try:
            if self.variant == "cumulative":
                # DC-CU: Use full accumulated cheatsheet
                result = self.dc.generate_with_cheatsheet(
                    question=question,
                    context=context,
                    answer_format=answer_format,
                    cheatsheet=self.cheatsheet,
                    generator_prompt_template=GENERATOR_PROMPT,
                    curator_prompt_template=CURATOR_PROMPT
                )
                
                # Extract answer and updated cheatsheet
                answer = result.get('answer', 'ERROR: No answer')
                new_cheatsheet = result.get('updated_cheatsheet', self.cheatsheet)
                
                # Update cheatsheet for next question
                self.cheatsheet = new_cheatsheet
                
            elif self.variant == "retrieval_synthesis":
                # DC-RS: Following original DC implementation flow
                # 1. Retrieve similar Q&As
                # 2. Synthesize custom cheatsheet (curator)
                # 3. Generate answer with custom cheatsheet (generator)
                # 4. Store Q&A for future retrieval
                
                # Step 2a: Retrieve top-K similar Q&As from history
                similar_qas = self._retrieve_similar_qas(question, top_k=5)
                retrieved_qas_text = self._format_retrieved_qas(similar_qas)
                
                # Step 2b: Synthesize CUSTOM cheatsheet for this question
                #          Using curator with: global_cheatsheet + retrieved_qas + current_question
                curator_prompt_rs = CURATOR_PROMPT_RS.format(
                    previous_cheatsheet=self.cheatsheet,
                    retrieved_qa_pairs=retrieved_qas_text,
                    next_input=question
                )
                
                curator_messages = [{"role": "user", "content": curator_prompt_rs}]
                curator_output = self.dc.generate(curator_messages, temperature=0.1, max_tokens=2048)
                
                # Extract custom cheatsheet from curator output (look for <cheatsheet> tags)
                if "<cheatsheet>" in curator_output:
                    try:
                        custom_cheatsheet = curator_output.split("<cheatsheet>")[1].split("</cheatsheet>")[0].strip()
                    except:
                        custom_cheatsheet = curator_output  # Fallback to full output
                else:
                    custom_cheatsheet = curator_output
                
                # Step 2c: Generate answer using the CUSTOM cheatsheet
                #          (NOT the global cheatsheet - this is the key difference)
                generator_prompt = GENERATOR_PROMPT.format(
                    context=context,
                    cheatsheet=custom_cheatsheet,  # Use custom synthesized cheatsheet
                    question=question,
                    answer_format=answer_format
                )
                
                generator_messages = [{"role": "user", "content": generator_prompt}]
                answer = self.dc.generate(generator_messages, temperature=0.1, max_tokens=512)
                
                # Step 2d: Update global cheatsheet (optional - original doesn't do this for DC-RS)
                #          We'll keep it to maintain learning across questions
                self.cheatsheet = custom_cheatsheet
                
                # Step 2e: Store this Q&A in history for future retrieval
                qa_entry = {
                    'question': question,
                    'answer': answer,
                    'context': context[:500],  # Truncate context to save memory
                    'format': answer_format
                }
                self.qa_history.append(qa_entry)
                
                # Store embedding for this question
                question_embedding = self.embedding_model.embed_query(question)
                self.qa_embeddings.append(question_embedding)
            
            else:
                raise ValueError(f"Unknown DC variant: {self.variant}")
            
            return answer
            
        except Exception as e:
            print(f"⚠️  DC generation error: {e}")
            import traceback
            traceback.print_exc()
            return f"ERROR: {str(e)}"
    
    def __call__(self, question, doc_id, answer_format):
        """Allow module(args) syntax for compatibility"""
        return self.forward(question, doc_id, answer_format)
    
    def get_cheatsheet_stats(self):
        """Get current cheatsheet statistics"""
        return {
            'length_chars': len(self.cheatsheet),
            'length_words': len(self.cheatsheet.split()),
            'is_empty': self.cheatsheet == "(empty)"
        }

