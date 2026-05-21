"""
Network resilience tests for the momo search bar.

Scope: black-box frontend verification — we simulate network failures and observe
whether the site:
  1. Handles complete offline gracefully (no white screen or JS crash)
  2. Handles search API failures without unhandled errors
  3. Recovers and works normally after network is restored

These tests verify that the site degrades gracefully under adverse network
conditions rather than crashing or showing a blank page.
"""

import logging

from libs.pages.homepage import HomePageSearchBar
from libs.pages.search_result import SearchResultPage

logger = logging.getLogger(__name__)


class TestNetworkResilience:
    """Black-box network resilience tests for the momo search bar."""

    # ── Complete offline ──────────────────────────────────────────────────────

    def test_search_while_offline_no_crash(self, main_page):
        """
        Simulate going offline before clicking search.
        The page should not white-screen or throw unhandled JS errors.

        Steps:
            1. Load the homepage and verify search bar is visible.
            2. Type a keyword into the search box.
            3. Set the browser context to offline mode.
            4. Click the search button.
            5. Verify the page body still has visible content (not a blank page).
            6. Verify no unhandled JS exceptions were thrown.
            7. Restore network connectivity.
        """
        js_errors: list[str] = []
        main_page.on("pageerror", lambda err: js_errors.append(str(err)))

        home = HomePageSearchBar(main_page)
        home.wait_for_page_load()
        assert home.is_on_homepage(), "Failed to navigate to homepage"
        logger.info("✓ On homepage")

        home.fill_search_box("iphone")
        logger.info("Keyword filled, going offline ...")

        main_page.context.set_offline(True)
        logger.info("Browser is now offline")

        home.click_search_button()

        main_page.wait_for_timeout(3000)

        body_text = main_page.locator("body").inner_text(timeout=5000)
        assert len(body_text.strip()) > 0, "Page is blank (white screen) after offline search"
        logger.info("✓ Page is not blank, body has %d characters", len(body_text))

        assert not js_errors, (
            f"Unhandled JS errors during offline search: {js_errors}"
        )
        logger.info("✓ No unhandled JS exceptions")

        main_page.context.set_offline(False)
        logger.info("Network restored")

    # ── Search API failure ────────────────────────────────────────────────────

    def test_search_api_connection_failed(self, main_page):
        """
        Intercept search-related requests and simulate connection failure.
        The page should show an error state rather than crash.

        Steps:
            1. Load the homepage and verify search bar is visible.
            2. Set up a route to abort all requests matching /search/ with 'connectionfailed'.
            3. Type a keyword and click search.
            4. Verify the page body still has visible content.
            5. Verify no unhandled JS exceptions were thrown.
            6. Remove the route intercept.
        """
        js_errors: list[str] = []
        main_page.on("pageerror", lambda err: js_errors.append(str(err)))

        home = HomePageSearchBar(main_page)
        home.wait_for_page_load()
        assert home.is_on_homepage(), "Failed to navigate to homepage"
        logger.info("✓ On homepage")

        main_page.route("**/search/**", lambda route: route.abort("connectionfailed"))
        logger.info("Route intercept active: /search/ requests will fail with connectionfailed")

        home.fill_search_box("macbook")
        home.click_search_button()

        main_page.wait_for_timeout(3000)

        body_text = main_page.locator("body").inner_text(timeout=5000)
        assert len(body_text.strip()) > 0, "Page is blank after search API failure"
        logger.info("✓ Page is not blank, body has %d characters", len(body_text))

        assert not js_errors, (
            f"Unhandled JS errors during API failure: {js_errors}"
        )
        logger.info("✓ No unhandled JS exceptions")

        main_page.unroute("**/search/**")
        logger.info("Route intercept removed")

    def test_search_api_timeout(self, main_page):
        """
        Intercept search-related requests and simulate a network timeout.
        The page should not hang indefinitely or crash.

        Steps:
            1. Load the homepage and verify search bar is visible.
            2. Set up a route to abort all requests matching /search/ with 'timedout'.
            3. Type a keyword and click search.
            4. Verify the page body still has visible content.
            5. Verify no unhandled JS exceptions were thrown.
            6. Remove the route intercept.
        """
        js_errors: list[str] = []
        main_page.on("pageerror", lambda err: js_errors.append(str(err)))

        home = HomePageSearchBar(main_page)
        home.wait_for_page_load()
        assert home.is_on_homepage(), "Failed to navigate to homepage"
        logger.info("✓ On homepage")

        main_page.route("**/search/**", lambda route: route.abort("timedout"))
        logger.info("Route intercept active: /search/ requests will time out")

        home.fill_search_box("衛生紙")
        home.click_search_button()

        main_page.wait_for_timeout(3000)

        body_text = main_page.locator("body").inner_text(timeout=5000)
        assert len(body_text.strip()) > 0, "Page is blank after search API timeout"
        logger.info("✓ Page is not blank, body has %d characters", len(body_text))

        assert not js_errors, (
            f"Unhandled JS errors during API timeout: {js_errors}"
        )
        logger.info("✓ No unhandled JS exceptions")

        main_page.unroute("**/search/**")
        logger.info("Route intercept removed")

    # ── Recovery after network restore ────────────────────────────────────────

    def test_recovery_after_offline(self, main_page):
        """
        Go offline, attempt a search, restore network, then search again.
        The second search should work normally.

        Steps:
            1. Load the homepage normally.
            2. Go offline and attempt a search (expected to fail silently).
            3. Restore network connectivity.
            4. Navigate back to the homepage.
            5. Perform a normal search and verify the result page loads with relevant results.
        """
        home = HomePageSearchBar(main_page)
        home.wait_for_page_load()
        assert home.is_on_homepage(), "Failed to navigate to homepage"
        logger.info("✓ On homepage")

        logger.info("Going offline ...")
        main_page.context.set_offline(True)

        home.fill_search_box("test_offline")
        home.click_search_button()
        main_page.wait_for_timeout(2000)
        logger.info("Offline search attempted")

        main_page.context.set_offline(False)
        logger.info("Network restored, navigating back to homepage ...")

        home.goto()
        home.wait_for_page_load()
        assert home.is_on_homepage(), "Failed to navigate to homepage after recovery"
        logger.info("✓ Back on homepage after recovery")

        keyword = "apple"
        logger.info("Searching for '%s' after recovery ...", keyword)
        home.fill_search_box(keyword)
        home.click_search_button()

        search_res = SearchResultPage(main_page)
        search_res.wait_for_page_loaded()
        assert search_res.is_on_search_result_page(keyword), (
            "Search result page failed to load after network recovery"
        )
        logger.info("✓ Search works normally after network recovery")
