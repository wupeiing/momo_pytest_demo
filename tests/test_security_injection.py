"""
Security injection tests for the momo search bar.

Scope: black-box frontend verification — we submit hostile payloads and observe
whether the site:
  1. Executes injected JavaScript  (XSS)
  2. Leaks database error messages (SQL Injection)
  3. Outputs shell command results (Command Injection)

These tests verify the site is NOT vulnerable; a passing suite means
each payload was handled safely.
"""

import logging
import re

import pytest
from playwright.sync_api import Page, Dialog

from libs.pages.homepage import HomePageSearchBar

logger = logging.getLogger(__name__)

# ── Payloads ───────────────────────────────────────────────────────────────────

XSS_PAYLOAD = "<script>alert('XSS')</script>"
SQL_PAYLOAD = "' OR '1'='1"
CMD_PAYLOAD = "; ls -la"

# ── Patterns indicating a successful injection ─────────────────────────────────

# SQL error strings that should never appear in a page
SQL_ERROR_PATTERNS = [
    r"SQL syntax",
    r"mysql_fetch",
    r"ORA-\d{5}",
    r"SQLSTATE",
    r"Unclosed quotation mark",
    r"You have an error in your SQL syntax",
    r"Warning.*mysql",
    r"MySQLSyntaxErrorException",
    r"JDBCException",
]

# Shell command output that should never appear in a page
CMD_OUTPUT_PATTERNS = [
    r"root:x:0:0",       # /etc/passwd leak
    r"uid=\d+\(\w+\)",   # id command output
    r"total \d+\s",      # ls -la header
]


# ── Helper ─────────────────────────────────────────────────────────────────────

def _do_search(page: Page, keyword: str) -> None:
    """Navigate from homepage and submit *keyword* via the search bar."""
    home = HomePageSearchBar(page)
    home.wait_for_page_load()
    assert home.is_on_homepage(), "未成功進入首頁"
    home.fill_search_box(keyword)
    home.click_search_button()
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:  # pylint: disable=broad-exception-caught
        pass  # continue even if networkidle times out (slow pages)


# ── Test class ─────────────────────────────────────────────────────────────────

class TestSecurityInjection:
    """Black-box security tests for the momo search bar."""

    # ── XSS / JavaScript Injection ─────────────────────────────────────────────

    @pytest.mark.parametrize("payload", [XSS_PAYLOAD])
    def test_xss_no_js_dialog_triggered(self, main_page, payload):
        """XSS payload should not trigger any JavaScript dialog (alert/confirm/prompt)."""
        dialog_info: dict = {"fired": False, "message": ""}

        def handle(dlg: Dialog) -> None:
            dialog_info["fired"] = True
            dialog_info["message"] = dlg.message
            logger.warning("[XSS] JS dialog triggered! message: '%s'", dlg.message)
            dlg.dismiss()

        main_page.on("dialog", handle)

        logger.info("[XSS] submitting payload: %r", payload)
        _do_search(main_page, payload)

        assert not dialog_info["fired"], (
            f"XSS succeeded: JS dialog detected, message='{dialog_info['message']}'"
        )
        logger.info("✓ No JS dialog triggered, payload handled safely")

    @pytest.mark.parametrize("payload", [XSS_PAYLOAD])
    def test_xss_dangerous_chars_encoded_in_url(self, main_page, payload):
        """< and > in XSS payloads must be URL-encoded in the resulting URL."""
        logger.info("[XSS] testing URL encoding: %r", payload)
        _do_search(main_page, payload)

        raw_url = main_page.url
        assert "<" not in raw_url, (
            f"Unencoded '<' found in URL, reflected XSS risk: {raw_url}"
        )
        assert ">" not in raw_url, (
            f"Unencoded '>' found in URL, reflected XSS risk: {raw_url}"
        )
        logger.info("✓ URL correctly encoded: %s", raw_url)

    @pytest.mark.parametrize("payload", [XSS_PAYLOAD])
    def test_xss_no_injected_script_in_dom(self, main_page, payload):
        """XSS payload must not produce alert-containing <script> or event attributes in the DOM."""
        logger.info("[XSS] testing DOM injection: %r", payload)
        _do_search(main_page, payload)

        injected: list = main_page.evaluate("""
            () => {
                const hits = [];
                document.querySelectorAll('script').forEach(s => {
                    if ((s.textContent || '').match(/alert|XSS/i))
                        hits.push('script: ' + s.textContent.slice(0, 120));
                });
                document.querySelectorAll('[onerror],[onload]').forEach(el => {
                    const v = (el.getAttribute('onerror') || '') +
                              (el.getAttribute('onload') || '');
                    if (v.match(/alert/i))
                        hits.push('element handler: ' + v.slice(0, 120));
                });
                return hits;
            }
        """)

        assert len(injected) == 0, (
            f"Dangerous elements found in DOM, XSS may have executed: {injected}"
        )
        logger.info("✓ No injected dangerous elements in DOM")

    # ── SQL Injection ──────────────────────────────────────────────────────────

    @pytest.mark.parametrize("payload", [SQL_PAYLOAD])
    def test_sql_injection_no_db_error_in_page(self, main_page, payload):
        """SQL injection payload must not cause the page to leak database error messages."""
        logger.info("[SQLi] submitting payload: %r", payload)
        _do_search(main_page, payload)

        page_text = main_page.locator("body").inner_text()
        found = [
            pattern
            for pattern in SQL_ERROR_PATTERNS
            if re.search(pattern, page_text, re.IGNORECASE)
        ]

        assert not found, (
            f"SQL error message detected in page, possible DB info leak — matched: {found}"
        )
        logger.info("✓ No SQL error messages detected")

    @pytest.mark.parametrize("payload", [SQL_PAYLOAD])
    def test_sql_injection_single_quote_encoded_in_url(self, main_page, payload):
        """Single quote in SQL injection payload must be encoded as %27 in the URL."""
        logger.info("[SQLi] testing URL encoding: %r", payload)
        _do_search(main_page, payload)

        raw_url = main_page.url
        assert "'" not in raw_url, (
            f"Unencoded single quote found in URL, SQL Injection risk: {raw_url}"
        )
        logger.info("✓ Single quote correctly encoded, URL: %s", raw_url)

    # ── Command Injection ──────────────────────────────────────────────────────

    @pytest.mark.parametrize("payload", [CMD_PAYLOAD])
    def test_cmd_injection_no_shell_output_in_page(self, main_page, payload):
        """Command injection payload must not cause shell command output to appear on the page."""
        logger.info("[CMDi] submitting payload: %r", payload)
        _do_search(main_page, payload)

        page_text = main_page.locator("body").inner_text()
        found = [
            pattern
            for pattern in CMD_OUTPUT_PATTERNS
            if re.search(pattern, page_text, re.IGNORECASE)
        ]

        assert not found, (
            f"Possible shell command output on page, Command Injection risk — matched: {found}"
        )
        logger.info("✓ No shell command output detected")

    @pytest.mark.parametrize("payload", [CMD_PAYLOAD])
    def test_cmd_injection_pipe_encoded_in_url(self, main_page, payload):
        """Pipe | in command injection payload must be encoded as %7C in the URL."""
        logger.info("[CMDi] testing URL encoding: %r", payload)
        _do_search(main_page, payload)

        raw_url = main_page.url
        # Only check after scheme (host + path + query); scheme itself never contains |
        path_and_query = raw_url.split("://", 1)[-1]
        assert "|" not in path_and_query, (
            f"Unencoded '|' found in URL, Command Injection risk: {raw_url}"
        )
        logger.info("✓ Pipe character correctly encoded, URL: %s", raw_url)
