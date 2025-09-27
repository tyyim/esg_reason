#!/usr/bin/env python3
"""
Launch Autonomous ColBERT Evaluation
Simple launcher script with environment setup and monitoring.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def setup_environment():
    """Set up environment variables"""
    # Required API key
    api_key = "sk-398b62f740a643458bf06c26f0324df1"
    os.environ["DASHSCOPE_API_KEY"] = api_key
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    print("✅ Environment variables set")

def check_dependencies():
    """Check if required files exist"""
    required_files = [
        "./MMESGBench/dataset/samples.json",
        "./autonomous_colbert_evaluator.py"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False

    print("✅ All required files found")
    return True

def run_evaluation():
    """Run the autonomous evaluation"""
    print("🚀 Starting Autonomous ColBERT Evaluation...")
    print("📊 This will process all 933 questions with parallel API calls")
    print("⏱️  Estimated time: 45-90 minutes (depending on API speed)")
    print("💾 Progress will be saved automatically every 25 questions")
    print("🛑 You can stop anytime with Ctrl+C - progress will be saved")
    print("-" * 60)

    try:
        # Run the evaluation
        result = subprocess.run([
            sys.executable, "autonomous_colbert_evaluator.py"
        ], check=True)

        print("\n🎉 Evaluation completed successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Evaluation failed with exit code {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Evaluation interrupted by user")
        print("💾 Progress has been saved - you can resume later")
        return False

def check_results():
    """Check if results files were created"""
    result_files = [
        "autonomous_colbert_checkpoint.json",
        "autonomous_colbert_results.json",
        "autonomous_evaluation.log"
    ]

    found_files = []
    for file_path in result_files:
        if Path(file_path).exists():
            file_size = Path(file_path).stat().st_size
            found_files.append(f"{file_path} ({file_size:,} bytes)")

    if found_files:
        print("\n📁 Generated files:")
        for file_info in found_files:
            print(f"  📄 {file_info}")

    return len(found_files) > 0

def main():
    """Main launcher function"""
    print("🤖 Autonomous ColBERT Evaluation Launcher")
    print("=" * 50)

    # Setup
    setup_environment()

    if not check_dependencies():
        print("\n❌ Please ensure all required files are available")
        return 1

    # Run evaluation
    success = run_evaluation()

    # Check results
    check_results()

    if success:
        print("\n✅ Autonomous evaluation completed successfully!")
        print("📊 Check the results files for detailed analysis")
        return 0
    else:
        print("\n⚠️  Evaluation was interrupted or failed")
        print("📄 Check autonomous_evaluation.log for details")
        print("🔄 You can restart to resume from the last checkpoint")
        return 1

if __name__ == "__main__":
    sys.exit(main())