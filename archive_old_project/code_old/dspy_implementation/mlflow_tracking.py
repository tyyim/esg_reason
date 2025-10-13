#!/usr/bin/env python3
"""
MLFlow experiment tracking for DSPy optimization
Tracks metrics, parameters, and artifacts for RAG optimization
"""

import mlflow
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class DSPyMLFlowTracker:
    """
    MLFlow experiment tracking wrapper for DSPy optimization.

    Features:
        - Automatic experiment creation
        - Parameter logging (model configs, hyperparameters)
        - Metric logging (retrieval, answer, end-to-end accuracy)
        - Artifact logging (optimized modules, results, predictions)
        - Step-by-step optimization tracking
    """

    def __init__(self, experiment_name: str = "MMESGBench_DSPy_Optimization",
                 tracking_uri: Optional[str] = None):
        """
        Initialize MLFlow tracker.

        Args:
            experiment_name: Name of MLFlow experiment
            tracking_uri: MLFlow tracking server URI (default: local ./mlruns)
        """
        # Set tracking URI (local by default)
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        else:
            # Use local mlruns directory
            mlruns_dir = Path.cwd() / "mlruns"
            mlruns_dir.mkdir(exist_ok=True)
            mlflow.set_tracking_uri(f"file://{mlruns_dir}")

        # Create or get experiment
        try:
            self.experiment = mlflow.set_experiment(experiment_name)
            self.experiment_id = self.experiment.experiment_id
        except Exception as e:
            print(f"⚠️  Could not set experiment: {e}")
            self.experiment = None
            self.experiment_id = None

        self.run = None
        self.run_id = None

        print(f"✅ MLFlow tracker initialized")
        print(f"   Experiment: {experiment_name}")
        print(f"   Tracking URI: {mlflow.get_tracking_uri()}")

    def start_run(self, run_name: str, tags: Optional[Dict[str, str]] = None):
        """
        Start new MLFlow run.

        Args:
            run_name: Name for this run
            tags: Optional tags (e.g., {'optimizer': 'MIPROv2', 'phase': 'baseline'})

        Returns:
            MLFlow run object
        """
        if self.run:
            print(f"⚠️  Ending previous run {self.run_id}")
            self.end_run()

        self.run = mlflow.start_run(run_name=run_name, tags=tags or {})
        self.run_id = self.run.info.run_id

        print(f"\n🚀 Started MLFlow run: {run_name}")
        print(f"   Run ID: {self.run_id}")

        return self.run

    def log_params(self, params: Dict[str, Any]):
        """
        Log parameters (configuration, hyperparameters).

        Args:
            params: Dictionary of parameters
        """
        if not self.run:
            print("⚠️  No active run. Call start_run() first.")
            return

        for key, value in params.items():
            try:
                mlflow.log_param(key, value)
            except Exception as e:
                print(f"⚠️  Could not log param {key}: {e}")

        print(f"📝 Logged {len(params)} parameters")

    def log_baseline(self, metrics: Dict[str, float], config: Dict[str, Any]):
        """
        Log baseline evaluation results.

        Args:
            metrics: Baseline metrics (retrieval_accuracy, answer_accuracy, etc.)
            config: Baseline configuration
        """
        if not self.run:
            print("⚠️  No active run. Call start_run() first.")
            return

        # Log configuration
        self.log_params(config)

        # Log baseline metrics (skip nested dicts)
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(f"baseline_{key}", value)

        print(f"📊 Logged baseline metrics:")
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                print(f"   {key}: {value:.1%}" if isinstance(value, float) else f"   {key}: {value}")

    def log_optimization_step(self, step: int, metrics: Dict[str, float]):
        """
        Log optimization progress at each step.

        Args:
            step: Optimization step number
            metrics: Metrics at this step
        """
        if not self.run:
            print("⚠️  No active run. Call start_run() first.")
            return

        for key, value in metrics.items():
            try:
                mlflow.log_metric(key, value, step=step)
            except Exception as e:
                print(f"⚠️  Could not log metric {key}: {e}")

    def log_final_results(self, metrics: Dict[str, float], artifacts: Optional[Dict[str, str]] = None):
        """
        Log final optimized results.

        Args:
            metrics: Final metrics after optimization
            artifacts: Optional dictionary of {artifact_name: file_path}
        """
        if not self.run:
            print("⚠️  No active run. Call start_run() first.")
            return

        # Log final metrics (skip nested dicts)
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(f"final_{key}", value)

        print(f"\n📊 Final Results:")
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                print(f"   {key}: {value:.1%}" if isinstance(value, float) else f"   {key}: {value}")

        # Log artifacts (files)
        if artifacts:
            for name, path in artifacts.items():
                try:
                    mlflow.log_artifact(path, name)
                    print(f"   📎 Logged artifact: {name}")
                except Exception as e:
                    print(f"   ⚠️  Could not log artifact {name}: {e}")

    def log_model_artifact(self, model_data: Dict[str, Any], artifact_name: str = "optimized_model"):
        """
        Log DSPy model data as JSON artifact.

        Args:
            model_data: Dictionary containing model information
            artifact_name: Name for the artifact
        """
        if not self.run:
            print("⚠️  No active run. Call start_run() first.")
            return

        # Save to temporary JSON file
        temp_path = Path(f"/tmp/{artifact_name}_{self.run_id}.json")
        with open(temp_path, 'w') as f:
            json.dump(model_data, f, indent=2)

        # Log artifact
        try:
            mlflow.log_artifact(str(temp_path), "model")
            print(f"📦 Logged model artifact: {artifact_name}")
        except Exception as e:
            print(f"⚠️  Could not log model artifact: {e}")

    def log_comparison(self, baseline_metrics: Dict[str, float], optimized_metrics: Dict[str, float]):
        """
        Log comparison between baseline and optimized model.

        Args:
            baseline_metrics: Baseline metrics
            optimized_metrics: Optimized metrics
        """
        if not self.run:
            print("⚠️  No active run. Call start_run() first.")
            return

        print(f"\n📊 Baseline vs Optimized:")

        for key in baseline_metrics:
            if key in optimized_metrics:
                baseline = baseline_metrics[key]
                optimized = optimized_metrics[key]
                improvement = optimized - baseline

                mlflow.log_metric(f"improvement_{key}", improvement)

                if isinstance(baseline, float) and isinstance(optimized, float):
                    print(f"   {key}:")
                    print(f"      Baseline:  {baseline:.1%}")
                    print(f"      Optimized: {optimized:.1%}")
                    print(f"      Improvement: {improvement:+.1%}")

    def end_run(self):
        """End current MLFlow run."""
        if self.run:
            mlflow.end_run()
            print(f"\n✅ Ended MLFlow run: {self.run_id}")
            self.run = None
            self.run_id = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically end run."""
        self.end_run()


def create_run_name(prefix: str = "enhanced_rag") -> str:
    """Create timestamped run name."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}"


if __name__ == "__main__":
    print("=" * 60)
    print("MLFlow Tracking Test")
    print("=" * 60)

    # Test tracker
    tracker = DSPyMLFlowTracker(experiment_name="Test_Experiment")

    # Start run
    run_name = create_run_name("test_run")
    tracker.start_run(run_name, tags={'test': 'true', 'optimizer': 'MIPROv2'})

    # Log baseline
    baseline_config = {
        'model': 'qwen-max',
        'temperature': 0.0,
        'retrieval': 'postgresql_pgvector',
        'top_k': 5
    }
    baseline_metrics = {
        'retrieval_accuracy': 0.37,
        'answer_accuracy': 0.45,
        'end_to_end_accuracy': 0.30
    }
    tracker.log_baseline(baseline_metrics, baseline_config)

    # Log optimization steps
    for step in range(1, 4):
        metrics = {
            'retrieval_accuracy': 0.37 + (step * 0.05),
            'answer_accuracy': 0.45 + (step * 0.02),
            'end_to_end_accuracy': 0.30 + (step * 0.03)
        }
        tracker.log_optimization_step(step, metrics)

    # Log final results
    final_metrics = {
        'retrieval_accuracy': 0.52,
        'answer_accuracy': 0.51,
        'end_to_end_accuracy': 0.48
    }
    tracker.log_final_results(final_metrics)

    # Log comparison
    tracker.log_comparison(baseline_metrics, final_metrics)

    # End run
    tracker.end_run()

    print("\n✅ MLFlow tracking test complete!")
    print(f"   View results: mlflow ui (then open http://localhost:5000)")
