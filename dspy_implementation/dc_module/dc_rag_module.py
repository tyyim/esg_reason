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
from dspy_implementation.dc_module.dc_prompts import GENERATOR_PROMPT, CURATOR_PROMPT


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
        
        print(f"✅ DC-RAG Module initialized")
        print(f"   Model: {model_name}")
        print(f"   Variant: {variant}")
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
        
        # Step 2: DC Generation + Curation (original 2-stage approach)
        try:
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
            
            # Step 3: Update cheatsheet for next question
            self.cheatsheet = new_cheatsheet
            
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

