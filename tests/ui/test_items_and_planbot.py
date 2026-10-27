"""Item parameters (TS-04) and PlanBot assistant (TS-07)."""
import pytest
from playwright.sync_api import Page, expect

from pages.assistant_page import AssistantPage
from pages.items_page import ItemParametersPage


@pytest.fixture
def items(logged_in_page: Page) -> ItemParametersPage:
    return ItemParametersPage(logged_in_page).open()


@pytest.mark.ui
@pytest.mark.smoke
def test_update_item_parameters_persist(items: ItemParametersPage):
    items.update("P100", lead_time_days=10, moq=480, safety_stock_days=5)
    items.expect_toast("P100 parameters saved")
    items.page.reload()
    expect(items.field("P100", "lead_time_days")).to_have_value("10")
    expect(items.field("P100", "moq")).to_have_value("480")


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("field, value, error", [
    ("lead_time_days", 0, "Lead time must be a whole number between 1 and 365"),
    ("lead_time_days", 366, "Lead time must be a whole number between 1 and 365"),
    ("moq", 0, "MOQ must be a whole number between 1 and 100,000"),
    ("moq", 100001, "MOQ must be a whole number between 1 and 100,000"),
    ("safety_stock_days", -1, "Safety stock days must be a whole number between 0 and 90"),
    ("safety_stock_days", 91, "Safety stock days must be a whole number between 0 and 90"),
    ("lead_time_days", 7.5, "Lead time must be a whole number between 1 and 365"),
])
def test_item_parameter_boundaries(items: ItemParametersPage, field, value, error):
    items.update("P200", **{field: value})
    expect(items.error("P200", field)).to_have_text(error)


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("field, value", [("lead_time_days", 1), ("lead_time_days", 365), ("moq", 1), ("moq", 100000),
                                          ("safety_stock_days", 0), ("safety_stock_days", 90)])
def test_item_parameter_valid_edges(items: ItemParametersPage, field, value):
    items.update("P200", **{field: value})
    items.expect_toast("P200 parameters saved")


@pytest.fixture
def bot(logged_in_page: Page) -> AssistantPage:
    return AssistantPage(logged_in_page).open()


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.defect
@pytest.mark.parametrize("blank", ["", "   "], ids=["empty", "whitespace"])
def test_planbot_blank_input_does_not_hang(bot: AssistantPage, blank):
    """Regression guard: blank input left the bot 'thinking' forever (Low / Low)."""
    bot.ask(blank)
    expect(bot.error).to_have_text("Please enter a question")
    expect(bot.thinking).to_be_hidden()


@pytest.mark.ui
@pytest.mark.smoke
def test_planbot_answers_known_topic(bot: AssistantPage):
    bot.ask("How is the forecast calculated?")
    expect(bot.bot_message(0)).to_contain_text("Product-Location-Customer level")
    expect(bot.thinking).to_be_hidden()
    expect(bot.input).to_have_value("")


@pytest.mark.ui
@pytest.mark.regression
def test_planbot_understands_swedish_keyword(bot: AssistantPage):
    bot.ask("Hur beräknas prognosen?")
    expect(bot.bot_message(0)).to_contain_text("Forecasts are generated monthly")


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
def test_planbot_length_limit(bot: AssistantPage):
    bot.ask("a" * 501)
    expect(bot.error).to_have_text("Questions are limited to 500 characters")
