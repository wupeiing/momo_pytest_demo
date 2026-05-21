"""
Network resilience tests for the momo search bar.

Scope: black-box frontend verification — we simulate a network outage and observe
whether the site recovers and works normally after connectivity is restored.
"""

import logging

from libs.pages.homepage import HomePageSearchBar
from libs.pages.search_result import SearchResultPage

logger = logging.getLogger(__name__)


def test_recovery_after_offline(main_page):
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
