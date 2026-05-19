import pytest

BASE_URLS = {
    "staging": "https://www.stg.momoshop.com.tw",
    "prod": "https://www.momoshop.com.tw",
}

MAIN_PAGE_PATH = "/main/Main.jsp"


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="staging",
        choices=list(BASE_URLS.keys()),
        help="Target environment: staging (default) or prod",
    )


@pytest.fixture(scope="session")
def base_url(request):
    env = request.config.getoption("--env")
    return BASE_URLS[env]


@pytest.fixture
def blank_page(page):
    """Blank browser, no pre-navigation."""
    return page


@pytest.fixture
def main_page(page, base_url):  # pylint: disable=redefined-outer-name
    """Directly enter the main page /main/Main.jsp."""
    page.goto(base_url + MAIN_PAGE_PATH)
    return page
