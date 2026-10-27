from playwright.sync_api import Page

from pages.base_page import BasePage


class CollaborationPage(BasePage):
    path = "/collaboration.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.pl_select = page.get_by_test_id("pl-select")
        self.comments = page.get_by_test_id("comments").locator("li")
        self.empty_state = page.get_by_test_id("no-comments")
        self.text = page.get_by_test_id("comment-text")
        self.post_button = page.get_by_test_id("post-comment")
        self.feature_disabled = page.get_by_test_id("feature-disabled")

    def post(self, text: str):
        self.text.fill(text)
        self.post_button.click()
