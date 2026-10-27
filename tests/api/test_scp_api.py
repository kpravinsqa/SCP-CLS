import csv
import io

import pytest

from api.scp_client import ScpClient


@pytest.fixture
def client(api) -> ScpClient:
    return ScpClient(api)


def totals_by(rows, keys):
    out = {}
    for r in rows:
        k = tuple(r[x] for x in keys)
        out[k] = out.get(k, 0) + r["total"]
    return out


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.defect
def test_every_level_reconciles_with_plc(client):
    plc = client.forecast("PLC").json()["rows"]
    for level, keys in (("PL", ("product", "location")), ("P", ("product",))):
        agg = {tuple(r[x] for x in keys): r["total"] for r in client.forecast(level).json()["rows"]}
        assert agg == totals_by(plc, keys), f"{level} does not reconcile with PLC"


@pytest.mark.api
@pytest.mark.regression
def test_monthly_values_reconcile(client):
    plc = client.forecast("PLC").json()
    p = client.forecast("P").json()
    for month in plc["months"]:
        assert sum(r["values"][month] for r in plc["rows"]) == sum(r["values"][month] for r in p["rows"])


@pytest.mark.api
@pytest.mark.regression
def test_value_uses_unit_price(client):
    rows = {r["product"]: r for r in client.forecast("P").json()["rows"]}
    assert rows["P100"]["value"] == round(rows["P100"]["total"] * 1.85, 2)
    assert rows["P200"]["value"] == round(rows["P200"]["total"] * 3.40, 2)


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("payload, field", [
    ({"product": "P100", "location": "STO", "customer": "ICA", "month": "May-27", "qty": 5}, "month"),
    ({"product": "P100", "location": "STO", "customer": "ICA", "month": "Nov-26", "qty": -1}, "qty"),
    ({"product": "P100", "location": "STO", "customer": "ICA", "month": "Nov-26", "qty": "5"}, "qty"),
])
def test_plc_edit_validation(client, payload, field):
    resp = client.edit_plc(**payload)
    assert resp.status == 400 and resp.json()["field"] == field


@pytest.mark.api
@pytest.mark.regression
def test_export_headers_and_content_type(client):
    resp = client.export("PL")
    assert resp.headers["content-type"].startswith("text/csv")
    assert 'filename="forecast_PL.csv"' in resp.headers["content-disposition"]
    rows = list(csv.reader(io.StringIO(resp.text())))
    assert rows[0] == ["Product", "Location", "Nov-26", "Dec-26", "Jan-27", "Feb-27", "Mar-27", "Apr-27", "Total"]


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
def test_invalid_level(client):
    assert client.forecast("XYZ").status == 400


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
def test_standard_tenant_collaboration_api_forbidden(playwright, base_url):
    ctx = playwright.request.new_context(base_url=base_url)
    token = ctx.post("/api/auth/login", data={"username": "std_planner", "password": "Scp@1234"}).json()["token"]
    resp = ctx.get("/api/collaboration/comments?key=P100|STO", headers={"Authorization": f"Bearer {token}"})
    assert resp.status == 403
    ctx.dispose()


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize("locale, ok", [("sv-SE", True), ("fi-FI", True), ("de-DE", False)])
def test_login_locale_support(anon_api, locale, ok):
    resp = anon_api.post("/api/auth/login", data={"username": "åsa.lind", "password": "Scp@1234", "locale": locale})
    assert resp.ok is ok
    if ok:
        assert resp.json()["user"]["locale"] == locale


@pytest.mark.api
@pytest.mark.regression
def test_partial_item_update_keeps_other_fields(client):
    body = client.update_item("P100", moq=300).json()
    assert body == {"product": "P100", "description": "Rye Crispbread 250g", "lead_time_days": 14, "moq": 300, "safety_stock_days": 7}


@pytest.mark.api
@pytest.mark.defect
@pytest.mark.regression
def test_bot_blank_question_returns_400_fast(client):
    resp = client.ask("  ")
    assert resp.status == 400
    assert resp.json()["error"] == "Please enter a question"
