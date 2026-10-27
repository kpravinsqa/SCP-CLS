"""Login & Nordic localisation — manual suite TS-01 / TS-06."""
import re

import pytest
from playwright.sync_api import Page, expect

from config.settings import settings
from pages.forecast_page import ForecastPage
from pages.login_page import LoginPage
from utils.data_loader import cases


@pytest.mark.ui
@pytest.mark.smoke
def test_login_default_locale(page: Page):
    login = LoginPage(page).open()
    login.login(settings.username, settings.password)
    login.wait_for_post_login()
    expect(page.get_by_test_id("tenant-badge")).to_have_text("Nordic Foods AB")
    expect(ForecastPage(page).title).to_have_text("Forecast")


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.defect
def test_swedish_locale_login_with_nordic_characters(page: Page):
    """Regression guard: login failed for Swedish-locale users (showstopper)."""
    login = LoginPage(page).open()
    login.login(*settings.swedish_user, locale="sv-SE")
    login.wait_for_post_login()
    expect(login.user_badge).to_have_text("Åsa Lindqvist")
    expect(page.get_by_test_id("nav-forecast")).to_have_text("Prognos")
    expect(page.locator("html")).to_have_attribute("lang", "sv-SE")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("case", cases("localisation", "locales"))
def test_labels_and_number_formats_per_locale(page: Page, case):
    login = LoginPage(page).open()
    login.login(settings.username, settings.password, locale=case["locale"])
    forecast = ForecastPage(page)
    expect(page.get_by_test_id("nav-forecast")).to_have_text(case["nav_forecast"])
    expect(forecast.logout_button).to_have_text(case["logout"])
    expect(forecast.grand_total).not_to_be_empty()
    assert forecast.text(forecast.grand_total) == case["grand_total"]
    assert forecast.text(forecast.grand_value) == case["grand_value_sek"]


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.defect
@pytest.mark.parametrize("creds, locale, expected", [
    (("std_planner", "Scp@1234"), "sv-SE", "117 585,00 US$"),
    (("collab_planner", "Scp@1234"), "en-US", "€117,585.00"),
    (("ibp_planner", "Scp@1234"), "en-US", "SEK 117,585.00"),
], ids=["USD-tenant-swedish-ui", "EUR-tenant-english-ui", "SEK-tenant-english-ui"])
def test_currency_follows_tenant_not_ui_language(page: Page, creds, locale, expected):
    """Regression guard: wrong currency sign shown when UI language differed from tenant currency."""
    LoginPage(page).open().login(*creds, locale=locale)
    forecast = ForecastPage(page)
    expect(forecast.grand_value).not_to_be_empty()
    assert forecast.text(forecast.grand_value) == expected


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("user, pwd", [("ibp_planner", "scp@1234"), ("asa.lind", "Scp@1234"), ("ibp_planner", "Scp@1234 ")],
                         ids=["password-case", "nordic-char-stripped", "trailing-space"])
def test_invalid_login(page: Page, user, pwd):
    login = LoginPage(page).open()
    login.login(user, pwd)
    login.expect_form_error("Invalid username or password")


@pytest.mark.ui
@pytest.mark.smoke
def test_logout(logged_in_page: Page):
    ForecastPage(logged_in_page).logout()
    logged_in_page.goto("/items.html")
    expect(logged_in_page).to_have_url(re.compile(r".*/login\.html$"))
