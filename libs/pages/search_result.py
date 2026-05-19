import logging
from urllib.parse import unquote, urlparse, parse_qs

from playwright.sync_api import Locator, Page, expect

from libs.utils.keyword_matcher import KeywordMatcher

logger = logging.getLogger(__name__)


class SearchResultPage:
    SEARCH_INPUT_LOCATOR = 'input[id="header-search-input"]'
    SEARCH_BUTTON_LOCATOR = 'button[id="header-search-button"]'
    SEARCH_LIST_AREA_LOCATOR = "div.bt_2_layout.searchbox.searchListArea"
    SEARCH_LIST_NO_RESULT_LOCATOR = "div.noSearchResultWrapper"
    SEARCH_LIST_NO_RESULT_FUZZY_LOCATOR = "div#errorArea div#isfuzzydiv"

    PRODUCT_NAME_LOCATOR = "ul.listAreaUl li.listAreaLi h3.prdName"
    COLUMN_TYPE_ITEM_LOCATOR = "div.listArea.columnType li.listAreaLi"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.search_input = page.locator(self.SEARCH_INPUT_LOCATOR)
        self.search_button = page.locator(self.SEARCH_BUTTON_LOCATOR)

    def fill_search_box(self, keyword: str) -> None:
        self.search_input.fill(keyword)

    def enter_with_search_box(self) -> None:
        self.search_input.press("Enter")

    def click_search_button(self) -> None:
        expect(self.search_button).to_be_visible()
        self.search_button.click()

    def search(self, keyword: str) -> None:
        self.fill_search_box(keyword)
        self.click_search_button()

    def wait_for_page_loaded(self, timeout: int = 30000) -> None:
        logger.info("Waiting for search result page to load ...")
        expect(self.page.locator(self.SEARCH_LIST_AREA_LOCATOR)).to_be_visible(timeout=timeout)
        logger.info("Search result page loaded")

    def _get_url_fuzzy_param(self) -> str:
        """Return _isFuzzy query param from the current URL, or empty string."""
        params = parse_qs(urlparse(self.page.url).query)
        return params.get("_isFuzzy", [""])[0]

    def wait_for_no_results(self, timeout: int = 30000) -> None:
        fuzzy_val = self._get_url_fuzzy_param()
        if fuzzy_val:
            logger.info(
                "URL fuzzy=%r, waiting for fuzzy banner (#errorArea #isfuzzydiv)", fuzzy_val
            )
            expect(
                self.page.locator(self.SEARCH_LIST_NO_RESULT_FUZZY_LOCATOR)
            ).to_be_visible(timeout=timeout)
            logger.info("Fuzzy recommendation banner is visible")
        else:
            logger.info("Waiting for no-results banner (.noSearchResultWrapper)")
            expect(
                self.page.locator(self.SEARCH_LIST_NO_RESULT_LOCATOR)
            ).to_be_visible(timeout=timeout)
            logger.info("No-results banner is visible")

    def click_column_type(self) -> None:
        column_type_locator = self.page.locator("label.columnType")
        expect(column_type_locator).to_be_visible(timeout=10000)
        column_type_locator.click()

    def get_invalid_results(self, keyword: str, tolerance: float = 0.6) -> list[str]:
        """
        Check search results, allowing a configurable proportion of unrelated products.

        Args:
            keyword: search keyword
            tolerance: allowed fraction of unrelated results (0.6 = allow up to 60%)

        Returns:
            List of URLs for unrelated products, or empty list if within tolerance.
        """
        def _text(li: Locator, selector: str) -> str:
            loc = li.locator(selector)
            return loc.inner_text().strip() if loc.count() > 0 else ""

        invalid: list[str] = []
        total_count = 0

        for li in self.page.locator(self.COLUMN_TYPE_ITEM_LOCATOR).all():
            total_count += 1
            prd_name    = _text(li, "h3.prdName")
            publishing  = _text(li, "a.publishing")
            description = _text(li, "p.description")

            logger.debug("Checking product: '%s'", prd_name)

            if any(KeywordMatcher.all_keywords_in_name(keyword, f)
                   for f in [prd_name, publishing, description]):
                continue

            url_loc = li.locator("h3.prdName a")
            url = url_loc.get_attribute("href") if url_loc.count() > 0 else "(no url)"
            invalid.append(url)

        invalid_rate = len(invalid) / total_count if total_count > 0 else 0

        logger.info("Keyword '%s' validation:", keyword)
        logger.info("  Total products: %s", total_count)
        logger.info("  Unrelated: %s (%.1f%%)", len(invalid), invalid_rate * 100)
        logger.info("  Related: %s (%.1f%%)", total_count - len(invalid), (1 - invalid_rate) * 100)

        if invalid_rate <= tolerance:
            logger.info("✓ Within tolerance (≤%.0f%%), considered passing", tolerance * 100)
            return []

        logger.warning(
            "✗ Exceeded tolerance (%.1f%% > %.0f%%)", invalid_rate * 100, tolerance * 100
        )
        return invalid

    def is_on_search_result_page(self, keyword: str) -> bool:
        """
        Check if on the search result page with the keyword in the URL path.
        Supports multi-word keywords; spaces are encoded as %20.
        """
        decoded_url = unquote(self.page.url)
        expected_path = f"/search/{keyword}"
        is_search_page = expected_path in decoded_url
        logger.info(
            "On search result page: %s (expected: %s, decoded URL: %s)",
            is_search_page, expected_path, decoded_url,
        )
        return is_search_page
