# Contributing to MkDocs Protobuf Plugin

Thank you for your interest in contributing to the MkDocs Protobuf Plugin! This guide will help you get started with contributing to this project.

## Development Setup

### Prerequisites

- Python 3.8 or newer
- pip
- virtualenv (optional, but recommended)

### Setting Up the Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mkdocs-protobuf.git
   cd mkdocs-protobuf
   ```

2. Create and activate a virtual environment (optional):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install all dependencies using requirements.txt:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Testing

### Running Tests

Run the test suite using the provided script:

```bash
./run_tests.py
```

Or run individual test modules:

```bash
python -m unittest test/test_plugin.py
```

### Adding Tests

When adding new features or fixing bugs, please add appropriate tests:

1. Create test files in the `test/` directory
2. Follow the unittest framework pattern
3. Include tests for both normal operation and edge cases
4. Make sure to test any file paths or import resolution changes

## Code Style

We follow PEP 8 guidelines for Python code. Please ensure your code is formatted accordingly:

```bash
# Install tools
pip install black flake8

# Format code
black mkdocs_protobuf_plugin/

# Check code style
flake8 mkdocs_protobuf_plugin/
```

## Documentation

### Building Documentation

To build and preview the documentation locally:

```bash
mkdocs build
mkdocs serve
```

Then visit `http://localhost:8000` in your browser.

### Documentation Standards

- Keep docstrings up-to-date with code changes
- Use Markdown for documentation
- Include examples for new features
- Update the README.md with relevant changes

## Git Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests to ensure they pass
5. Commit your changes with clear messages
6. Push your branch to your fork
7. Submit a pull request

## Pull Request Guidelines

When submitting a pull request:

1. Clearly describe the changes and their purpose
2. Link to any related issues
3. Include screenshots for UI changes
4. Add notes about testing done
5. Make sure CI tests pass

## Feature Requests and Bug Reports

- Use the GitHub issue tracker to report bugs or request features
- Provide detailed steps to reproduce bugs
- Include information about your environment (OS, Python version, etc.)
- Suggest solutions if possible

## Project Structure

Understanding the project structure can help you contribute effectively:

```
mkdocs-protobuf/
├── mkdocs_protobuf_plugin/     # Main plugin package
│   ├── __init__.py             # Package initialization
│   ├── plugin.py               # Main plugin class
│   ├── converter.py            # Proto to Markdown converter
│   └── import_resolver.py      # Import resolution
├── test/                       # Test files
├── docs/                       # Documentation
├── proto/                      # Proto files for documentation
├── setup.py                    # Package setup
└── run_tests.py                # Test runner
```

For more details on the plugin architecture, see [Architecture Documentation](docs/architecture.md).

## Adding New Features

When adding new features:

1. Start by discussing the feature via an issue
2. Consider backward compatibility
3. Write tests before implementing the feature (TDD approach)
4. Update documentation to reflect new capabilities
5. Update the CHANGELOG.md file

## License

By contributing to this project, you agree that your contributions will be licensed under the project's license (see LICENSE file).

## Getting Help

If you have questions or need help with the development process:

1. Check the documentation
2. Look at existing code for examples
3. Open an issue with the "question" label

Thank you for contributing to MkDocs Protobuf Plugin!
