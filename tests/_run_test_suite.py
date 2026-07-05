#!/usr/bin/env python
"""
Test Suite Runner for Bicala
Runs all .bica files in the tests directory and reports results
"""

import os
import subprocess
import sys
from pathlib import Path

def run_test_file(test_file):
    """Run a single .bica test file and return result"""
    try:
        # Get the interpreter script path
        interpreter_path = Path(__file__).parent.parent / "run.py"
        result = subprocess.run(
            [sys.executable, str(interpreter_path), str(test_file)],
            capture_output=True,
            text=True,
            timeout=10  # 10 second timeout per test
        )
        return {
            "file": test_file.name,
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "file": test_file.name,
            "success": False,
            "output": "",
            "error": "TIMEOUT"
        }
    except Exception as e:
        return {
            "file": test_file.name,
            "success": False,
            "output": "",
            "error": str(e)
        }

def main():
    # Find all .bica files in the tests directory
    test_dir = Path(__file__).parent
    test_files = sorted(test_dir.glob("*.bica"))
    
    print(f"=== BICALA TEST SUITE RUNNER ===")
    print(f"Found {len(test_files)} test files")
    print()
    
    results = []
    passed_count = 0
    failed_count = 0
    
    for test_file in test_files:
        print(f"Running: {test_file.name}...", end=" ")
        result = run_test_file(test_file)
        results.append(result)
        
        if result["success"]:
            print("[PASS]")
            passed_count += 1
        else:
            print("[FAIL]")
            failed_count += 1
            if result["error"]:
                print(f"  Error: {result['error'][:100]}...")
    
    print()
    print("=== TEST SUITE SUMMARY ===")
    print(f"Total tests: {len(test_files)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print(f"Success rate: {(passed_count/len(test_files)*100):.1f}%")
    
    # Detailed results for failed tests
    if failed_count > 0:
        print()
        print("=== FAILED TEST DETAILS ===")
        for result in results:
            if not result["success"]:
                print(f"\n{result['file']}:")
                if result["error"]:
                    print(f"  Error: {result['error']}")
                if result["output"]:
                    print(f"  Output: {result['output'][:200]}...")
    
    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
