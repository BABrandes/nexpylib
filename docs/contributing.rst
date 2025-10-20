Contributing
============

We welcome contributions to NexPy! Here's how you can help:

Getting Started
---------------

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature or bugfix
4. Make your changes
5. Add tests for your changes
6. Ensure all tests pass
7. Submit a pull request

Development Setup
-----------------

1. Install NexPy in development mode:

   .. code-block:: bash

      git clone https://github.com/yourusername/nexpylib.git
      cd nexpylib
      pip install -e .[dev]

2. Install pre-commit hooks:

   .. code-block:: bash

      pre-commit install

Code Style
----------

We use Black for code formatting and flake8 for linting:

.. code-block:: bash

   black src/ tests/
   flake8 src/ tests/

Testing
-------

Run the test suite:

.. code-block:: bash

   pytest

Documentation
-------------

To build the documentation:

.. code-block:: bash

   cd docs
   make html

Pull Request Guidelines
-----------------------

- Ensure your code follows the existing style
- Add tests for new functionality
- Update documentation as needed
- Write clear commit messages
- Keep pull requests focused and small

Reporting Issues
----------------

When reporting issues, please include:

- Python version
- NexPy version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
