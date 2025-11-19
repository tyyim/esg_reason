#!/usr/bin/env python3
"""
ACE Evaluator for MMESGBench

Mirrors the DC evaluator structure: checkpointing, logging, retries, and
uses MMESGBench's eval_score for metrics. Runs ACE in online mode.
"""
from __future__ import annotations

import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dspy_implementation.ace.playbook import Playbook  # type: ignore
from dspy_implementation.ace.ace_module import ACERAGModule  # type: ignore
from dspy_implementation.ace.adaptation import OfflineAdapter, Sample  # type: ignore
from dspy_implementation.dspy_dataset import MMESGBenchDataset  # type: ignore
from dspy_implementation.dspy_setup import setup_dspy_qwen  # type: ignore
from MMESGBench.src.eval.eval_score import eval_score  # type: ignore


class ACEEvaluator:
    def __init__(self, output_dir: str = "results/ace_experiments") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()

    def _setup_logging(self) -> None:
        log_dir = Path("logs/ace_evaluation")
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"ace_eval_{timestamp}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"ACE Evaluator initialized. Logs: {log_file}")

    def _load_checkpoint(self, checkpoint_file: Path):
        if checkpoint_file.exists():
            self.logger.info(f"Loading checkpoint: {checkpoint_file}")
            with checkpoint_file.open('r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def _save_checkpoint(self, checkpoint_file: Path, predictions, playbook: object, metadata: dict) -> None:
        """Save checkpoint with full playbook state for recovery."""
        try:
            # Ensure playbook can be serialized
            if hasattr(playbook, 'to_dict'):
                playbook_dict = playbook.to_dict()
                bullets_count = len(playbook_dict.get('bullets', {}))
                self.logger.debug(f"Playbook serialized: {bullets_count} bullets")
            else:
                playbook_dict = {}
                self.logger.warning("Playbook does not have to_dict method - saving empty playbook")
            
            # Get playbook stats for logging
            playbook_stats = playbook.stats() if hasattr(playbook, 'stats') else {}
            
            payload = {
                'predictions': predictions,
                'playbook': playbook_dict,
                'playbook_stats': playbook_stats,
                'metadata': metadata,
                'timestamp': datetime.now().isoformat()
            }
            
            # Write checkpoint file atomically
            with checkpoint_file.open('w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Checkpoint saved: {len(predictions)} predictions, playbook: {playbook_stats} (bullets: {len(playbook_dict.get('bullets', {}))})")
            
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}", exc_info=True)
            # Try to save without playbook as fallback
            fallback_payload = {
                'predictions': predictions,
                'metadata': metadata,
                'timestamp': datetime.now().isoformat(),
                'checkpoint_error': str(e)
            }
            with checkpoint_file.open('w', encoding='utf-8') as f:
                json.dump(fallback_payload, f, ensure_ascii=False, indent=2)
            self.logger.warning("Saved checkpoint without playbook due to error")

    def _evaluate_one(self, ace_module: ACERAGModule, example, *, adapt: bool = True, max_retries: int = 3, context_override: str | None = None):
        self.logger.info(f"[Question {example.doc_id}] Processing: {example.question[:100]}...")
        for attempt in range(max_retries):
            try:
                details = ace_module.forward_with_details(
                    question=example.question,
                    doc_id=example.doc_id,
                    answer_format=example.answer_format,
                    context=context_override,
                    ground_truth=example.answer,  # Pass ground_truth to enable reflection
                    adapt=adapt,
                )
                final_answer = details.get('final_answer', '')
                analysis_text = details.get('reasoning', '')
                context_text = details.get('context', '')

                if (final_answer is None or final_answer == '' or str(final_answer).strip().lower() in ['none', 'null', 'n/a', 'na', 'str']):
                    final_answer = "Not answerable"
                score = eval_score(example.answer, final_answer, example.answer_format)
                is_correct = (score >= 0.5)
                return {
                    'question': example.question,
                    'doc_id': example.doc_id,
                    'answer_format': example.answer_format,
                    'ground_truth': example.answer,
                    'analysis': analysis_text,
                    'final_answer': final_answer,
                    'context': context_text,
                    'anls_score': score,
                    'correct': is_correct,
                    'playbook_stats': ace_module.playbook_stats(),
                }
            except Exception as e:
                self.logger.exception(f"Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__}: {e}")
                if attempt + 1 >= max_retries:
                    return {
                        'question': example.question,
                        'doc_id': example.doc_id,
                        'answer_format': example.answer_format,
                        'ground_truth': example.answer,
                        'analysis': f"ERROR: {type(e).__name__}: {str(e)}",
                        'final_answer': '',
                        'context': '',
                        'anls_score': 0.0,
                        'correct': False,
                        'playbook_stats': ace_module.playbook_stats(),
                    }
                time.sleep(2 ** attempt)

    def _compute_metrics(self, predictions):
        total = len(predictions)
        correct = sum(1 for p in predictions if p['correct'])
        accuracy = correct / total if total > 0 else 0.0
        fmt_breakdown = {}
        for fmt in ['Int', 'Float', 'Str', 'List', 'null']:
            fmt_preds = [p for p in predictions if p['answer_format'] == fmt]
            if fmt_preds:
                fmt_correct = sum(1 for p in fmt_preds if p['correct'])
                fmt_breakdown[fmt] = {
                    'correct': fmt_correct,
                    'total': len(fmt_preds),
                    'accuracy': fmt_correct / len(fmt_preds)
                }
        return {
            'overall_accuracy': accuracy,
            'correct': correct,
            'total': total,
            'format_breakdown': fmt_breakdown
        }

    def evaluate(self, dataset_name: str = "dev", model_name: str = "qwen2.5-7b-instruct", max_questions: int | None = None, no_retrieval: bool = False, baseline_context_file: str | None = None, checkpoint_interval: int = 10, *, offline_pretrain: bool = False, offline_train_split: str = "dev", offline_epochs: int = 1, freeze_playbook: bool = False, offline_max_questions: int | None = None, load_playbook: str | None = None, no_progress: bool = False, llm_type: str = "dashscope", api_key: str | None = None, base_url: str | None = None):
        self.logger.info("=" * 80)
        self.logger.info("ACE EVALUATION - MMESGBench")
        self.logger.info("=" * 80)
        self.logger.info(f"Dataset: {dataset_name}")
        self.logger.info(f"Model: {model_name}")
        self.logger.info(f"LLM Type: {llm_type}")

        setup_dspy_qwen()
        dataset = MMESGBenchDataset()
        if dataset_name == "dev":
            eval_set = dataset.dev_set
        elif dataset_name == "test":
            eval_set = dataset.test_set
        else:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        if max_questions:
            eval_set = eval_set[:max_questions]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_file = self.output_dir / f"ace_online_{dataset_name}_{model_name}_checkpoint.json"
        output_file = self.output_dir / f"ace_online_{dataset_name}_{model_name}_{timestamp}.json"

        ace_module = ACERAGModule(
            model_name=model_name,
            llm_type=llm_type,
            api_key=api_key,
            base_url=base_url,
        )

        # Check for checkpoint first - checkpoint takes priority over load_playbook
        checkpoint = self._load_checkpoint(checkpoint_file)
        checkpoint_playbook_restored = False
        
        if checkpoint:
            predictions = checkpoint.get('predictions', [])
            start_idx = len(predictions)
            # Restore playbook from checkpoint if available (highest priority)
            if 'playbook' in checkpoint and checkpoint['playbook']:
                try:
                    ace_module.playbook = Playbook.from_dict(checkpoint['playbook'])
                    # CRITICAL: Update adapter's playbook reference to point to the restored playbook
                    ace_module.adapter.playbook = ace_module.playbook
                    self.logger.info(f"Restored playbook from checkpoint: {ace_module.playbook.stats()}")
                    checkpoint_playbook_restored = True
                except Exception as e:
                    self.logger.warning(f"Failed to restore playbook from checkpoint: {e}. Will try load_playbook if provided.")
            self.logger.info(f"Resuming from question {start_idx + 1}/{len(eval_set)}")
        else:
            predictions = []
            start_idx = 0

        # Optional: load a previously saved playbook (only if not restored from checkpoint)
        if load_playbook and not checkpoint_playbook_restored:
            try:
                with open(load_playbook, 'r', encoding='utf-8') as f:
                    pb = json.load(f)
                ace_module.playbook = Playbook.from_dict(pb)
                # CRITICAL: Update adapter's playbook reference to point to the loaded playbook
                ace_module.adapter.playbook = ace_module.playbook
                self.logger.info(f"Loaded playbook from {load_playbook}. Skipping offline pretrain if requested.")
                offline_pretrain = False
            except Exception as e:
                self.logger.warning(f"Failed to load playbook from {load_playbook}: {e}. Will continue without it.")

        # Optional: offline pretraining to warm up playbook
        if offline_pretrain:
            self.logger.info("\n" + "-" * 80)
            self.logger.info(f"OFFLINE PRETRAIN START - split={offline_train_split}, epochs={offline_epochs}")
            # Select split
            train_split = None
            if offline_train_split == "train":
                train_split = getattr(dataset, "train_set", None)
                if train_split is None:
                    self.logger.warning("Dataset has no train_set; falling back to dev_set for offline pretrain.")
                    train_split = dataset.dev_set
            elif offline_train_split == "dev":
                train_split = dataset.dev_set
            else:
                raise ValueError(f"Unknown offline_train_split: {offline_train_split}")
            if offline_max_questions:
                train_split = train_split[:offline_max_questions]

            # Build Samples with retrieved context
            samples = []
            for ex in tqdm(train_split, desc="Offline retrieval for pretrain", disable=no_progress):
                ctx = ace_module.retriever.retrieve(ex.doc_id, ex.question, top_k=5)
                if not ctx:
                    continue
                s = Sample(
                    question=ex.question,
                    context=ctx,
                    ground_truth=ex.answer,
                    metadata={"doc_id": ex.doc_id, "answer_format": ex.answer_format},
                )
                samples.append(s)

            if not samples:
                self.logger.warning("No samples prepared for offline pretrain; skipping.")
            else:
                adapter = OfflineAdapter(
                    playbook=ace_module.playbook,
                    generator=ace_module.generator,
                    reflector=ace_module.reflector,
                    curator=ace_module.curator,
                    max_refinement_rounds=ace_module.adapter.max_refinement_rounds,
                    reflection_window=ace_module.adapter.reflection_window,
                )
                adapter.run(samples, ace_module.environment, epochs=offline_epochs)
                # Save pretrained playbook
                pretrain_file = self.output_dir / f"ace_pretrained_playbook_{offline_train_split}_{timestamp}.json"
                with pretrain_file.open('w', encoding='utf-8') as f:
                    json.dump(ace_module.playbook.to_dict(), f, ensure_ascii=False, indent=2)
                self.logger.info(f"Offline pretrain complete. Playbook saved: {pretrain_file}")

        # Optional: preload baseline contexts for no-retrieval mode
        baseline_contexts = None
        baseline_by_doc_question = {}
        baseline_by_question = {}
        if no_retrieval:
            # auto-pick default path if not provided
            if baseline_context_file is None:
                if dataset_name == "dev":
                    baseline_context_file = str(project_root / "results" / "dev_set" / "baseline_dev_predictions_20251019_130401.json")
                elif dataset_name == "test":
                    baseline_context_file = str(project_root / "results" / "test_set" / "baseline_test_predictions_20251021_225632.json")
            try:
                with open(baseline_context_file, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
                preds = payload.get('predictions') or {}
                # normalize predictions to a list of entries while preserving file order
                entries = []
                if isinstance(preds, dict):
                    def _key_order(k: str):
                        # try to sort q0, q1, ... numerically; otherwise lexicographically
                        try:
                            return int(''.join(ch for ch in k if ch.isdigit()))
                        except Exception:
                            return k
                    for k in sorted(preds.keys(), key=_key_order):
                        v = preds[k]
                        if isinstance(v, dict):
                            entries.append(v)
                elif isinstance(preds, list):
                    for v in preds:
                        if isinstance(v, dict):
                            entries.append(v)

                # Build sequential contexts and mapping indices by (doc_id, question) and by question text
                baseline_contexts = []
                for v in entries:
                    ctx = v.get('context', '')
                    q = v.get('question')
                    d = v.get('doc_id')
                    if ctx is None:
                        ctx = ''
                    baseline_contexts.append(ctx)
                    if d is not None and q is not None:
                        baseline_by_doc_question[(str(d), str(q))] = ctx
                    if q is not None:
                        baseline_by_question[str(q)] = ctx
                if baseline_contexts:
                    self.logger.info(f"Loaded {len(baseline_contexts)} baseline contexts from {baseline_context_file}")
                else:
                    self.logger.warning(f"No contexts found in {baseline_context_file}; will fall back to retrieval.")
            except Exception as e:
                self.logger.warning(f"Failed to load baseline contexts: {e}; will fall back to retrieval.")

        # Note: checkpoint and playbook restoration already handled above
        # predictions and start_idx are already set from checkpoint if it existed

        self.logger.info(f"Evaluating {len(eval_set)} questions...")
        for local_idx, example in enumerate(tqdm(eval_set[start_idx:], initial=start_idx, total=len(eval_set), desc="ACE Evaluation", disable=no_progress)):
            context_override = None
            global_idx = start_idx + local_idx
            if no_retrieval:
                # Prefer mapping by (doc_id, question), then by question text, then by sequential index
                if (example.doc_id, example.question) in baseline_by_doc_question:
                    context_override = baseline_by_doc_question[(example.doc_id, example.question)]
                elif example.question in baseline_by_question:
                    context_override = baseline_by_question[example.question]
                elif baseline_contexts and global_idx < len(baseline_contexts):
                    context_override = baseline_contexts[global_idx]
            result = self._evaluate_one(ace_module, example, adapt=not freeze_playbook, context_override=context_override)
            predictions.append(result)
            # Save checkpoint every N questions if enabled
            # Note: We save after appending, so len(predictions) is the current count
            if checkpoint_interval and checkpoint_interval > 0 and (len(predictions) % checkpoint_interval == 0):
                meta = {
                    'dataset': dataset_name,
                    'model': model_name,
                    'questions_processed': len(predictions)
                }
                # Always save the current playbook state to checkpoint
                self._save_checkpoint(checkpoint_file, predictions, playbook=ace_module.playbook, metadata=meta)
                self.logger.info(f"Checkpoint saved at question {len(predictions)} with playbook stats: {ace_module.playbook.stats()}")

        results = self._compute_metrics(predictions)
        results['metadata'] = {
            'dataset': dataset_name,
            'model': model_name,
            'total_questions': len(predictions),
            'timestamp': timestamp,
        }
        results['predictions'] = predictions
        # Save complete playbook state
        results['final_playbook'] = ace_module.playbook.to_dict()
        results['final_playbook_prompt'] = ace_module.playbook.as_prompt()

        with output_file.open('w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Also save playbook as a separate JSON file for easier inspection
        playbook_file = self.output_dir / f"ace_playbook_{dataset_name}_{model_name}_{timestamp}.json"
        with playbook_file.open('w', encoding='utf-8') as f:
            json.dump(ace_module.playbook.to_dict(), f, ensure_ascii=False, indent=2)
        self.logger.info(f"Playbook saved: {playbook_file}")

        self.logger.info("\n" + "=" * 80)
        self.logger.info("EVALUATION COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"Accuracy: {results['overall_accuracy']:.1%} ({results['correct']}/{results['total']})")
        self.logger.info(f"Results saved: {output_file}")

        # Final checkpoint at end as well
        final_meta = {
            'dataset': dataset_name,
            'model': model_name,
            'questions_processed': len(predictions),
            'final': True,
        }
        self._save_checkpoint(checkpoint_file, predictions, playbook=ace_module.playbook, metadata=final_meta)
        # Keep the checkpoint file for inspection/restart convenience

        return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate ACE on MMESGBench")
    parser.add_argument("--dataset", choices=["dev", "test"], default="dev")
    parser.add_argument("--model", default="qwen2.5-7b-instruct")
    parser.add_argument("--max-questions", type=int, default=None)
    parser.add_argument("--output-dir", default="results/ace_experiments")
    parser.add_argument("--checkpoint-interval", type=int, default=10, help="Save checkpoint every N questions (0 to disable)")
    parser.add_argument("--no-retrieval", action="store_true", help="Use baseline context file instead of retrieval for dev/test")
    parser.add_argument("--baseline-context-file", type=str, default=None, help="Path to baseline predictions JSON providing 'context' fields")
    parser.add_argument("--load-playbook", type=str, default=None, help="Path to a pretrained playbook JSON to load before evaluation")
    parser.add_argument("--no-progress", action="store_true", help="Disable tqdm progress bars to make logs clearer")
    parser.add_argument("--offline-pretrain", action="store_true", help="Run offline pretrain on a split to warm up playbook before evaluation")
    parser.add_argument("--offline-train-split", choices=["train", "dev"], default="dev", help="Which split to use for offline pretrain")
    parser.add_argument("--offline-epochs", type=int, default=1, help="Number of epochs for offline pretrain")
    parser.add_argument("--offline-max-questions", type=int, default=None, help="Limit number of questions for offline pretrain")
    parser.add_argument("--freeze-playbook", action="store_true", help="Freeze playbook during evaluation (no reflection/curation)")
    parser.add_argument("--llm-type", choices=["dashscope", "openai"], default="openai", help="Type of LLM client to use (default: dashscope)")
    parser.add_argument("--api-key", type=str, default=None, help="API key (defaults to DASHSCOPE_API_KEY or OPENAI_API_KEY env var)")
    parser.add_argument("--base-url", type=str, default=None, help="Base URL for API (defaults to OPENAI_API_BASE env var for OpenAI)")
    args = parser.parse_args()

    evaluator = ACEEvaluator(output_dir=args.output_dir)
    evaluator.evaluate(
        dataset_name=args.dataset,
        model_name=args.model,
        max_questions=args.max_questions,
        no_retrieval=args.no_retrieval,
        baseline_context_file=args.baseline_context_file,
        checkpoint_interval=args.checkpoint_interval,
        offline_pretrain=args.offline_pretrain,
        offline_train_split=args.offline_train_split,
        offline_epochs=args.offline_epochs,
        freeze_playbook=args.freeze_playbook,
        offline_max_questions=args.offline_max_questions,
        load_playbook=args.load_playbook,
        no_progress=args.no_progress,
        llm_type=args.llm_type,
        api_key=args.api_key,
        base_url=args.base_url,
    )


