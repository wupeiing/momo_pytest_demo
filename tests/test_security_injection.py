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

import re
import pytest
from urllib.parse import unquote
from playwright.sync_api import Page, Dialog

from lib.pages.homepage import HomePageSearchBar
import logging

logger = logging.getLogger(__name__)

# ── Payloads ───────────────────────────────────────────────────────────────────

XSS_PAYLOADS = [
    pytest.param("<script>alert('XSS')</script>",  id="script-tag"),
    pytest.param("<img src=x onerror=alert(1)>",   id="img-onerror"),
    pytest.param("javascript:alert(1)",             id="js-uri"),
    pytest.param("<svg onload=alert(1)>",           id="svg-onload"),
]

SQL_INJECTION_PAYLOADS = [
    pytest.param("' OR '1'='1",                    id="or-true"),
    pytest.param("'; DROP TABLE products; --",     id="drop-table"),
    pytest.param("1 UNION SELECT NULL, NULL--",    id="union-select"),
    pytest.param("' OR 1=1--",                     id="or-1-1-comment"),
]

CMD_INJECTION_PAYLOADS = [
    pytest.param("; ls -la",           id="semicolon-ls"),
    pytest.param("| cat /etc/passwd",  id="pipe-passwd"),
    pytest.param("$(whoami)",          id="subshell-whoami"),
    pytest.param("`id`",              id="backtick-id"),
]

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
    except Exception:
        pass  # continue even if networkidle times out (slow pages)


# ── Test class ─────────────────────────────────────────────────────────────────

class TestSecurityInjection:
    """Black-box security tests for the momo search bar."""

    # ── XSS / JavaScript Injection ─────────────────────────────────────────────

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_no_js_dialog_triggered(self, main_page, payload):
        """XSS payload 不應觸發任何 JavaScript dialog（alert / confirm / prompt）。

        判斷依據：Playwright 的 dialog 事件若被觸發，代表 JS 成功執行，即 XSS 成立。
        """
        dialog_info: dict = {"fired": False, "message": ""}

        def handle(dlg: Dialog) -> None:
            dialog_info["fired"] = True
            dialog_info["message"] = dlg.message
            logger.warning(f"[XSS] JS dialog 被觸發！訊息: '{dlg.message}'")
            dlg.dismiss()

        main_page.on("dialog", handle)

        logger.info(f"[XSS] 輸入 payload: {payload!r}")
        _do_search(main_page, payload)

        assert not dialog_info["fired"], (
            f"XSS 注入成功：偵測到 JS dialog，訊息='{dialog_info['message']}'"
        )
        logger.info("✓ 未觸發 JS dialog，payload 已被安全處理")

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_dangerous_chars_encoded_in_url(self, main_page, payload):
        """XSS payload 中的 < > 必須在 URL 中被正確 URL 編碼，不能以原始字元出現。

        反射型 XSS 的必要條件之一是 payload 以未編碼形式出現在 URL 裡，
        進而被 server-side template engine 原樣輸出到 HTML。
        """
        logger.info(f"[XSS] 測試 URL 編碼: {payload!r}")
        _do_search(main_page, payload)

        raw_url = main_page.url
        assert "<" not in raw_url, (
            f"URL 中出現未編碼的 '<'，存在反射型 XSS 風險: {raw_url}"
        )
        assert ">" not in raw_url, (
            f"URL 中出現未編碼的 '>'，存在反射型 XSS 風險: {raw_url}"
        )
        logger.info(f"✓ URL 已正確編碼: {raw_url}")

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_no_injected_script_in_dom(self, main_page, payload):
        """XSS payload 不應在 DOM 中生成含有 alert 的 <script> 或事件屬性。

        即使 URL 編碼正確，若 server 在回應 HTML 時沒有做 HTML-escape，
        payload 仍可能被瀏覽器解析並執行，此測試直接掃描渲染後的 DOM。
        """
        logger.info(f"[XSS] 測試 DOM 注入: {payload!r}")
        _do_search(main_page, payload)

        injected: list = main_page.evaluate("""
            () => {
                const hits = [];
                // <script> 含有 alert 或 XSS 字樣
                document.querySelectorAll('script').forEach(s => {
                    if ((s.textContent || '').match(/alert|XSS/i))
                        hits.push('script: ' + s.textContent.slice(0, 120));
                });
                // 元素帶有 onerror / onload 且含 alert
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
            f"DOM 中發現注入的危險元素，XSS 可能已執行: {injected}"
        )
        logger.info("✓ DOM 中無注入的危險元素")

    # ── SQL Injection ──────────────────────────────────────────────────────────

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_sql_injection_no_db_error_in_page(self, main_page, payload):
        """SQL injection payload 不應使頁面洩漏資料庫錯誤訊息。

        若頁面出現 SQL 錯誤字串，代表 payload 有機會到達資料庫層且造成異常，
        同時洩漏了後端技術細節，屬於嚴重安全問題。
        """
        logger.info(f"[SQLi] 輸入 payload: {payload!r}")
        _do_search(main_page, payload)

        page_text = main_page.locator("body").inner_text()
        found = [
            pattern
            for pattern in SQL_ERROR_PATTERNS
            if re.search(pattern, page_text, re.IGNORECASE)
        ]

        assert not found, (
            f"頁面中偵測到 SQL 錯誤訊息，可能洩漏資料庫資訊 — 命中 pattern: {found}"
        )
        logger.info("✓ 未偵測到 SQL 錯誤訊息")

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_sql_injection_single_quote_encoded_in_url(self, main_page, payload):
        """SQL injection payload 中的單引號 ' 在 URL 中必須被編碼為 %27。

        單引號是 SQL injection 最常見的觸發字元，若其原始形式出現在 URL 中
        且後端未做參數化查詢，可能直接造成注入。
        """
        logger.info(f"[SQLi] 測試 URL 編碼: {payload!r}")
        _do_search(main_page, payload)

        raw_url = main_page.url
        assert "'" not in raw_url, (
            f"URL 中出現未編碼的單引號 \"'\"，可能存在 SQL Injection 風險: {raw_url}"
        )
        logger.info(f"✓ 單引號已正確編碼，URL: {raw_url}")

    # ── Command Injection ──────────────────────────────────────────────────────

    @pytest.mark.parametrize("payload", CMD_INJECTION_PAYLOADS)
    def test_cmd_injection_no_shell_output_in_page(self, main_page, payload):
        """Command injection payload 不應使頁面顯示任何 shell 指令執行結果。

        若頁面出現 /etc/passwd 內容、id 指令輸出或 ls 目錄列表等，
        代表後端將搜尋字串傳遞給了 shell 執行，屬於嚴重 RCE 漏洞。
        """
        logger.info(f"[CMDi] 輸入 payload: {payload!r}")
        _do_search(main_page, payload)

        page_text = main_page.locator("body").inner_text()
        found = [
            pattern
            for pattern in CMD_OUTPUT_PATTERNS
            if re.search(pattern, page_text, re.IGNORECASE)
        ]

        assert not found, (
            f"頁面中偵測到疑似 shell 指令輸出，可能存在 Command Injection 漏洞 — 命中 pattern: {found}"
        )
        logger.info("✓ 未偵測到 shell 指令輸出")

    @pytest.mark.parametrize("payload", CMD_INJECTION_PAYLOADS)
    def test_cmd_injection_pipe_encoded_in_url(self, main_page, payload):
        """Command injection payload 中的 pipe | 在 URL 中必須被編碼為 %7C。

        pipe 字元是最常見的命令串接符，若以原始形式出現在 URL path 中
        且後端未做 sanitization，可能被傳遞給 shell 執行。
        """
        logger.info(f"[CMDi] 測試 URL 編碼: {payload!r}")
        _do_search(main_page, payload)

        raw_url = main_page.url
        # 只檢查 scheme 之後的部分（host + path + query），scheme 本身不含 |
        path_and_query = raw_url.split("://", 1)[-1]
        assert "|" not in path_and_query, (
            f"URL 中出現未編碼的 '|'，可能存在 Command Injection 風險: {raw_url}"
        )
        logger.info(f"✓ pipe 字元已正確編碼，URL: {raw_url}")
