from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.text import normalise_spaces


class ForecastPage(BasePage):
    path = "/forecast.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.title = page.get_by_test_id("page-title")
        self.level = page.get_by_test_id("level")
        self.export_button = page.get_by_test_id("export-csv")
        self.grand_total = page.get_by_test_id("grand-total")
        self.grand_value = page.get_by_test_id("grand-value")
        self.rows = page.get_by_test_id("forecast-table").locator("tbody tr")

    def open(self):
        super().open()
        self.grand_total.filter(has_text="4").wait_for()
        return self

    def choose_level(self, level: str):
        with self.page.expect_response(f"**/api/forecast?level={level}"):
            self.level.select_option(level)

    def row(self, key: str):
        return self.page.get_by_test_id(f"row-{key}")

    def child(self, key: str):
        return self.page.get_by_test_id(f"child-{key}")

    def total_of(self, key: str, child: bool = False) -> int:
        locator = (self.child(key) if child else self.row(key)).get_by_test_id("total")
        return int("".join(ch for ch in locator.inner_text() if ch.isdigit()))

    def text(self, locator) -> str:
        return normalise_spaces(locator.inner_text())
