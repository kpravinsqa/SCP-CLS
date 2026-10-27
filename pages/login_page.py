from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/login.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.username = page.get_by_test_id("username")
        self.password = page.get_by_test_id("password")
        self.locale = page.get_by_test_id("locale")
        self.submit = page.get_by_test_id("login-submit")
        self.form_error = page.get_by_test_id("error-form")

    def login(self, username: str, password: str, locale: str = "en-US"):
        self.username.fill(username)
        self.password.fill(password)
        self.locale.select_option(locale)
        self.submit.click()

    def wait_for_post_login(self):
        self.page.wait_for_url("**/forecast.html")

    def expect_form_error(self, message: str):
        expect(self.form_error).to_have_text(message)
