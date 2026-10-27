from playwright.sync_api import Page

from pages.base_page import BasePage


class AssistantPage(BasePage):
    path = "/assistant.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.input = page.get_by_test_id("bot-input")
        self.send_button = page.get_by_test_id("bot-send")
        self.thinking = page.get_by_test_id("thinking")
        self.error = page.get_by_test_id("error-question")

    def ask(self, question: str):
        self.input.fill(question)
        self.send_button.click()

    def bot_message(self, n: int = 0):
        return self.page.get_by_test_id(f"bot-msg-{n}")
