# Repository Cleanup Plan
**Date**: October 22, 2025  
**Goal**: Organize for team collaboration, remove clutter, preserve all essential files

---

## 📁 Proposed New Structure

```
CC/
├── README.md                          # Main entry point
├── CHANGELOG.md                       # Historical log
├── RESEARCH_FINDINGS.md               # Complete analysis
├── CLAUDE.md                          # AI assistant guidelines
│
├── dspy_implementation/               # ✅ KEEP - Core implementation
│   ├── data_splits/                   # Train/dev/test splits
│   ├── optimized_modules/             # GEPA/MIPROv2 modules
│   ├── *.py                           # All DSPy scripts
│   └── requirements_dspy.txt
│
├── results/                           # 🆕 NEW - Organized results
│   ├── dev_set/                       # Dev set predictions
│   │   ├── baseline_dev_predictions_20251019_130401.json
│   │   ├── gepa_dev_predictions_20251019_130401.json
│   │   ├── miprov2_dev_predictions_20251019_130401.json
│   │   └── complete_dev_analysis_20251019_130401.json
│   ├── test_set/                      # Test set predictions
│   │   ├── baseline_test_predictions_20251021_225632.json
│   │   ├── gepa_test_predictions_20251021_225632.json
│   │   ├── miprov2_test_predictions_20251021_225632.json
│   │   └── complete_test_analysis_20251021_225632.json
│   └── analysis/                      # Analysis outputs
│       ├── hybrid_system_analysis_results.json
│       ├── domain_knowledge_investigation.json
│       └── string_llm_evaluation_results.json
│
├── analysis/                          # 🆕 NEW - Analysis scripts & reports
│   ├── scripts/
│   │   ├── analyze_test_set_results.py
│   │   ├── hybrid_system_analysis.py
│   │   ├── investigate_domain_knowledge.py
│   │   ├── llm_evaluate_strings.py
│   │   └── ...
│   ├── reports/
│   │   ├── COMPLETE_ERROR_ANALYSIS.md
│   │   ├── HYBRID_SYSTEM_FINDINGS.md
│   │   ├── STRING_LLM_EVALUATION_FINDINGS.md
│   │   ├── TWO_STAGE_AGENTIC_DESIGN.md
│   │   └── DEV_SET_ERROR_ANALYSIS.md
│   └── outputs/                       # Text outputs from analyses
│       ├── hybrid_system_analysis_output.txt
│       ├── string_llm_evaluation_output.txt
│       └── ...
│
├── docs/                              # 🆕 NEW - Additional documentation
│   ├── ANLS_EVALUATION_EXPLAINED.md
│   ├── MODEL_CONFIGURATION.md
│   ├── CODING_BEST_PRACTICES.md
│   ├── GEPA_OPTIMIZED_PROMPTS.md
│   └── TEST_EVALUATION_STATUS.md
│
├── scripts/                           # 🆕 NEW - Utility scripts
│   ├── run_complete_dev_evaluation.py
│   ├── run_complete_test_evaluation.py
│   ├── monitor_test_evaluation.py
│   ├── compare_optimizations_dev_set.py
│   ├── check_test_progress.sh
│   └── download_pdfs.py
│
├── MMESGBench/                        # ✅ KEEP - Dataset source
├── src/                               # ✅ KEEP - Core utilities
├── configs/                           # ✅ KEEP - Configurations
├── logs/                              # ✅ KEEP - Runtime logs
├── cache/                             # ✅ KEEP - Cache data
├── processed_data/                    # ✅ KEEP - Processed documents
├── source_documents/                  # ✅ KEEP - Original PDFs
│
└── archive/                           # 🆕 NEW - Old/outdated files
    ├── old_results/
    │   ├── baseline_rag_results_20251015_*.json
    │   ├── quick_dev_eval_*.json
    │   └── dspy_baseline_dev_checkpoint.json
    ├── old_phases/
    │   ├── phase1_mmesgbench_exact/
    │   ├── phase2_qwen_pgvector/
    │   ├── phase3a_dspy_prompts/
    │   └── phase3b_dspy_query_gen/
    ├── old_scripts/
    │   ├── run_phase*.sh
    │   ├── mmesgbench_exact_evaluation.py
    │   └── analyze_gepa_from_logs.py
    ├── old_docs/
    │   ├── PHASE1_READY.md
    │   ├── RUN_ALL_PHASES.md
    │   ├── PROJECT_REFACTORING_PLAN.md
    │   ├── REFACTORING_MAPPING.md
    │   ├── DATA_INVENTORY.md
    │   ├── CONVERSATION_SUMMARY.md
    │   └── GEPA_FINDINGS_FOR_NOTION.md
    └── archive_old_project/           # ✅ KEEP - Already archived
```

---

## 🗑️ Files to DELETE (Safe to Remove)

### Temporary/Output Files
- `*.txt` output files (already analyzed, info in reports)
- `*.log` files (detailed_error_analysis.log, string_analysis*.log)
- `*.pid` files (indexing.pid)
- Checkpoint files (already have final results)

### Old/Superseded Files
- `splits/` directory (superseded by `dspy_implementation/data_splits/`)
- Old phase scripts: `run_phase*.sh`
- `api_test_qwen2_5-7b-instruct_20251019_125703.json` (test file)

### Directories to Remove
- `__pycache__/` (Python cache)
- `mlruns/` (MLflow tracking - not used in final workflow)
- `checkpoints/` (old optimization checkpoints)
- `notebooks/` (if empty or outdated)
- `test_scripts/` (if superseded)
- `unified_evaluator/` (if not used)
- `tmp/` (temporary files)

---

## ✅ Files to KEEP in Root

### Essential Documentation (Root Level)
- `README.md` - Main entry point ✅
- `CHANGELOG.md` - Historical log ✅
- `RESEARCH_FINDINGS.md` - Complete analysis ✅
- `CLAUDE.md` - AI guidelines ✅
- `.gitignore` ✅
- `.env` (if exists) ✅

### Dataset Files
- `mmesgbench_dataset_corrected.json` - Corrected dataset ✅

---

## 🔄 Migration Steps

1. **Create new directory structure**
   ```bash
   mkdir -p results/{dev_set,test_set,analysis}
   mkdir -p analysis/{scripts,reports,outputs}
   mkdir -p docs
   mkdir -p scripts
   mkdir -p archive/{old_results,old_phases,old_scripts,old_docs}
   ```

2. **Move prediction results**
   ```bash
   # Dev set
   mv *_dev_predictions_20251019_130401.json results/dev_set/
   mv complete_dev_analysis_20251019_130401.json results/dev_set/
   
   # Test set
   mv *_test_predictions_20251021_225632.json results/test_set/
   mv *_test_checkpoint_20251021_225632.json results/test_set/
   mv complete_test_analysis_20251021_225632.json results/test_set/
   
   # Analysis results
   mv hybrid_system_analysis_results.json results/analysis/
   mv domain_knowledge_investigation.json results/analysis/
   mv string_llm_evaluation_results.json results/analysis/
   mv string_questions_detailed_analysis.json results/analysis/
   ```

3. **Move analysis scripts and reports**
   ```bash
   # Scripts
   mv analyze_test_set_results.py analysis/scripts/
   mv hybrid_system_analysis.py analysis/scripts/
   mv investigate_domain_knowledge.py analysis/scripts/
   mv llm_evaluate_strings.py analysis/scripts/
   mv agentic_router_design.py analysis/scripts/
   mv analyze_*.py analysis/scripts/
   mv deep_dive_*.py analysis/scripts/
   mv evaluate_string_with_llm.py analysis/scripts/
   
   # Reports
   mv COMPLETE_ERROR_ANALYSIS.md analysis/reports/
   mv HYBRID_SYSTEM_FINDINGS.md analysis/reports/
   mv STRING_LLM_EVALUATION_FINDINGS.md analysis/reports/
   mv TWO_STAGE_AGENTIC_DESIGN.md analysis/reports/
   mv DEV_SET_ERROR_ANALYSIS.md analysis/reports/
   mv TEST_SET_ERROR_ANALYSIS.md analysis/reports/
   mv DEEP_DIVE_FORMAT_FINDINGS.md analysis/reports/
   
   # Outputs
   mv *_output.txt analysis/outputs/
   ```

4. **Move documentation**
   ```bash
   mv ANLS_EVALUATION_EXPLAINED.md docs/
   mv MODEL_CONFIGURATION.md docs/
   mv CODING_BEST_PRACTICES.md docs/
   mv GEPA_OPTIMIZED_PROMPTS.md docs/
   mv TEST_EVALUATION_STATUS.md docs/
   ```

5. **Move utility scripts**
   ```bash
   mv run_complete_*.py scripts/
   mv monitor_test_evaluation.py scripts/
   mv compare_optimizations_dev_set.py scripts/
   mv check_test_progress.sh scripts/
   mv download_pdfs.py scripts/
   ```

6. **Archive old files**
   ```bash
   # Old results
   mv baseline_rag_results_*.json archive/old_results/
   mv quick_dev_eval_*.json archive/old_results/
   mv dspy_baseline_dev_checkpoint.json archive/old_results/
   
   # Old phases
   mv phase1_* archive/old_phases/
   mv phase2_* archive/old_phases/
   mv phase3a_* archive/old_phases/
   mv phase3b_* archive/old_phases/
   
   # Old scripts
   mv run_phase*.sh archive/old_scripts/
   mv mmesgbench_exact_evaluation.py archive/old_scripts/
   
   # Old docs
   mv PHASE1_READY.md archive/old_docs/
   mv RUN_ALL_PHASES.md archive/old_docs/
   mv PROJECT_REFACTORING_PLAN.md archive/old_docs/
   mv REFACTORING_MAPPING.md archive/old_docs/
   mv DATA_INVENTORY.md archive/old_docs/
   mv CONVERSATION_SUMMARY.md archive/old_docs/
   mv GEPA_FINDINGS_FOR_NOTION.md archive/old_docs/
   ```

7. **Delete unnecessary files**
   ```bash
   # Temporary outputs
   rm -f *.txt  # All .txt output files
   rm -f *.log  # All log files
   rm -f *.pid  # PID files
   
   # Directories
   rm -rf __pycache__
   rm -rf mlruns
   rm -rf checkpoints
   rm -rf tmp
   
   # Old splits (superseded by dspy_implementation/data_splits/)
   rm -rf splits
   ```

---

## 📝 Update README.md

After cleanup, update README.md to document new structure:

```markdown
## 📁 Repository Structure

- `dspy_implementation/` - Core DSPy implementation and optimized modules
- `results/` - Prediction results and analysis outputs
  - `dev_set/` - Development set evaluations (93 questions)
  - `test_set/` - Test set evaluations (654 questions)
  - `analysis/` - Analysis result files (JSON)
- `analysis/` - Analysis scripts and comprehensive reports
  - `scripts/` - Python scripts for error analysis, hybrid systems, etc.
  - `reports/` - Markdown reports (error analysis, findings, designs)
  - `outputs/` - Text outputs from analysis runs
- `docs/` - Additional documentation
- `scripts/` - Utility scripts for evaluation and monitoring
- `MMESGBench/` - Original benchmark dataset and evaluation code
- `src/` - Core utility modules
- `archive/` - Archived old phases, scripts, and results

## 🎯 Key Files

**Authoritative Results**:
- `results/dev_set/*_20251019_130401.json` - Dev set predictions (baseline, GEPA, MIPROv2)
- `results/test_set/*_20251021_225632.json` - Test set predictions

**Analysis Reports**:
- `analysis/reports/COMPLETE_ERROR_ANALYSIS.md` - Comprehensive error analysis (dev + test)
- `analysis/reports/HYBRID_SYSTEM_FINDINGS.md` - Format-based routing (50.2% accuracy)
- `analysis/reports/TWO_STAGE_AGENTIC_DESIGN.md` - Two-stage agentic system design

**Documentation**:
- `README.md` - This file
- `RESEARCH_FINDINGS.md` - Complete research analysis
- `CHANGELOG.md` - Development history
- `CLAUDE.md` - AI collaboration guidelines
```

---

## ✅ Verification Checklist

After cleanup:
- [ ] All authoritative result files in `results/` directory
- [ ] All analysis scripts in `analysis/scripts/`
- [ ] All reports in `analysis/reports/`
- [ ] Root directory clean (only 4-5 essential docs)
- [ ] `dspy_implementation/` intact and functional
- [ ] README.md updated with new structure
- [ ] .gitignore updated to exclude outputs
- [ ] Git status clean (no uncommitted changes to important files)
- [ ] Test that evaluation scripts still work

---

## 🚨 Safety Notes

**DO NOT DELETE**:
- `dspy_implementation/` - Core functionality
- `MMESGBench/` - Dataset source
- `src/` - Utility modules
- `configs/` - Configuration files
- `processed_data/` - Processed documents
- `source_documents/` - Original PDFs
- `cache/` - Cache for performance
- `logs/` - Runtime logs (may be needed for debugging)
- `archive_old_project/` - Already archived historical work

**Safe to delete (already captured in reports)**:
- `*.txt` output files
- `*.log` files (string_analysis.log, detailed_error_analysis.log)
- Checkpoint JSON files (intermediate results)
- `__pycache__`, `mlruns`, `checkpoints`, `tmp` directories

