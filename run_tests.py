#!/usr/bin/env python3
"""
Run all tests for the MkDocs Protobuf Plugin
"""
import unittest
import sys
import os

if __name__ == "__main__":
    print("Starting MkDocs Protobuf Plugin test suite...")

    # Make sure we're using the current package code
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # Discover and run tests with more detailed output
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test")
    print(f"Looking for tests in directory: {test_dir}")

    test_loader = unittest.TestLoader()
    try:
        test_suite = test_loader.discover("test", pattern="test_*.py")
        print(f"Found {test_suite.countTestCases()} test cases")

        # Force output buffer to flush
        sys.stdout.flush()

        # Run tests with verbose output
        test_runner = unittest.TextTestRunner(verbosity=2, buffer=False)
        result = test_runner.run(test_suite)

        # Display summary
        print("\nTest Summary:")
        print(f"  Ran {result.testsRun} tests")
        print(
            f"  Successes: {result.testsRun - len(result.failures) - len(result.errors)}"
        )
        print(f"  Failures: {len(result.failures)}")
        print(f"  Errors: {len(result.errors)}")
        print(f"  Overall Status: {'SUCCESS' if result.wasSuccessful() else 'FAILED'}")

        # Exit with non-zero code if tests failed
        sys.exit(0 if result.wasSuccessful() else 1)

    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)
