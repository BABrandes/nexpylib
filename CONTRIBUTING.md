# Contributing to NexPy

Thank you for your interest in contributing to NexPy! This document provides guidelines and information for contributors.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/nexpylib.git
   cd nexpylib
   ```
3. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Install Dependencies

Install NexPy in development mode with all development dependencies:

```bash
pip install -e .[dev]
```

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
pre-commit install
```

## Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **flake8** for linting
- **mypy** for type checking
- **pytest** for testing

### Formatting Code

```bash
make format
# or
black src/ tests/
```

### Linting

```bash
make lint
# or
flake8 src/ tests/
mypy src/
```

## Testing

### Running Tests

```bash
make test
# or
pytest
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names
- Follow the existing test patterns
- Aim for good test coverage

## Documentation

### Building Documentation

```bash
make docs
# or
cd docs && make html
```

### Writing Documentation

- Update docstrings for new functions and classes
- Add examples to the documentation
- Update the API reference as needed

## Pull Request Guidelines

### Before Submitting

1. **Run tests**: Ensure all tests pass
2. **Check formatting**: Run `make format` and `make lint`
3. **Update documentation**: Add or update docstrings and documentation
4. **Write clear commit messages**: Use descriptive commit messages

### Pull Request Process

1. **Create a clear title** describing the change
2. **Provide a detailed description** of what was changed and why
3. **Reference any related issues** using GitHub's issue linking
4. **Keep pull requests focused** - one feature or bugfix per PR
5. **Ensure CI passes** - all checks must be green

### Commit Message Format

Use clear, descriptive commit messages:

```
feat: add new data processing function
fix: resolve issue with file loading
docs: update API documentation
test: add tests for new functionality
```

## Reporting Issues

When reporting issues, please include:

- **Python version**
- **NexPy version**
- **Operating system**
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Error messages** (if any)

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to create a welcoming environment for all contributors.

## Questions?

If you have questions about contributing, please:

- Open an issue on GitHub
- Check the existing documentation
- Review the codebase for examples

Thank you for contributing to NexPy!
