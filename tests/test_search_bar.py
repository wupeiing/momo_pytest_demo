from lib.pages.homepage import HomePageSearchBar
from lib.pages.search_result import SearchResultPage
import time
import pytest
from playwright.sync_api import expect
from urllib.parse import unquote
import logging

logger = logging.getLogger(__name__)

class TestSearchBar:

    @pytest.mark.parametrize("keyword", ["亂碼測試", "adjefmsdddss"])
    def test_homepage_search_bar_dirct_search_no_results(self, main_page, keyword):
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
        home_search = HomePageSearchBar(main_page)
        home_search.wait_for_page_load()
        assert home_search.is_on_homepage(), "Failed to navigate to homepage"
        logger.info("✓ On homepage")

        keyword = home_search.get_placeholder_text()
        logger.info(f"Search keyword: '{keyword}'")
        time.sleep(10)  # wait for placeholder to stabilize
        home_search.click_search_button()
        time.sleep(10)  # search button clicked

        logger.info("Waiting for search result page to load ...")
        search_res = SearchResultPage(main_page)
        search_res.wait_for_page_loaded()
        assert search_res.is_on_search_result_page(keyword), "Search result page failed to load"

        search_res.click_columnType()

        logger.info("Verifying search results relevance ...")

        invalid_res = search_res.get_invalid_results(keyword)
        assert len(invalid_res) == 0, f"{len(invalid_res)} search results not related to keyword: {invalid_res}"
        logger.info("✓ Search results are relevant to keyword")

    # @pytest.mark.parametrize("keyword", ["macbook", "jk 羅琳", "冷氣 日立"])
    @pytest.mark.parametrize("keyword", ["macbook", "iphone 15", "", "衛生紙 舒潔"])
    def test_homepage_search_bar_dirct_search_with_results(self, main_page, keyword):
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

        search_res.click_columnType()

        logger.info("Verifying search results relevance ...")

        invalid_res = search_res.get_invalid_results(keyword)
        assert len(invalid_res) == 0, f"{len(invalid_res)} search results not related to keyword: {invalid_res}"
        logger.info("✓ Search results are relevant to keyword")


    @pytest.mark.parametrize("keyword", ["mac", "iphone 16", "清潔"])
    def test_auto_suggest(self, main_page, keyword):
        main_page.get_by_test_id("header-search-input").click()
        main_page.get_by_test_id("header-search-input").press_sequentially(keyword, delay=100)

        home_search = HomePageSearchBar(main_page)
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
