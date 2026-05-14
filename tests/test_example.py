import time

def test_example_page_title(page):
    page.goto("https://www.momoshop.com.tw/")
    assert "momo" in page.title()
    time.sleep(10)
