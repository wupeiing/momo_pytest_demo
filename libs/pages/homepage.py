import logging
import re

from playwright.sync_api import Page, expect

logger = logging.getLogger(__name__)


class HomePageSearchBar:
    HOME_URL = "https://www.momoshop.com.tw/main/Main.jsp"
    SEARCH_ANCHOR_LOCATOR = '[data-testid="search-input-anchor"]'
    SEARCH_INPUT_LOCATOR = 'input[data-testid="header-search-input"]'
    SEARCH_BUTTON_LOCATOR = 'button[data-testid="header-search-button"]'
    SUGGESTION_LISTBOX_LOCATOR = 'ul#header-search-input-listbox'
    SUGGESTION_ITEM_LOCATOR = 'div.absolute button span.text-sm'

    def __init__(self, page: Page) -> None:
        self.page = page
        self.search_anchor = page.locator(self.SEARCH_ANCHOR_LOCATOR)
        self.search_input = page.locator(self.SEARCH_INPUT_LOCATOR)
        self.search_button = page.locator(self.SEARCH_BUTTON_LOCATOR)

    def goto(self) -> None:
        self.page.goto(self.HOME_URL)
        expect(self.search_anchor).to_be_visible(timeout=10000)
        expect(self.search_input).to_be_visible(timeout=10000)

    def wait_for_page_load(self, timeout: int = 30000) -> None:
        logger.info("Waiting for homepage to load ...")
        try:
            self.page.wait_for_selector(self.SEARCH_INPUT_LOCATOR, timeout=timeout, state="visible")
            logger.info("Homepage loaded")
        except Exception as e:
            logger.error("Homepage load timed out: %s", e)
            raise

    def is_on_homepage(self) -> bool:
        current_url = self.page.url
        is_homepage = self.HOME_URL in current_url
        logger.info("On homepage: %s (current URL: %s)", is_homepage, current_url)
        return is_homepage

    def get_placeholder_text(self) -> str:
        try:
            expect(self.search_input).to_have_attribute(
                "placeholder", re.compile(r".+"), timeout=10000
            )
            return self.search_input.evaluate("el => el.placeholder") or ""
        except AssertionError as e:
            logger.warning("Failed to get placeholder text: %s", e)
            return ""

    def fill_search_box(self, keyword: str) -> None:
        self.search_input.fill(keyword)

    def type_in_search_box(self, keyword: str, delay: int = 80) -> None:
        """Type character-by-character to trigger auto-suggestion (fill skips keyboard events)."""
        self.search_input.click()
        self.search_input.press_sequentially(keyword, delay=delay)

    def wait_and_get_suggestion_keywords(self, timeout: int = 5000) -> list[str]:
        """Wait for the suggestion dropdown and return all keyword texts."""
        self.page.locator("div.absolute button").first.wait_for(
            state="visible", timeout=timeout
        )
        logger.info("Auto-suggestion dropdown appeared, collecting suggestion items ...")
        keywords = self.page.locator(self.SUGGESTION_ITEM_LOCATOR).all_text_contents()
        for kw in keywords:
            logger.info(kw)
        return keywords

    def enter_with_search_box(self) -> None:
        self.search_input.press("Enter")

    def clear_search_box(self) -> None:
        self.search_input.clear()

    def click_search_button(self) -> None:
        expect(self.search_button).to_be_visible()
        self.search_button.click()

    def search(self, keyword: str) -> None:
        self.wait_for_page_load()
        assert self.is_on_homepage(), "Failed to navigate to homepage"
        self.fill_search_box(keyword)
        self.click_search_button()
        self.page.wait_for_load_state("networkidle", timeout=10000)
