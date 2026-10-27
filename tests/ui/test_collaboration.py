"""Collaborative planning feature gating — manual suite TS-03."""
import pytest
from playwright.sync_api import Page, expect

from config.settings import settings
from pages.collaboration_page import CollaborationPage
from pages.login_page import LoginPage


def login_as(page: Page, creds):
    login = LoginPage(page).open()
    login.login(*creds)
    login.wait_for_post_login()


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.defect
@pytest.mark.parametrize("creds, visible", [
    (("ibp_planner", "Scp@1234"), True),
    (("collab_planner", "Scp@1234"), True),
    (("std_planner", "Scp@1234"), False),
], ids=["IBP-subscription", "COLLAB-subscription", "STANDARD-subscription"])
def test_collaboration_menu_by_subscription(page: Page, creds, visible):
    """Regression guard: collaborative planning was hidden for IBP customers (High / High)."""
    login_as(page, creds)
    expect(page.get_by_test_id("nav-collaboration")).to_have_count(1 if visible else 0)


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
def test_standard_tenant_direct_url_blocked(page: Page):
    login_as(page, settings.standard_user)
    CollaborationPage(page).open()
    expect(CollaborationPage(page).feature_disabled).to_be_visible()


@pytest.mark.ui
@pytest.mark.regression
def test_post_comment(logged_in_page: Page):
    collab = CollaborationPage(logged_in_page).open()
    expect(collab.empty_state).to_be_visible()
    collab.post("Customer ICA expects +10% for the February campaign")
    collab.expect_toast("Comment posted")
    expect(collab.comments).to_have_count(1)
    expect(collab.comments.first).to_contain_text("IBP Planner: Customer ICA expects")


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("text, error", [("   ", "Comment is required"), ("x" * 501, "Comment must be 500 characters or fewer")],
                         ids=["blank", "501-chars"])
def test_comment_validation(logged_in_page: Page, text, error):
    collab = CollaborationPage(logged_in_page).open()
    collab.post(text)
    expect(collab.field_error("text")).to_have_text(error)


@pytest.mark.ui
@pytest.mark.regression
def test_comments_are_scoped_to_product_location(logged_in_page: Page):
    collab = CollaborationPage(logged_in_page).open()
    collab.post("Only for P100 Gothenburg")
    expect(collab.comments).to_have_count(1)
    collab.pl_select.select_option("P200|STO")
    expect(collab.empty_state).to_be_visible()
