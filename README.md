# momo_pytest_demo

Demo framework for pytest + Playwright targeting momoshop.com.tw.

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

1. Create and activate a conda environment:

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

---

## Run tests

### Basic

```bash
python -m pytest
```

### Options

| Option | Values | Default | Description |
|---|---|---|---|
| `--env` | `staging`, `prod` | `staging` | Target environment |
| `--browser` | `chromium`, `firefox`, `webkit` | `chromium` | Browser engine |
| `--headed` | _(flag)_ | headless | Show browser window |

### Environment

Run against **staging** (default):

```bash
python -m pytest --env staging
```

Run against **production**:

```bash
python -m pytest --env prod
```

### Browser

```bash
# Chromium (default)
python -m pytest --browser chromium

# Firefox
python -m pytest --browser firefox

# WebKit (Safari engine)
python -m pytest --browser webkit
```

### Headed mode (visible browser window)

```bash
python -m pytest --headed
```

---

## Run specific tests

### Run a single test file

```bash
python -m pytest tests/test_search_bar.py
python -m pytest tests/test_security_injection.py
```

### Run a single test class

```bash
python -m pytest tests/test_search_bar.py::TestSearchBar
```

### Run a single test

```bash
python -m pytest tests/test_search_bar.py::TestSearchBar::test_auto_suggest
```

### Run a parametrized test with a specific keyword

```bash
python -m pytest "tests/test_search_bar.py::TestSearchBar::test_auto_suggest[mac]"
```

### Combine options

```bash
# Run auto-suggest tests against prod with a visible Chrome window
python -m pytest -v --headed --env prod tests/test_search_bar.py::TestSearchBar::test_auto_suggest

# Run all search bar tests on Firefox against staging
python -m pytest --headed --browser firefox --env staging tests/test_search_bar.py

# Run security injection tests headlessly against prod
python -m pytest --env prod tests/test_security_injection.py
```

---

## Project structure

```
tests/
  test_search_bar.py        — search bar functional tests
  test_security_injection.py — XSS / SQL / command injection tests

libs/
  pages/
    homepage.py             — page object for the homepage search bar
    search_result.py        — page object for the search result page
  utils/
    keyword_matcher.py      — keyword relevance matching helper

conftest.py                 — fixtures and --env option definition
pyproject.toml              — project metadata and pytest configuration
```

---

## Notes

- `--env` is a custom option defined in `conftest.py`. It sets the base URL for all tests.
- `--browser` and `--headed` are built-in options provided by `pytest-playwright`.
- Live logs are printed to the console during the run (configured in `pyproject.toml`).
