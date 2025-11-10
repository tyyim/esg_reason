"""
DC Evaluator v2 - Using Original DC Implementation Directly
Only adapts data loading for MMESGBench
"""
import sys
from pathlib import Path
import json
import os
from datetime import datetime
from tqdm import tqdm
import time

# Add paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "dc_repo"))

# Load environment variables (for DASHSCOPE_API_KEY)
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# Ensure API key is set in os.environ for litellm
if not os.getenv("DASHSCOPE_API_KEY"):
    raise ValueError("DASHSCOPE_API_KEY not found in environment")

# Import original DC code
from dynamic_cheatsheet.language_model import LanguageModel

# Import our utilities
from dspy_implementation.dspy_dataset import MMESGBenchDataset
from dspy_implementation.dspy_postgres_retriever import DSPyPostgresRetriever
from src.evaluation import eval_score
from langchain_community.embeddings import DashScopeEmbeddings


class DCEvaluatorV2:
    """
    Uses original DC implementation directly, only adapts MMESGBench data
    """
    
    def __init__(self, model_name="qwen2.5-7b-instruct"):
        """Initialize with original DC LanguageModel"""
        # Map our model names to DC's expected DashScope format
        if model_name == "qwen2.5-7b-instruct":
            dc_model = "dashscope/qwen2.5-7b-instruct"
        elif model_name == "qwen-max":
            dc_model = "dashscope/qwen-max"
        elif model_name == "qwen-plus":
            dc_model = "dashscope/qwen-plus"
        elif model_name == "qwen-turbo":
            dc_model = "dashscope/qwen-turbo"
        else:
            # Assume it's already in correct format
            dc_model = model_name
        
        self.lm = LanguageModel(model_name=dc_model)
        self.retriever = DSPyPostgresRetriever()
        
        # For DC-RS: embedding model
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY environment variable not set")
        self.embedding_model = DashScopeEmbeddings(
            model="text-embedding-v4",
            dashscope_api_key=api_key
        )
        
        print(f"✅ DC Evaluator V2 initialized")
        print(f"   Using original DC LanguageModel")
        print(f"   Model: {dc_model}")
    
    def load_prompts(self, variant="cumulative"):
        """Load prompt templates from dc_repo"""
        prompts_dir = project_root / "dc_repo" / "prompts"
        
        # Generator prompt (same for both variants)
        with open(prompts_dir / "generator_prompt.txt", 'r') as f:
            generator_template = f.read()
        
        # Curator prompt (variant-specific)
        if variant == "cumulative":
            curator_file = "curator_prompt_for_dc_cumulative.txt"
        else:
            curator_file = "curator_prompt_for_dc_retrieval_synthesis.txt"
        
        with open(prompts_dir / curator_file, 'r') as f:
            curator_template = f.read()
        
        return generator_template, curator_template
    
    def format_input(self, question, context, answer_format):
        """Format MMESGBench data as DC input_txt"""
        return f"""Question: {question}

Retrieved Context from ESG Document:
{context}

Expected Answer Format: {answer_format}

Instructions:
- Int: Return only the integer (e.g., "42")
- Float: Return the number with decimals (e.g., "3.14")
- Str: Return the exact text string (e.g., "Scope 1 emissions")
- List: Return a JSON array (e.g., ["item1", "item2"])
- null: Return "null" if unanswerable

Provide ONLY the final answer in the specified format."""
    
    def evaluate(self, dataset_name="dev", variant="cumulative", max_questions=None):
        """
        Evaluate using original DC implementation
        
        Args:
            dataset_name: "dev" or "test"
            variant: "cumulative" or "retrieval_synthesis"
            max_questions: Limit questions for testing
        """
        print(f"\n{'='*60}")
        print(f"DC Evaluation V2 - Using Original Implementation")
        print(f"{'='*60}")
        print(f"Dataset: {dataset_name}")
        print(f"Variant: {variant}")
        print(f"Max questions: {max_questions or 'all'}")
        
        # Load data
        dataset = MMESGBenchDataset()
        if dataset_name == "dev":
            questions = dataset.dev_set
        else:
            questions = dataset.test_set
        
        if max_questions:
            questions = questions[:max_questions]
        
        # Load prompts
        generator_template, curator_template = self.load_prompts(variant)
        
        # Initialize DC state
        cheatsheet = "(empty)"
        
        # For DC-RS
        if variant == "retrieval_synthesis":
            input_corpus = []
            input_embeddings = []
            generator_outputs = []
        
        # Evaluate
        predictions = []
        correct = 0
        
        for i, item in enumerate(tqdm(questions, desc="Evaluating")):
            question = item['question']
            doc_id = item['doc_id']
            answer_format = item['answer_format']
            gt = item['answer']
            
            # Retrieve context
            context = self.retriever.retrieve(doc_id, question, top_k=5)
            if not context:
                print(f"⚠️  Retrieval failed for question {i+1}")
                predictions.append({
                    'question': question,
                    'predicted': 'ERROR: Retrieval failed',
                    'ground_truth': gt,
                    'correct': False
                })
                continue
            
            # Format input
            input_txt = self.format_input(question, context, answer_format)
            
            try:
                # For DC-RS: add current embedding BEFORE calling advanced_generate
                if variant == "retrieval_synthesis":
                    current_embedding = self.embedding_model.embed_query(question)
                    # Temporarily add to lists for advanced_generate call
                    input_embeddings.append(current_embedding)
                    input_corpus.append(input_txt)
                
                # Call original DC advanced_generate()
                if variant == "cumulative":
                    result = self.lm.advanced_generate(
                        approach_name="DynamicCheatsheet_Cumulative",
                        input_txt=input_txt,
                        cheatsheet=cheatsheet,
                        generator_template=generator_template,
                        cheatsheet_template=curator_template,
                        temperature=0.1,
                        max_tokens=512,
                        allow_code_execution=False
                    )
                else:  # retrieval_synthesis
                    result = self.lm.advanced_generate(
                        approach_name="DynamicCheatsheet_RetrievalSynthesis",
                        input_txt=input_txt,
                        cheatsheet=cheatsheet,
                        generator_template=generator_template,
                        cheatsheet_template=curator_template,
                        temperature=0.1,
                        max_tokens=512,
                        allow_code_execution=False,
                        original_input_corpus=input_corpus,
                        original_input_embeddings=input_embeddings,
                        generator_outputs_so_far=generator_outputs,
                        retrieve_top_k=5
                    )
                
                # Extract results
                pred = result['final_answer']
                cheatsheet = result['final_cheatsheet']
                
                # For DC-RS: add generator output AFTER getting result
                if variant == "retrieval_synthesis":
                    generator_outputs.append(pred)
                
                # Evaluate
                score = eval_score(gt, pred, answer_format)
                is_correct = (score >= 0.5)
                
                if is_correct:
                    correct += 1
                
                predictions.append({
                    'question': question,
                    'predicted': pred,
                    'ground_truth': gt,
                    'answer_type': answer_format,
                    'score': score,
                    'correct': is_correct
                })
                
            except Exception as e:
                print(f"\n⚠️  Error on question {i+1}: {e}")
                # For DC-RS: remove the embedding/corpus we added if there was an error
                if variant == "retrieval_synthesis" and len(input_embeddings) > len(generator_outputs):
                    input_embeddings.pop()
                    input_corpus.pop()
                predictions.append({
                    'question': question,
                    'predicted': f'ERROR: {str(e)}',
                    'ground_truth': gt,
                    'correct': False
                })
        
        # Compute metrics
        accuracy = correct / len(predictions) if predictions else 0
        
        print(f"\n{'='*60}")
        print(f"Results:")
        print(f"  Accuracy: {accuracy:.1%} ({correct}/{len(predictions)})")
        print(f"{'='*60}\n")
        
        return {
            'accuracy': accuracy,
            'correct': correct,
            'total': len(predictions),
            'predictions': predictions,
            'final_cheatsheet': cheatsheet
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="DC Evaluator V2 - Using Original Implementation")
    parser.add_argument("--dataset", choices=["dev", "test"], default="dev")
    parser.add_argument("--variant", choices=["cumulative", "retrieval_synthesis"], default="cumulative")
    parser.add_argument("--model", default="qwen2.5-7b-instruct")
    parser.add_argument("--max-questions", type=int, default=None)
    
    args = parser.parse_args()
    
    evaluator = DCEvaluatorV2(model_name=args.model)
    results = evaluator.evaluate(
        dataset_name=args.dataset,
        variant=args.variant,
        max_questions=args.max_questions
    )
    
    # Save results
    output_dir = project_root / "results" / "dc_experiments"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"dc_v2_{args.variant}_{args.dataset}_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Results saved to: {output_file}")


if __name__ == "__main__":
    main()

