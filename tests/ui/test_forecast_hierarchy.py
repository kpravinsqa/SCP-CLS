"""Forecast hierarchy aggregation & export — manual suite TS-02 / TS-05."""
import csv
import io

import pytest
from playwright.sync_api import Page, expect

from pages.forecast_page import ForecastPage


@pytest.fixture
def fc(logged_in_page: Page) -> ForecastPage:
    return ForecastPage(logged_in_page).open()


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.parametrize("level, rows", [("PLC", 12), ("PL", 4), ("P", 2)])
def test_row_count_per_level(fc: ForecastPage, level, rows):
    fc.choose_level(level)
    expect(fc.rows).to_have_count(rows)
    expect(fc.grand_total).to_have_text("43,200")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.defect
@pytest.mark.parametrize("pl_key", ["P100|STO", "P100|GOT", "P200|STO", "P200|GOT"])
def test_pl_total_equals_sum_of_plc_children(fc: ForecastPage, pl_key):
    """Regression guard: PLC → PL aggregation once showed wrong forecasts (High / High)."""
    fc.choose_level("PL")
    parent = fc.total_of(pl_key)
    fc.row(pl_key).click()
    children = [f"{pl_key}|{c}" for c in ("AXF", "COOP", "ICA")]
    for key in children:
        expect(fc.child(key)).to_be_visible()
    assert parent == sum(fc.total_of(k, child=True) for k in children)


@pytest.mark.ui
@pytest.mark.regression
def test_drill_down_toggles(fc: ForecastPage):
    fc.choose_level("PL")
    fc.row("P100|STO").click()
    expect(fc.rows).to_have_count(7)
    fc.row("P100|STO").click()
    expect(fc.rows).to_have_count(4)


@pytest.mark.ui
@pytest.mark.regression
def test_edit_at_plc_rolls_up_to_product(fc: ForecastPage, api):
    api.put("/api/forecast/plc", data={"product": "P100", "location": "STO", "customer": "ICA", "month": "Nov-26", "qty": 1000})
    fc.page.reload()
    fc.choose_level("P")
    expect(fc.row("P100").get_by_test_id("total")).to_have_text("19,500")   # 18 900 - 400 + 1 000
    expect(fc.grand_total).to_have_text("43,800")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("level, header, rows", [
    ("PLC", ["Product", "Location", "Customer"], 12),
    ("PL", ["Product", "Location"], 4),
    ("P", ["Product"], 2),
])
def test_csv_export(fc: ForecastPage, level, header, rows):
    fc.choose_level(level)
    with fc.page.expect_download() as info:
        fc.export_button.click()
    download = info.value
    assert download.suggested_filename == f"forecast_{level}.csv"
    content = list(csv.reader(io.StringIO(open(download.path(), encoding="utf-8").read())))
    assert content[0][: len(header)] == header
    assert content[0][-1] == "Total"
    assert len(content) - 1 == rows
    assert sum(int(r[-1]) for r in content[1:]) == 43200
