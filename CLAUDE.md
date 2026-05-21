# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Black-box E2E test suite for **momoshop.com.tw** using pytest + Playwright. Tests verify the search bar (functional) and input sanitization (security/injection). This is a test-only repo — there is no application code to build or deploy.

## Commands

```bash
# Setup
python -m pip install -r requirements.txt
python -m playwright install

# Run all tests
python -m pytest

# Run a single test file
python -m pytest tests/test_search_bar.py

# Run a single test by name
python -m pytest tests/test_search_bar.py::TestSearchBar::test_auto_suggest

# Run a specific parametrized case
python -m pytest "tests/test_search_bar.py::TestSearchBar::test_auto_suggest[mac]"

# Common flags
python -m pytest --env prod          # default: staging
python -m pytest --browser firefox   # default: chromium
python -m pytest --headed            # show browser window (default: headless)

# Lint
pylint libs/ tests/ conftest.py
```

## Architecture

**Page Object Model** — all Playwright interactions go through page objects in `libs/pages/`. Tests in `tests/` instantiate page objects and call their methods; they never use Playwright locators directly.

- `HomePageSearchBar` — search input, auto-suggest dropdown, search button on the homepage
- `SearchResultPage` — result list, column-type toggle, relevance validation via `get_invalid_results()`
- `KeywordMatcher` — normalizes text (strips punctuation, lowercases, preserves CJK) and checks whether all keyword tokens appear in a product name. Used by `SearchResultPage.get_invalid_results()` with a configurable tolerance (default 60%)

**Fixtures** (`conftest.py`):
- `base_url` (session-scoped) — resolved from `--env` flag to staging/prod URL
- `main_page` — navigates to `/main/Main.jsp` before the test; use this for tests that start on the homepage
- `blank_page` — raw Playwright `page` with no navigation; currently unused but available

**Test conventions**:
- Tests use `main_page` fixture (pre-navigated to homepage), not `blank_page`
- Search bar tests parametrize over both English and Chinese keywords
- Security tests submit hostile payloads (XSS, SQLi, command injection) and assert the site handles them safely — a passing test means no vulnerability was found
- Tests log progress with `logging.info()` and use emoji checkmarks (✓/✗) for pass/fail summaries

## Key Details

- `type_in_search_box()` uses `press_sequentially()` (character-by-character) to trigger auto-suggest; `fill_search_box()` uses Playwright `fill()` which skips keyboard events
- The `--env` custom option is defined in `conftest.py`; `--browser` and `--headed` come from pytest-playwright
- `pyproject.toml` enables live CLI logging at INFO level
