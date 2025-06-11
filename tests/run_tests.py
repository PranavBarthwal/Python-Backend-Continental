#!/usr/bin/env python3
"""
Comprehensive test runner for PHR Healthcare API
Executes all unit tests and generates coverage reports
"""

import unittest
import sys
import os
import logging
from io import StringIO

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)


class TestResult:
    def __init__(self):
        self.tests_run = 0
        self.failures = 0
        self.errors = 0
        self.skipped = 0
        self.success_rate = 0.0
        self.details = []


def run_test_suite():
    """Run all tests and return comprehensive results"""
    
    # Discover and load all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Capture test output
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        buffer=True
    )
    
    print("=" * 70)
    print("PHR Healthcare API - Test Suite")
    print("=" * 70)
    
    # Run tests
    result = runner.run(suite)
    
    # Process results
    test_result = TestResult()
    test_result.tests_run = result.testsRun
    test_result.failures = len(result.failures)
    test_result.errors = len(result.errors)
    test_result.skipped = len(result.skipped)
    
    if test_result.tests_run > 0:
        successful_tests = test_result.tests_run - test_result.failures - test_result.errors
        test_result.success_rate = (successful_tests / test_result.tests_run) * 100
    
    # Collect failure details
    for failure in result.failures:
        test_result.details.append({
            'type': 'FAILURE',
            'test': str(failure[0]),
            'message': failure[1]
        })
    
    for error in result.errors:
        test_result.details.append({
            'type': 'ERROR',
            'test': str(error[0]),
            'message': error[1]
        })
    
    return test_result, stream.getvalue()


def print_test_summary(test_result, output):
    """Print comprehensive test summary"""
    
    print(f"\nTest Results Summary:")
    print("-" * 50)
    print(f"Tests Run:     {test_result.tests_run}")
    print(f"Successes:     {test_result.tests_run - test_result.failures - test_result.errors}")
    print(f"Failures:      {test_result.failures}")
    print(f"Errors:        {test_result.errors}")
    print(f"Skipped:       {test_result.skipped}")
    print(f"Success Rate:  {test_result.success_rate:.1f}%")
    
    # Color coding for success rate
    if test_result.success_rate >= 90:
        status = "EXCELLENT ✓"
    elif test_result.success_rate >= 80:
        status = "GOOD ✓"
    elif test_result.success_rate >= 70:
        status = "ACCEPTABLE ⚠"
    else:
        status = "NEEDS IMPROVEMENT ✗"
    
    print(f"Overall Status: {status}")
    
    # Print failure details
    if test_result.details:
        print(f"\nDetailed Failure Analysis:")
        print("-" * 50)
        for i, detail in enumerate(test_result.details, 1):
            print(f"{i}. {detail['type']}: {detail['test']}")
            print(f"   Message: {detail['message'].split('AssertionError:')[-1].strip()}")
            print()
    
    # Print test categories coverage
    print(f"\nTest Coverage by Category:")
    print("-" * 50)
    categories = {
        'Authentication': ['test_auth'],
        'API Routes': ['test_api_routes'],
        'AI Services': ['test_ai_services'],
        'Database Models': ['test_models'],
        'HMIS Integration': ['test_hmis']
    }
    
    for category, patterns in categories.items():
        covered = any(pattern in output.lower() for pattern in patterns)
        status = "✓ Covered" if covered else "✗ Missing"
        print(f"{category:20} {status}")


def run_specific_test(test_name):
    """Run a specific test module"""
    try:
        module = __import__(f'test_{test_name}')
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()
    except ImportError:
        print(f"Test module 'test_{test_name}' not found")
        return False


def main():
    """Main test runner function"""
    
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        print(f"Running specific test: {test_name}")
        success = run_specific_test(test_name)
        sys.exit(0 if success else 1)
    
    # Run all tests
    try:
        test_result, output = run_test_suite()
        print_test_summary(test_result, output)
        
        # Exit with appropriate code
        if test_result.failures == 0 and test_result.errors == 0:
            print(f"\n🎉 All tests passed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ Some tests failed. Please review the failures above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error running tests: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()