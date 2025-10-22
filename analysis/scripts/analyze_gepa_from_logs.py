#!/usr/bin/env python3
"""
Parse GEPA optimization logs to extract question-level results
WITHOUT re-running any evaluations.

Uses the existing log file: logs/gepa_optimization/gepa_skip_baseline_20251018_150802.log
"""

import re
import json
from datetime import datetime

def parse_gepa_log():
    """Parse the GEPA optimization log to extract results."""

    log_file = "logs/gepa_optimization/gepa_skip_baseline_20251018_150802.log"

    print("\n" + "="*80)
    print("PARSING GEPA OPTIMIZATION LOG")
    print("="*80)
    print(f"\nLog file: {log_file}")

    with open(log_file, 'r') as f:
        log_content = f.read()

    # Extract key findings
    print("\n📊 KEY FINDINGS FROM LOG:")
    print("-"*80)

    # Find baseline statement
    baseline_match = re.search(r'Baseline.*?(\d+\.\d+)%', log_content)
    if baseline_match:
        baseline_pct = baseline_match.group(1)
        print(f"\n✅ Baseline (stated): {baseline_pct}%")

    # Find final GEPA result
    final_gepa = re.search(r'Average Metric: (\d+\.?\d*) / (\d+) \((\d+\.\d+)%\).*?100%', log_content)
    if final_gepa:
        correct = final_gepa.group(1)
        total = final_gepa.group(2)
        pct = final_gepa.group(3)
        print(f"✅ GEPA Final: {pct}% ({correct}/{total} correct)")

        # Calculate difference
        if baseline_match:
            diff = float(pct) - float(baseline_pct)
            print(f"\n📉 Performance Change: {diff:+.1f}%")
            print(f"   Questions changed: {int(float(baseline_pct)/100*int(total)) - int(float(correct))}")

    # Find iterations info
    iterations = re.findall(r'INFO dspy\.teleprompt\.gepa.*?iteration (\d+)', log_content)
    if iterations:
        print(f"\n🔄 GEPA Iterations: {len(iterations)} iterations completed")

    # Find program selection
    program_match = re.search(r'Selected Program #(\d+)', log_content)
    if program_match:
        program_num = program_match.group(1)
        print(f"🎯 Best Program: Program #{program_num}")

    # Analyze prompt evolution
    print("\n" + "-"*80)
    print("PROMPT EVOLUTION ANALYSIS")
    print("-"*80)

    # Count reflection iterations
    reflection_sections = re.findall(r'(Feedback:.*?(?=\n\n|\nBy following))', log_content, re.DOTALL)
    print(f"\n📝 Reflection Feedback Instances: {len(reflection_sections)}")

    if reflection_sections:
        print("\nSample Reflection Feedback:")
        for i, feedback in enumerate(reflection_sections[:3], 1):
            clean_feedback = feedback.replace('\n', ' ').strip()[:200]
            print(f"\n{i}. {clean_feedback}...")

    # Find evaluation errors
    print("\n" + "-"*80)
    print("EVALUATION ISSUES")
    print("-"*80)

    connection_errors = re.findall(r'ERROR:dashscope.*?Connection', log_content)
    print(f"\n⚠️  Connection Errors: {len(connection_errors)} times")

    syntax_errors = re.findall(r'SyntaxError', log_content)
    if syntax_errors:
        print(f"⚠️  SyntaxErrors: {len(syntax_errors)} times")

    # Extract performance over iterations
    print("\n" + "-"*80)
    print("PERFORMANCE PROGRESSION")
    print("-"*80)

    # Find validation scores during optimization
    val_scores = re.findall(r'INFO dspy\.evaluate\.evaluate: Average Metric: ([\d.]+) / (\d+) \(([\d.]+)%\)', log_content)

    if val_scores:
        print("\n📈 Validation Performance During Optimization:")
        print(f"   Total evaluations: {len(val_scores)}")

        # Show trend
        scores = [float(s[2]) for s in val_scores[-10:]]  # Last 10
        if len(scores) >= 2:
            print(f"\n   Last 10 evaluations:")
            for i, score in enumerate(scores, 1):
                print(f"      {i}. {score:.1f}%")

            trend = scores[-1] - scores[0]
            print(f"\n   Trend (last 10): {trend:+.1f}%")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    print(f"""
From the GEPA optimization log, we can confirm:

1. **Baseline Performance**: {baseline_pct if baseline_match else 'Not found'}%
   - This was a STATED value, not re-evaluated
   - From previous run

2. **GEPA Performance**: {pct if final_gepa else 'Not found'}%
   - Evaluated during final evaluation
   - {correct if final_gepa else '?'}/{total if final_gepa else '?'} questions correct

3. **Change**: {diff:+.1f}% ({int(float(baseline_pct)/100*int(total)) - int(float(correct))} questions) if baseline_match and final_gepa else 'Cannot calculate'

4. **Optimization Process**:
   - {len(iterations)} iterations completed
   - Selected Program #{program_num if program_match else '?'}
   - {len(connection_errors)} connection errors encountered
   - {len(reflection_sections)} reflection feedback instances

5. **LIMITATION**:
   ⚠️  The log does NOT contain question-level predictions
   ⚠️  We only have aggregate scores, not individual Q&A pairs
   ⚠️  Cannot perform detailed error analysis without re-evaluation

   To get question-level analysis, we would need to:
   - Re-run baseline evaluation (saves predictions)
   - Load GEPA module and evaluate on dev set
   - Compare predictions question-by-question
    """)

    # Recommendation
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    print("""
The user is RIGHT: We jumped to conclusions without question-level analysis.

What we actually know from logs:
- ✅ Aggregate performance: 58.1% → 54.8% (-3.3%)
- ✅ GEPA completed 32 iterations successfully
- ✅ GEPA's prompts became much longer (7,749 chars vs 0)
- ❌ Which 3 questions degraded? UNKNOWN
- ❌ Are errors clustered by format? UNKNOWN
- ❌ Did evaluator issues affect results? UNKNOWN

Next steps:
1. Accept we don't have question-level data from current logs
2. Either:
   a) Re-run evaluations to get question-level data (slow but complete)
   b) Accept aggregate findings and document limitations
   c) Use test set for validation (654 questions, more stable)
    """)


if __name__ == "__main__":
    parse_gepa_log()
