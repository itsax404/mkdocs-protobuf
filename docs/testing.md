# Testing Guide

This document provides an overview of the testing approach for the MkDocs Protobuf Plugin and instructions for running and extending the test suite.

## Test Architecture

The MkDocs Protobuf Plugin uses Python's built-in `unittest` framework for testing. The tests are organized into several modules focusing on different aspects of the plugin:

1. **Core Plugin Tests** (`test_plugin.py`): Tests the main plugin functionality and integration with MkDocs
2. **Nested Structure Tests** (`test_nested_structure.py`): Tests handling of nested proto file directories
3. **Example Setup Tests** (`test_example_setup.py`): Tests the example project setup and validation
4. **API Generation Tests** (`test_api.py`): Tests specific API documentation generation features

## Running Tests

### Running the Complete Test Suite

To run all tests, use the provided script:

```bash
./run_tests.py
```

This will discover and run all test cases in the `test` directory.

### Running Individual Test Modules

To run specific test modules:

```bash
python -m unittest test/test_plugin.py
python -m unittest test/test_nested_structure.py
```

### Running Specific Test Cases

To run a specific test case or method:

```bash
python -m unittest test.test_plugin.TestProtobufPlugin
python -m unittest test.test_plugin.TestProtobufPlugin.test_plugin_initialization
```

## Test Coverage

The test suite aims to provide comprehensive coverage of the plugin's functionality:

### Functional Coverage

- **Import Resolution**: Tests for resolving import paths between proto files
- **Message Extraction**: Tests for extracting message definitions from proto files
- **Service Documentation**: Tests for documenting service methods and RPCs
- **Cross-References**: Tests for creating links between related proto elements
- **Directory Structure**: Tests for maintaining directory structure in generated docs
- **File Watching**: Tests for watching and reprocessing changed proto files

### Edge Cases

- **Circular Imports**: Tests handling of circular import dependencies
- **Empty Protos**: Tests for empty or minimal proto files
- **Custom Options**: Tests for proto files with custom options
- **Special Characters**: Tests for handling special characters in comments

## Adding New Tests

When adding new tests:

1. Create or extend test classes in the appropriate test module
2. Follow the unittest pattern with setUp/tearDown methods
3. Use descriptive test method names starting with `test_`
4. Include assertions to validate expected behavior

Example:

```python
def test_message_extraction_with_comments(self):
    """Test that comments are properly extracted and included in documentation."""
    # Test setup code...
    self.assertIn('Expected comment text', generated_content)
```

## Mocking and Test Data

The test suite uses a combination of approaches for test data:

1. **Temporary Files**: Many tests create temporary proto files during test execution
2. **Proto Files**: Some tests use the proto files in the `proto` directory
3. **Mocking**: Complex MkDocs interactions may use mock objects

## Continuous Integration

Tests are run automatically on pull requests and commits to the main branch. All tests must pass before merging changes.

## Test-Driven Development

We encourage a test-driven development (TDD) approach:

1. Write a failing test for the feature or fix
2. Implement the feature or fix
3. Verify that the test passes
4. Refactor code while ensuring tests continue to pass

## Debugging Tests

When tests fail, you can use Python's debugging tools:

```bash
# Run with higher verbosity
python -m unittest test/test_plugin.py -v

# Use Python debugger
python -m pdb -m unittest test/test_plugin.py
```

## Test Design Principles

Our tests follow these principles:

1. **Independence**: Tests should not depend on each other
2. **Isolation**: Each test should run in isolation with proper setup/teardown
3. **Clarity**: Test names and assertions should clearly indicate what's being tested
4. **Completeness**: Test both normal operation and error conditions
