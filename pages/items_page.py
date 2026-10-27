from playwright.sync_api import Page

from pages.base_page import BasePage


class ItemParametersPage(BasePage):
    path = "/items.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.rows = page.get_by_test_id("items-table").locator("tbody tr")

    def open(self):
        super().open()
        self.rows.first.wait_for()
        return self

    def field(self, product: str, name: str):
        return self.page.get_by_test_id(f"{product}-{name}")

    def error(self, product: str, name: str):
        return self.page.get_by_test_id(f"error-{product}-{name}")

    def update(self, product: str, **values):
        for name, value in values.items():
            self.field(product, name).fill(str(value))
        self.page.get_by_test_id(f"save-{product}").click()
