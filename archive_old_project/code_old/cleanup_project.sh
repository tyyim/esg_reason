#!/bin/bash

# Project Cleanup Script - Archive old work and keep only essentials
# Date: 2025-10-13

echo "🧹 Starting project cleanup..."
echo "Creating archive structure..."

# Create archive directory structure
mkdir -p archive_old_project/{
code_old,
results_old,
documentation_old,
analysis_old,
logs_old
}

echo "📦 Archiving old Python scripts..."
# Archive old evaluation scripts
mv *.py archive_old_project/code_old/ 2>/dev/null || true

echo "📊 Archiving old results and predictions..."
# Archive JSON results
mv *_results.json archive_old_project/results_old/ 2>/dev/null || true
mv *_predictions.json archive_old_project/results_old/ 2>/dev/null || true
mv *_evaluation.json archive_old_project/results_old/ 2>/dev/null || true
mv baseline_vs_optimized*.json archive_old_project/results_old/ 2>/dev/null || true
mv unified_eval_*.json archive_old_project/results_old/ 2>/dev/null || true

echo "📝 Archiving old documentation..."
# Archive analysis and comparison docs (keep only essential docs)
mv ANALYSIS_SUMMARY.md archive_old_project/documentation_old/ 2>/dev/null || true
mv BASELINE_COMPARISON*.md archive_old_project/documentation_old/ 2>/dev/null || true
mv BASELINE_VERIFICATION.md archive_old_project/documentation_old/ 2>/dev/null || true
mv BASELINE_REFERENCE.md archive_old_project/documentation_old/ 2>/dev/null || true
mv COMPLETE_EVALUATION_PLAN.md archive_old_project/documentation_old/ 2>/dev/null || true
mv DSPy_RAG_Redesign_Plan.md archive_old_project/documentation_old/ 2>/dev/null || true
mv DSPy_Train_Dev_Test_Split_Plan.md archive_old_project/documentation_old/ 2>/dev/null || true
mv ENHANCED_RAG_IMPLEMENTATION_COMPLETE.md archive_old_project/documentation_old/ 2>/dev/null || true
mv evaluation_analysis_report.md archive_old_project/documentation_old/ 2>/dev/null || true
mv evaluation_metric_gaps_analysis.md archive_old_project/documentation_old/ 2>/dev/null || true

echo "📁 Archiving old analysis files..."
# Archive analysis results
mv *_analysis.json archive_old_project/analysis_old/ 2>/dev/null || true
mv *_analysis.py archive_old_project/code_old/ 2>/dev/null || true
mv false_negative_analysis.json archive_old_project/analysis_old/ 2>/dev/null || true

echo "📋 Archiving logs..."
# Archive logs
mv *.log archive_old_project/logs_old/ 2>/dev/null || true
mv complete_evaluation_log.txt archive_old_project/logs_old/ 2>/dev/null || true

echo "🗂️ Moving existing archive_scripts..."
# Move existing archive
mv archive_scripts archive_old_project/ 2>/dev/null || true

echo "📚 Moving old implementations..."
# Move old DSPy implementation
mv dspy_implementation archive_old_project/code_old/ 2>/dev/null || true
mv dspy_results archive_old_project/results_old/ 2>/dev/null || true

echo "🧪 Moving experiment artifacts..."
# Move experiments and checkpoints
mv experiments archive_old_project/ 2>/dev/null || true
mv checkpoints archive_old_project/ 2>/dev/null || true

echo "🗄️ Moving corrected evaluation results..."
mv corrected_evaluation_results archive_old_project/results_old/ 2>/dev/null || true

echo "✅ Cleanup complete!"
echo ""
echo "📋 Summary:"
echo "  - Old code → archive_old_project/code_old/"
echo "  - Old results → archive_old_project/results_old/"
echo "  - Old docs → archive_old_project/documentation_old/"
echo "  - Old analysis → archive_old_project/analysis_old/"
echo "  - Old logs → archive_old_project/logs_old/"
echo ""
echo "📄 Kept essential files:"
echo "  - CLAUDE.md (project guidelines)"
echo "  - CHANGELOG.md (progress tracking)"
echo "  - Research Plan (Notion sync)"
echo "  - PROJECT_REFACTORING_PLAN.md (implementation plan)"
echo "  - ANLS_EVALUATION_EXPLAINED.md (evaluation reference)"
echo ""
echo "🏗️ Core infrastructure preserved:"
echo "  - src/ (core code)"
echo "  - MMESGBench/ (benchmark)"
echo "  - source_documents/ (PDFs)"
echo "  - mmesgbench_dataset_corrected.json (ground truth)"
echo ""
