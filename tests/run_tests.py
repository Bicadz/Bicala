#!/usr/bin/env python3
"""
Bicala Core Protection Test Runner
Automated test suite for Beta 5.1.24.3 frozen state validation
"""

import subprocess
import sys
import os
from pathlib import Path

# Get the project root directory (parent of tests/)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
RUN_SCRIPT = PROJECT_ROOT / "run.py"

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def run_test(test_file, expected_error_code=None, should_succeed=False):
    """
    Run a single Bicala test file and check for expected behavior.
    
    Args:
        test_file: Path to the .bica test file
        expected_error_code: Expected error code in output (e.g., "N002")
        should_succeed: If True, test should exit with code 0 and have no errors
    
    Returns:
        tuple: (success: bool, message: str)
    """
    test_path = SCRIPT_DIR / test_file
    
    print(f"Running: {test_file}...", end=" ")
    
    try:
        # Run the test file using python run.py
        result = subprocess.run(
            [sys.executable, str(RUN_SCRIPT), str(test_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        output = result.stdout + result.stderr
        
        if should_succeed:
            # Test should succeed (exit code 0, no error messages)
            if result.returncode == 0 and "ERROR" not in output.upper() and "N002" not in output and "T002" not in output and "N003" not in output:
                print(f"{GREEN}PASSED{RESET}")
                return True, "Test passed as expected"
            else:
                print(f"{RED}FAILED{RESET}")
                print(f"  Expected: Success (exit code 0, no errors)")
                print(f"  Got: Exit code {result.returncode}")
                if output.strip():
                    print(f"  Output: {output[:200]}")
                return False, "Test failed unexpectedly"
        
        else:
            # Test should fail with specific error code
            if expected_error_code and expected_error_code in output:
                print(f"{GREEN}PASSED{RESET}")
                return True, f"Error code {expected_error_code} detected as expected"
            else:
                print(f"{RED}FAILED{RESET}")
                print(f"  Expected error code: {expected_error_code}")
                print(f"  Exit code: {result.returncode}")
                if output.strip():
                    print(f"  Output: {output[:300]}")
                return False, f"Expected error code {expected_error_code} not found"
    
    except subprocess.TimeoutExpired:
        print(f"{RED}FAILED{RESET}")
        print(f"  Test timed out after 10 seconds")
        return False, "Test timed out"
    
    except Exception as e:
        print(f"{RED}FAILED{RESET}")
        print(f"  Exception: {str(e)}")
        return False, f"Exception during test execution: {str(e)}"


def main():
    """Run all tests and report results."""
    
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}Bicala Core Protection Test Suite{RESET}")
    print(f"{BOLD}Beta 5.1.24.3 - Frozen State Validation{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")
    print()
    
    # Define test cases
    test_cases = [
        ("test_success.bica", None, True, "Positive path - const and type constraints"),
        ("test_err_n002.bica", "N002", False, "N002 - Const reassignment"),
        ("test_err_t002.bica", "T002", False, "T002 - Type mismatch"),
        ("test_err_n003_keyword.bica", "N003", False, "N003 - Protected constant deletion"),
        ("test_err_n003_builtin.bica", "N003", False, "N003 - Protected builtin deletion"),
    ]
    
    # Run all tests
    results = []
    for test_file, expected_error, should_succeed, description in test_cases:
        success, message = run_test(test_file, expected_error, should_succeed)
        results.append((test_file, success, description, message))
        print()
    
    # Print summary
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}Test Summary{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")
    
    passed = sum(1 for _, success, _, _ in results if success)
    failed = len(results) - passed
    
    for test_file, success, description, message in results:
        status = f"{GREEN}PASSED{RESET}" if success else f"{RED}FAILED{RESET}"
        print(f"{status} - {description}")
        if not success:
            print(f"        {message}")
    
    print()
    print(f"{BOLD}Total: {passed} PASSED, {failed} FAILED{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")
    
    # Exit with appropriate code
    if failed > 0:
        sys.exit(1)
    else:
        print(f"{GREEN}{BOLD}All tests passed! Core protections are active.{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
