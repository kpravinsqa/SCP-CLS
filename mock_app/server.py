"""
Mock "classic" Supply Chain Planning web application.

Synthetic re-creation of areas exercised while testing a long-running SCP
product: multi-tenant login with Nordic localisation, forecast hierarchy
aggregation (Product-Location-Customer -> Product-Location -> Product),
collaborative planning gated by subscription, item planning parameters,
CSV export and an in-app assistant ("PlanBot").
No proprietary code or data.
"""
from __future__ import annotations

import copy
import csv
import io
import itertools
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from mock_app.core import ApiError, App, require

app = App(Path(__file__).parent / "static")

MONTHS = ["Nov-26", "Dec-26", "Jan-27", "Feb-27", "Mar-27", "Apr-27"]
LOCALES = ["en-US", "en-GB", "sv-SE", "nb-NO", "da-DK", "fi-FI"]
COLLAB_SUBSCRIPTIONS = {"IBP", "COLLAB"}
BOT_MAX = 500

TENANTS = {
    "NORDIC": {"name": "Nordic Foods AB", "subscription": "IBP", "currency": "SEK"},
    "ACME": {"name": "Acme Retail Inc", "subscription": "STANDARD", "currency": "USD"},
    "EUROCO": {"name": "EuroCo Oy", "subscription": "COLLAB", "currency": "EUR"},
}
USERS_SEED = {
    "ibp_planner": {"password": "Scp@1234", "display_name": "IBP Planner", "tenant": "NORDIC"},
    "åsa.lind": {"password": "Scp@1234", "display_name": "Åsa Lindqvist", "tenant": "NORDIC"},
    "std_planner": {"password": "Scp@1234", "display_name": "Standard Planner", "tenant": "ACME"},
    "collab_planner": {"password": "Scp@1234", "display_name": "Collab Planner", "tenant": "EUROCO"},
}

PRODUCTS = {"P100": ("Rye Crispbread 250g", 1.85), "P200": ("Lingonberry Jam 400g", 3.40)}
LOCATIONS = {"STO": "Stockholm DC", "GOT": "Gothenburg DC"}
CUSTOMERS = {"ICA": "ICA Gruppen", "COOP": "Coop", "AXF": "Axfood"}

ITEMS_SEED = {
    "P100": {"lead_time_days": 14, "moq": 240, "safety_stock_days": 7},
    "P200": {"lead_time_days": 21, "moq": 120, "safety_stock_days": 10},
}

STATE: dict = {}
_ids = itertools.count(1)


def _seed_forecast():
    rows = []
    for pi, p in enumerate(PRODUCTS):
        for li, l in enumerate(LOCATIONS):
            for ci, c in enumerate(CUSTOMERS):
                base = 400 + 150 * pi + 80 * li + 35 * ci
                rows.append({"product": p, "location": l, "customer": c,
                             "values": {m: base + 10 * i * (ci + 1) for i, m in enumerate(MONTHS)}})
    return rows


def reset() -> None:
    global _ids
    _ids = itertools.count(1)
    app.revoke_all_tokens()
    STATE.clear()
    STATE["users"] = copy.deepcopy(USERS_SEED)
    STATE["forecast"] = _seed_forecast()
    STATE["items"] = copy.deepcopy(ITEMS_SEED)
    STATE["comments"] = defaultdict(list)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def tenant_of(req):
    return TENANTS[STATE["users"][req.user["username"]]["tenant"]]


# --------------------------------------------------------------------------- hooks / auth
@app.route("POST", "/api/test/reset", auth=False)
def _reset(req):
    reset()
    return {"status": "reset"}


@app.route("POST", "/api/auth/login", auth=False)
def login(req):
    username = require(req.body, "username", "Username")
    password = require(req.body, "password", "Password", strip=False)
    locale = req.body.get("locale") or "en-US"
    if locale not in LOCALES:
        raise ApiError(400, "Unsupported locale", field="locale")
    user = STATE["users"].get(username)
    if not user or user["password"] != password:
        raise ApiError(401, "Invalid username or password")
    tenant = TENANTS[user["tenant"]]
    profile = {"username": username, "display_name": user["display_name"], "locale": locale,
               "tenant": tenant["name"], "currency": tenant["currency"],
               "features": {"collaboration": tenant["subscription"] in COLLAB_SUBSCRIPTIONS}}
    return {"token": app.issue_token(profile), "user": profile}


# --------------------------------------------------------------------------- forecast hierarchy
LEVEL_KEYS = {"PLC": ("product", "location", "customer"), "PL": ("product", "location"), "P": ("product",)}


def aggregate(level: str):
    if level not in LEVEL_KEYS:
        raise ApiError(400, "Level must be one of PLC, PL, P", field="level")
    keys = LEVEL_KEYS[level]
    buckets: dict[tuple, dict] = {}
    for row in STATE["forecast"]:
        k = tuple(row[x] for x in keys)
        agg = buckets.setdefault(k, {**{x: row[x] for x in keys}, "values": {m: 0 for m in MONTHS}})
        for m in MONTHS:
            agg["values"][m] += row["values"][m]
    out = []
    for agg in buckets.values():
        agg["total"] = sum(agg["values"].values())
        agg["value"] = round(agg["total"] * PRODUCTS[agg["product"]][1], 2)
        agg["key"] = "|".join(agg[x] for x in keys)
        out.append(agg)
    return sorted(out, key=lambda r: r["key"])


@app.route("GET", "/api/forecast")
def forecast(req):
    level = (req.query.get("level") or "PLC").upper()
    rows = aggregate(level)
    return {"level": level, "months": MONTHS, "currency": tenant_of(req)["currency"], "rows": rows,
            "grand_total": sum(r["total"] for r in rows), "grand_value": round(sum(r["value"] for r in rows), 2)}


@app.route("PUT", "/api/forecast/plc")
def edit_plc(req):
    b = req.body
    month = b.get("month")
    qty = b.get("qty")
    if month not in MONTHS:
        raise ApiError(400, "Unknown month", field="month")
    if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
        raise ApiError(400, "Quantity must be a non-negative whole number", field="qty")
    for row in STATE["forecast"]:
        if (row["product"], row["location"], row["customer"]) == (b.get("product"), b.get("location"), b.get("customer")):
            row["values"][month] = qty
            return row
    raise ApiError(404, "Forecast row not found")


@app.route("GET", "/api/forecast/export")
def export(req):
    level = (req.query.get("level") or "PLC").upper()
    rows = aggregate(level)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([*(k.capitalize() for k in LEVEL_KEYS[level]), *MONTHS, "Total"])
    for r in rows:
        writer.writerow([*(r[k] for k in LEVEL_KEYS[level]), *(r["values"][m] for m in MONTHS), r["total"]])
    return 200, buf.getvalue(), {"Content-Type": "text/csv; charset=utf-8",
                                 "Content-Disposition": f'attachment; filename="forecast_{level}.csv"'}


# --------------------------------------------------------------------------- collaboration
@app.route("GET", "/api/collaboration/comments")
def comments(req):
    if not req.user["features"]["collaboration"]:
        raise ApiError(403, "Collaborative planning is not enabled for your subscription")
    key = req.query.get("key") or ""
    return {"key": key, "items": STATE["comments"][key]}


@app.route("POST", "/api/collaboration/comments")
def add_comment(req):
    if not req.user["features"]["collaboration"]:
        raise ApiError(403, "Collaborative planning is not enabled for your subscription")
    key = require(req.body, "key", "Product-location")
    text = require(req.body, "text", "Comment")
    if len(text) > 500:
        raise ApiError(400, "Comment must be 500 characters or fewer", field="text")
    item = {"id": next(_ids), "author": req.user["display_name"], "text": text, "at": now()}
    STATE["comments"][key].append(item)
    return 201, item


# --------------------------------------------------------------------------- item parameters
@app.route("GET", "/api/items")
def items(req):
    return {"items": [{"product": p, "description": PRODUCTS[p][0], **v} for p, v in STATE["items"].items()]}


@app.route("PUT", r"/api/items/(?P<product>P\d+)")
def update_item(req):
    product = req.params["product"]
    if product not in STATE["items"]:
        raise ApiError(404, "Item not found")
    rules = {"lead_time_days": (1, 365, "Lead time"), "moq": (1, 100_000, "MOQ"), "safety_stock_days": (0, 90, "Safety stock days")}
    updates = {}
    for field, (lo, hi, label) in rules.items():
        if field in req.body:
            val = req.body[field]
            if not isinstance(val, int) or isinstance(val, bool) or not lo <= val <= hi:
                raise ApiError(400, f"{label} must be a whole number between {lo} and {hi:,}", field=field)
            updates[field] = val
    STATE["items"][product].update(updates)
    return {"product": product, "description": PRODUCTS[product][0], **STATE["items"][product]}


# --------------------------------------------------------------------------- PlanBot assistant
ANSWERS = [
    (("forecast", "prognos"), "Forecasts are generated monthly at Product-Location-Customer level and aggregated upwards."),
    (("safety", "säkerhet"), "Safety stock days are maintained per item under Item Parameters."),
    (("export", "csv"), "Use Export CSV on the Forecast screen to download the selected hierarchy level."),
]


@app.route("POST", "/api/bot/ask")
def ask(req):
    q = (req.body.get("question") or "").strip()
    if not q:
        raise ApiError(400, "Please enter a question", field="question")
    if len(q) > BOT_MAX:
        raise ApiError(400, f"Questions are limited to {BOT_MAX} characters", field="question")
    for keys, answer in ANSWERS:
        if any(k in q.lower() for k in keys):
            return {"answer": answer}
    return {"answer": "Sorry, I don't know that yet. Try asking about forecasts, safety stock or export."}


def create_server(host: str = "127.0.0.1", port: int = 0):
    reset()
    return app.create_server(host, port)


if __name__ == "__main__":
    srv = create_server("127.0.0.1", 8000)
    print("Mock SCP Classic at http://127.0.0.1:8000  (ibp_planner / Scp@1234)")
    srv.serve_forever()
