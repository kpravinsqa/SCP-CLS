const I18N = {
  en: { forecast: "Forecast", collaboration: "Collaboration", items: "Item Parameters", assistant: "PlanBot", logout: "Logout", total: "Total", export: "Export CSV", value: "Forecast value" },
  sv: { forecast: "Prognos", collaboration: "Samarbete", items: "Artikelparametrar", assistant: "PlanBot", logout: "Logga ut", total: "Totalt", export: "Exportera CSV", value: "Prognosvärde" },
  nb: { forecast: "Prognose", collaboration: "Samarbeid", items: "Vareparametere", assistant: "PlanBot", logout: "Logg ut", total: "Totalt", export: "Eksporter CSV", value: "Prognoseverdi" },
  da: { forecast: "Prognose", collaboration: "Samarbejde", items: "Vareparametre", assistant: "PlanBot", logout: "Log ud", total: "I alt", export: "Eksportér CSV", value: "Prognoseværdi" },
  fi: { forecast: "Ennuste", collaboration: "Yhteistyö", items: "Nimikeparametrit", assistant: "PlanBot", logout: "Kirjaudu ulos", total: "Yhteensä", export: "Vie CSV", value: "Ennusteen arvo" },
};
function t(key) { const u = API.user() || {}; const lang = (u.locale || "en-US").split("-")[0]; return (I18N[lang] || I18N.en)[key]; }
function fmtMoney(v) { const u = API.user(); return new Intl.NumberFormat(u.locale, { style: "currency", currency: u.currency }).format(v); }
function fmtNum(v) { return new Intl.NumberFormat(API.user().locale).format(v); }
function shell(active) {
  if (!requireAuth()) return false;
  const u = API.user();
  const links = [["forecast", t("forecast"), "forecast.html"], ["items", t("items"), "items.html"], ["assistant", t("assistant"), "assistant.html"]];
  if (u.features.collaboration) links.splice(1, 0, ["collaboration", t("collaboration"), "collaboration.html"]);
  renderShell(active, links, "SCP Classic (demo)");
  document.documentElement.lang = u.locale;
  $('[data-testid="logout"]').textContent = t("logout");
  const tenant = el("span", { class: "badge", testid: "tenant-badge" }, u.tenant); $('[data-testid="user-badge"]').before(tenant);
  if (active === "collaboration" && !u.features.collaboration) {
    document.querySelector("main").innerHTML = '<div class="card" data-testid="feature-disabled"><h1>Not available</h1><p>Collaborative planning is not enabled for your subscription.</p></div>';
    return false;
  }
  return true;
}
