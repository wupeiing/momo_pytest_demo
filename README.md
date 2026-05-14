# momo_pytest_demo

Demo framework for pytest + Playwright.

> Requires Python 3.9 or newer.

## Setup

### Standard virtual environment

1. Create a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

### Anaconda / conda environment

1. Create and activate a conda environment (using 3.11 as example):

   ```bash
   conda create -n momo_pytest_demo python=3.11 -y
   conda activate momo_pytest_demo
   ```

2. Install dependencies:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. Install Playwright browsers:

   ```bash
   python -m playwright install
   ```

## Run tests

```bash
pytest
```

To run tests with a visible browser:

```bash
pytest --headed
```

## Project files

- `pyproject.toml` — project metadata and pytest configuration
- `requirements.txt` — installable test dependencies
- `tests/test_example.py` — sample Playwright test

## Notes

- The sample test uses the `page` fixture provided by `pytest-playwright`.
- If you want to run a single test, use `pytest tests/test_example.py`.
