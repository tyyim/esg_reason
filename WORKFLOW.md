# Development Workflow

## Purpose
Prevent repeating mistakes and ensure systematic progress tracking.

---

## 🚦 Before Starting ANY Task

### 1. Context Review (5 min)
```bash
# Read current status
cat CLAUDE.md  # Current focus + critical files

# Check recent changes
tail -50 CHANGELOG.md  # What was done recently

# Review plan
# Check Research Plan for overall goals
```

### 2. Document Intent
- [ ] Update `CHANGELOG.md` with:
  - What you're about to do
  - Why you're doing it
  - Expected outcome

- [ ] Update todo list (TodoWrite tool) with specific task

### 3. Configuration Verification Checklist

For optimization/evaluation tasks:

- [ ] **Dataset**: Correct file? Corrected version?
- [ ] **Evaluation set**: Train/Dev/Test - which one? Same for baseline & optimized?
- [ ] **Metadata**: Does architecture description match what we're actually doing?
- [ ] **Parameters**: Do they match the test description (e.g., query_optimization: True/False)?
- [ ] **File naming**: Do output files match the architecture (baseline_* vs enhanced_*)?
- [ ] **Comparison logic**: Are we comparing apples to apples?

**STOP and review** before running: "Does this configuration make sense for what we're testing?"

---

## 🔄 During Work

### Code Changes
1. **One thing at a time**: Don't mix multiple fixes/features
2. **Test after each change**: Don't accumulate untested changes
3. **Document inline**: Add comments explaining WHY, not just WHAT

### Bug Fixes
When you find a bug:

1. **Document immediately** in CHANGELOG.md:
   ```markdown
   ### Bug: [Brief description]
   - **Symptom**: What went wrong
   - **Root cause**: Why it happened
   - **Fix**: What changed
   - **Test**: How to verify it's fixed
   ```

2. **Add to CLAUDE.md** under "Known Issues & Fixes"

3. **Check if we've seen this before**: Search CHANGELOG for similar issues

### Running Experiments
```bash
# Create dated log directory
mkdir -p logs
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Run with logging
python script.py 2>&1 | tee logs/experiment_${TIMESTAMP}.log

# Document in CHANGELOG immediately after
```

---

## ✅ After Completing Task

### 1. Update Documentation (Required - Don't Skip!)

**CLAUDE.md** updates:
```bash
# Update "Current Focus" if status changed
# Update "Known Issues & Fixes" if bugs found/fixed
# Update "Critical Files" if new important files created
```

**CHANGELOG.md** updates:
```markdown
### [Date] - [Task Name]

#### What We Did
- Specific actions taken
- Files changed

#### Results
- Quantitative results (accuracy, time, etc.)
- What worked / didn't work

#### Lessons Learned
- Key insights
- Mistakes to avoid next time
```

### 2. Clean Up
- [ ] Move debug/test scripts to `archive/debug_[date]/`
- [ ] Remove temporary files
- [ ] Delete old log files (keep only recent + milestone logs)

### 3. Update Todo List
- [ ] Mark completed tasks as done
- [ ] Add any new tasks discovered
- [ ] Ensure next task is clear

### 4. Git Commit
```bash
# Stage changes
git add [relevant files]

# Commit with clear message
git commit -m "feat/fix: [What changed]

- Specific change 1
- Specific change 2

Results: [Key metric/outcome]"
```

---

## 🎯 Decision Checkpoints

### Before Optimization
- [ ] Have we documented the current baseline on the SAME dataset we'll evaluate optimized model on?
- [ ] Do we know what components we're optimizing?
- [ ] Have we verified the configuration matches our intent?
- [ ] Have we set realistic expectations/targets?

### Before Evaluation
- [ ] Are we using the correct dataset? (train/dev/test)
- [ ] Are we comparing against the right baseline?
- [ ] Will this evaluation answer our research question?

### After Results
- [ ] Did we document the results in CHANGELOG?
- [ ] Did we update CLAUDE.md with new baseline/status?
- [ ] Did we analyze WHY results were what they were?
- [ ] Do we know what to do next?

---

## 📋 Common Mistakes to Avoid

From CHANGELOG - mistakes we've made:

1. **Inconsistent datasets**: Comparing 20-sample to full dataset
2. **Metadata mismatch**: Saying "query optimization" when not doing it
3. **Not documenting immediately**: Forgetting what we did or why
4. **Skipping verification**: Running without checking configuration
5. **Not updating CLAUDE.md**: Losing track of current status
6. **Accumulating debug scripts**: Codebase becomes messy

---

## 🔧 File Organization

### Keep These Clean
```
/Users/victoryim/Local_Git/CC/
├── CLAUDE.md                   # Always up to date
├── CHANGELOG.md                # Every change documented
├── WORKFLOW.md                 # This file
├── dspy_implementation/        # Core modules (production code)
├── logs/                       # Dated logs only
└── archive/                    # Old scripts, moved regularly
```

### Move to Archive Regularly
```bash
# Monthly cleanup
mkdir -p archive/debug_$(date +%Y%m)/
mv debug_*.py archive/debug_$(date +%Y%m)/
mv test_*.py archive/debug_$(date +%Y%m)/
mv *_old.py archive/debug_$(date +%Y%m)/
```

---

## 💡 When in Doubt

1. **Read CHANGELOG**: Have we tried this before?
2. **Check CLAUDE.md**: What's our current focus?
3. **Verify config**: Does it match what we SAY we're doing?
4. **Document first**: Write down what you're about to do
5. **One step at a time**: Don't mix multiple changes

---

## Example: Full Cycle

```bash
# 1. BEFORE: Read context
cat CLAUDE.md
tail -20 CHANGELOG.md

# 2. BEFORE: Document intent
echo "### 2025-10-12 - Testing baseline optimization" >> CHANGELOG.md
# ... write details ...

# 3. BEFORE: Verify config
# Go through checklist above

# 4. DURING: Run with logging
python enhanced_miprov2_optimization.py 2>&1 | tee logs/baseline_opt_20251012.log

# 5. AFTER: Document results
# Update CHANGELOG with results
# Update CLAUDE.md if status changed

# 6. AFTER: Clean up
mv old_test_script.py archive/debug_202510/

# 7. AFTER: Commit
git add CLAUDE.md CHANGELOG.md dspy_implementation/
git commit -m "feat: Baseline prompt optimization test

- Fixed metadata inconsistencies
- Evaluated on full dev set for fair comparison
- Results: TBD"
```

---

## This Workflow Prevents

- ✅ Repeating fixed bugs
- ✅ Configuration mistakes
- ✅ Lost context
- ✅ Inconsistent comparisons
- ✅ Messy codebase
- ✅ Unclear progress

**Follow this workflow for EVERY task, no exceptions.**
