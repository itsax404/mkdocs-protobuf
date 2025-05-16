# MkDocs Protobuf Plugin Tests

This directory contains tests for the MkDocs Protobuf Plugin.

## Test Files

- `test_plugin.py`: Tests the core functionality of the plugin
- `test_nested_structure.py`: Tests handling of nested proto file directories
- `test_example_setup.py`: Tests the example proto file setup

## Running Tests

Run all tests using the script in the root directory:

```bash
./run_tests.py
```

Or run individual test files:

```bash
python -m unittest test/test_plugin.py
python -m unittest test/test_nested_structure.py
python -m unittest test/test_example_setup.py
```

## Test Data

The tests use a combination of:

1. Temporary files created during test execution
2. Proto files in the `proto` directory

## Adding New Tests

When adding new tests:

1. Create a new test file in the `test` directory
2. Follow the unittest framework pattern
3. Use setUp/tearDown for proper test isolation
4. Update this README if adding significant new test categories
