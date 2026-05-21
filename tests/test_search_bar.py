"""
Search bar tests for the momo homepage.

Scope: black-box frontend verification — we interact with the search bar and observe
whether the site:
  1. Navigates to the correct search result page
  2. Displays results relevant to the search keyword
  3. Shows a no-results banner for garbage/non-existent keywords
  4. Triggers auto-suggestions containing the typed keyword
  5. Handles consecutive searches from the result page correctly

Tests are parametrized to cover English keywords, Chinese keywords, and multi-word queries.
"""

import logging

import pytest

from libs.pages.homepage import HomePageSearchBar
from libs.pages.search_result import SearchResultPage

logger = logging.getLogger(__name__)


class TestSearchBar:

    @pytest.mark.parametrize("keyword", ["亂碼測試", "adjefmsdddss"])
    def test_homepage_search_bar_dirct_search_no_results(self, main_page, keyword):
        """
        Test that searching a garbage/non-existent keyword shows a no-results page.

        Steps:
            1. Verify the browser is on the homepage.
            2. Type a garbage keyword into the search box and click search.
            3. Verify navigation to the search result page with the keyword in the URL.
            4. Verify the no-results banner (or fuzzy-match banner) is displayed.
        """
        home_search = HomePageSearchBar(main_page)
        home_search.wait_for_page_load()
        assert home_search.is_on_homepage(), "Failed to navigate to homepage"
        logger.info("✓ On homepage")

        logger.info(f"Search keyword: '{keyword}'")
        home_search.fill_search_box(keyword)
        home_search.click_search_button()

        logger.info("Waiting for search result page to load ...")
        search_res = SearchResultPage(main_page)
        search_res.wait_for_page_loaded()
        assert search_res.is_on_search_result_page(keyword), "Search result page failed to load"

        logger.info("Checking if search results match keyword ...")
        search_res.wait_for_no_results()

    def test_homepage_search_bar_placeholder_with_results(self, main_page):
        """
        Test that clicking search with the placeholder keyword returns relevant results.

        Steps:
            1. Verify the browser is on the homepage.
            2. Read the search box placeholder text as the keyword; skip if empty.
            3. Click the search button (without typing, using the placeholder as the query).
            4. Verify navigation to the search result page with the placeholder keyword in the URL.
            5. Switch to column (list) view.
            6. Verify all visible products are relevant to the keyword.
        """
        home_search = HomePageSearchBar(main_page)
        home_search.wait_for_page_load()
        assert home_search.is_on_homepage(), "Failed to navigate to homepage"
        logger.info("✓ On homepage")

        keyword = home_search.get_placeholder_text()
        if not keyword:
            pytest.skip("Search box placeholder is empty, skipping test")
        logger.info(f"Search keyword for placeholder: '{keyword}'")
        home_search.click_search_button()

        logger.info("Waiting for search result page to load ...")
        search_res = SearchResultPage(main_page)
        search_res.wait_for_page_loaded()
        assert search_res.is_on_search_result_page(keyword), "Search result page failed to load"

        search_res.click_column_type()

        logger.info("Verifying search results relevance ...")

        invalid_res = search_res.get_invalid_results(keyword)
        assert len(invalid_res) == 0, (
            f"{len(invalid_res)} search results not related to keyword: {invalid_res}"
        )
        logger.info("✓ Search results are relevant to keyword")

    @pytest.mark.parametrize("keyword", ["macbook", "iphone 15", "衛生紙 舒潔", "無線耳機"])
    def test_homepage_search_bar_dirct_search_with_results(self, main_page, keyword):
        """
        Test that searching a known keyword returns relevant products.

        Steps:
            1. Verify the browser is on the homepage.
            2. Type the keyword into the search box and click search.
            3. Verify navigation to the search result page with the keyword in the URL.
            4. Switch to column (list) view.
            5. Verify all visible products are relevant to the keyword.
        """
        home_search = HomePageSearchBar(main_page)
        home_search.wait_for_page_load()
        assert home_search.is_on_homepage(), "Failed to navigate to homepage"
        logger.info("✓ On homepage")

        logger.info(f"Search keyword: '{keyword}'")
        home_search.fill_search_box(keyword)
        home_search.click_search_button()

        logger.info("Waiting for search result page to load ...")
        search_res = SearchResultPage(main_page)
        search_res.wait_for_page_loaded()
        assert search_res.is_on_search_result_page(keyword), "Search result page failed to load"

        search_res.click_column_type()

        logger.info("Verifying search results relevance ...")

        invalid_res = search_res.get_invalid_results(keyword)
        assert len(invalid_res) == 0, (
            f"{len(invalid_res)} search results not related to keyword: {invalid_res}"
        )
        logger.info("✓ Search results are relevant to keyword")

    @pytest.mark.parametrize("keyword", ["mac", "iphone 16", "清潔"])
    def test_auto_suggest(self, main_page, keyword):
        """
        Test that typing a keyword triggers auto-suggestions, all containing the keyword.

        Steps:
            1. Verify the browser is on the homepage.
            2. Type the keyword character-by-character to trigger the suggestion dropdown.
            3. Wait for the suggestion dropdown to appear and collect all suggestion texts.
            4. Verify at least one suggestion is returned.
            5. Verify every suggestion contains the keyword as a substring.
        """
        home_search = HomePageSearchBar(main_page)
        home_search.wait_for_page_load()
        assert home_search.is_on_homepage(), "Failed to navigate to homepage"
        logger.info("✓ On homepage")

        logger.info(f"Search keyword: '{keyword}'")
        home_search.type_in_search_box(keyword)
        suggestions = home_search.wait_and_get_suggestion_keywords()

        logger.info(f"Got {len(suggestions)} auto-suggestions: {suggestions}")

        assert suggestions, "No auto-suggestions found"
        logger.info(f"Total {len(suggestions)} suggestion keywords retrieved")

        invalid = [s for s in suggestions if keyword.lower() not in s.lower()]
        assert not invalid, (
            f"The following suggestions do not contain keyword '{keyword}': {invalid}\n"
            f"All suggestions: {suggestions}"
        )
        logger.info(f"✓ All {len(suggestions)} suggestions contain '{keyword}'")

    @pytest.mark.parametrize(
        "kw_before, kw_after",
        [
            ("apple",  "samsung"),
            ("iphone",  "iphone 15"),
            ("足球鞋",   "籃球鞋"),
        ]
    )
    def test_search_in_search_page(self, main_page, kw_before, kw_after):
        """
        Test that a second search performed from the result page navigates correctly.

        Steps:
            1. Verify the browser is on the homepage.
            2. Search for kw_before and verify the search result page loads.
            3. From the result page, type kw_after into the search box and press Enter.
            4. Wait for nav to complete, then verify the new result page URL contains kw_after.
            5. Switch to column (list) view.
            6. Verify all visible products are relevant to kw_after.
        """
        home_search = HomePageSearchBar(main_page)
        home_search.wait_for_page_load()
        assert home_search.is_on_homepage(), "Failed to navigate to homepage"
        logger.info("✓ On homepage")

        logger.info(f"First search: '{kw_before}'")
        home_search.fill_search_box(kw_before)
        home_search.click_search_button()

        search_res = SearchResultPage(main_page)
        search_res.wait_for_page_loaded()
        assert search_res.is_on_search_result_page(kw_before), "Search result page failed to load"

        logger.info(f"Second search from result page: '{kw_after}'")
        search_res.fill_search_box(kw_after)
        with main_page.expect_navigation(timeout=15000):
            search_res.enter_with_search_box()

        search_res.wait_for_page_loaded()
        assert search_res.is_on_search_result_page(kw_after), \
            "Second search result page failed to load"

        search_res.click_column_type()

        logger.info("Verifying search results relevance ...")

        invalid_res = search_res.get_invalid_results(kw_after)
        assert len(invalid_res) == 0, (
            f"{len(invalid_res)} search results not related to keyword: {invalid_res}"
        )
        logger.info("✓ Search results are relevant to keyword")
