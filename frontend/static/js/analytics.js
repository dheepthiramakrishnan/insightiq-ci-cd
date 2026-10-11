/*
  analytics.js
  -------------
  Drives the Analytics page: loads filter options, applies Year /
  Region / Category filters, and re-renders KPIs + charts accordingly.
*/

const PLOTLY_LAYOUT_BASE = {
  margin: { t: 10, r: 10, b: 40, l: 50 },
  font: { family: "Segoe UI, sans-serif", size: 12 },
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
};
const PLOTLY_CONFIG = { responsive: true, displayModeBar: false };
const BLUE_SHADES = ["#1a56db", "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe", "#0b3a91"];

function currentFilters() {
  const year = document.getElementById("filter-year").value;
  const region = document.getElementById("filter-region").value;
  const category = document.getElementById("filter-category").value;
  const params = new URLSearchParams();
  if (year) params.append("year", year);
  if (region) params.append("region", region);
  if (category) params.append("category", category);
  return params.toString();
}

async function loadFilterOptions() {
  const opts = await apiGet("/filters/options");
  const yearSelect = document.getElementById("filter-year");
  const regionSelect = document.getElementById("filter-region");
  const categorySelect = document.getElementById("filter-category");

  opts.years.forEach((y) => yearSelect.insertAdjacentHTML("beforeend", `<option value="${y}">${y}</option>`));
  opts.regions.forEach((r) => regionSelect.insertAdjacentHTML("beforeend", `<option value="${r}">${r}</option>`));
  opts.categories.forEach((c) => categorySelect.insertAdjacentHTML("beforeend", `<option value="${c}">${c}</option>`));
}

async function loadAnalytics() {
  const qs = currentFilters();
  try {
    const kpis = await apiGet(`/kpis?${qs}`);
    document.getElementById("empty-state").classList.add("d-none");
    document.getElementById("analytics-content").classList.remove("d-none");

    document.getElementById("kpi-total-sales").textContent = formatCurrency(kpis.total_sales);
    document.getElementById("kpi-total-profit").textContent = formatCurrency(kpis.total_profit);
    document.getElementById("kpi-total-orders").textContent = kpis.total_orders.toLocaleString();
    document.getElementById("kpi-total-customers").textContent = kpis.total_customers.toLocaleString();

    await Promise.all([
      renderChart("monthly-sales-trend", qs, (data) =>
        Plotly.newPlot("chart-monthly-trend", [{ x: data.months, y: data.sales, type: "scatter", mode: "lines+markers", line: { color: "#1a56db", width: 3 } }], { ...PLOTLY_LAYOUT_BASE, height: 300 }, PLOTLY_CONFIG)
      ),
      renderChart("sales-by-region", qs, (data) =>
        Plotly.newPlot("chart-sales-region", [{ labels: data.regions, values: data.sales, type: "pie", hole: 0.5, marker: { colors: BLUE_SHADES } }], { ...PLOTLY_LAYOUT_BASE, height: 300 }, PLOTLY_CONFIG)
      ),
      renderChart("sales-by-category", qs, (data) =>
        Plotly.newPlot("chart-sales-category", [{ x: data.categories, y: data.sales, type: "bar", marker: { color: "#1a56db" } }], { ...PLOTLY_LAYOUT_BASE, height: 300 }, PLOTLY_CONFIG)
      ),
      renderChart("profit-by-category", qs, (data) =>
        Plotly.newPlot("chart-profit-category", [{ x: data.categories, y: data.profit, type: "bar", marker: { color: "#16a34a" } }], { ...PLOTLY_LAYOUT_BASE, height: 300 }, PLOTLY_CONFIG)
      ),
      renderChart("top-products", qs, (data) =>
        Plotly.newPlot("chart-top-products", [{ x: data.sales, y: data.products, type: "bar", orientation: "h", marker: { color: "#3b82f6" } }], { ...PLOTLY_LAYOUT_BASE, height: 320, yaxis: { automargin: true } }, PLOTLY_CONFIG)
      ),
    ]);
  } catch (err) {
    document.getElementById("analytics-content").classList.add("d-none");
    document.getElementById("empty-state").classList.remove("d-none");
  }
}

async function renderChart(name, qs, renderFn) {
  const res = await apiGet(`/charts/${name}?${qs}`);
  renderFn(res.data);
}

document.getElementById("apply-filters-btn").addEventListener("click", loadAnalytics);

document.addEventListener("DOMContentLoaded", async () => {
  try {
    await loadFilterOptions();
  } catch (err) {
    /* No dataset uploaded yet; loadAnalytics will show the empty state */
  }
  loadAnalytics();
});
