# Supply Chain Planning (SCP Classic) — Python + Playwright Automation

![Tests](https://github.com/kpravinsqa/playwright-python-scp-classic/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Playwright](https://img.shields.io/badge/playwright-python-2EAD33) ![i18n](https://img.shields.io/badge/i18n-Nordic%20locales-005a8c)

UI and API automation for a **classic, multi-tenant Supply Chain Planning** web application, modelled on areas I tested on
the **SCP Classic** project: forecast hierarchy aggregation (**PLC → PL → P**), collaborative planning gated by
subscription (IBP), **Nordic localisation** (sv-SE, nb-NO, da-DK, fi-FI), item planning parameters, CSV export and the
in-app assistant.

> **Confidentiality note:** original portfolio project with **no proprietary code, data or screens**. The system under
> test is a mock app (`mock_app/`) that reproduces the domain behaviour.

## Production-defect regression guards (`pytest -m defect`)

Each of these reproduces the pattern of a real defect I reported on the project and fails if it comes back:

| Defect pattern | Sev / Pri | Automated guard |
|---|---|---|
| PLC → PL aggregation showed wrong forecast | High / High | `test_pl_total_equals_sum_of_plc_children`, `test_every_level_reconciles_with_plc` |
| Collaborative planning hidden for IBP customers | High / High | `test_collaboration_menu_by_subscription` |
| Login failure for Swedish-locale users | Critical | `test_swedish_locale_login_with_nordic_characters` |
| Wrong currency sign displayed | Low / Low | `test_currency_follows_tenant_not_ui_language` |
| Assistant "thinking" forever on blank input | Low / Low | `test_planbot_blank_input_does_not_hang` |

## Coverage (68 automated checks)

| Suite | Module | Key scenarios |
|---|---|---|
| TS-01 | Login | default locale, Nordic characters in username, invalid credentials, logout |
| TS-02 | Forecast hierarchy | row counts per level, PL = Σ PLC children (4 nodes), drill-down toggle, PLC edit rolls up to product |
| TS-03 | Collaboration | menu by subscription (IBP / COLLAB / STANDARD), direct-URL block, post comment, validation, scoping |
| TS-04 | Item parameters | persistence, 7 invalid boundaries, 6 valid edges (lead time 1/365, MOQ 1/100 000, SS days 0/90) |
| TS-05 | Export | CSV download for each level: filename, header, row count, totals reconcile |
| TS-06 | Localisation | labels and number / currency format for 6 locales via `Intl`, currency driven by tenant |
| TS-07 | Assistant | blank / whitespace input, known topic, Swedish keyword, 500-char limit |
| API | REST | level reconciliation, monthly reconciliation, valuation, edit validation, export headers, 403, locale support |

## Getting started

```bash
git clone https://github.com/kpravinsqa/playwright-python-scp-classic.git
cd playwright-python-scp-classic
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
pytest                # pytest -m defect | -m smoke | -m api | -n auto
```

Manual exploration: `python -m mock_app.server` → http://127.0.0.1:8000. Users: `ibp_planner`, `std_planner`,
`collab_planner`, `åsa.lind`; password `Scp@1234`.

## Author

**Pravin Khedkar**, QA Lead / SDET · [@kpravinsqa](https://github.com/kpravinsqa)
