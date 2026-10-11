/*
  dashboard.js
  -------------
  Fetches KPIs and chart data for the Dashboard Home page and renders
  them using Plotly.
*/

const PLOTLY_LAYOUT_BASE = {
  margin: { t: 10, r: 10, b: 40, l: 50 },
  font: { family: "Segoe UI, sans-serif", size: 12 },
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
};
const PLOTLY_CONFIG = { responsive: true, displayModeBar: false };
const BLUE_SHADES = ["#1a56db", "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe", "#0b3a91"];

async function loadDashboard() {
  try {
    const kpis = await apiGet("/kpis");
    document.getElementById("empty-state").classList.add("d-none");
    document.getElementById("dashboard-content").classList.remove("d-none");
    document.getElementById("dataset-label").textContent = "Showing your most recently uploaded dataset";

    document.getElementById("kpi-total-sales").textContent = formatCurrency(kpis.total_sales);
    document.getElementById("kpi-total-profit").textContent = formatCurrency(kpis.total_profit);
    document.getElementById("kpi-total-orders").textContent = kpis.total_orders.toLocaleString();
    document.getElementById("kpi-total-customers").textContent = kpis.total_customers.toLocaleString();
    document.getElementById("kpi-best-category").textContent = kpis.best_selling_category;
    document.getElementById("kpi-top-region").textContent = kpis.highest_revenue_region;

    await Promise.all([
      renderMonthlyTrend(),
      renderSalesByRegion(),
      renderSalesByCategory(),
      renderTopProducts(),
    ]);
  } catch (err) {
    document.getElementById("dashboard-content").classList.add("d-none");
    document.getElementById("empty-state").classList.remove("d-none");
    document.getElementById("dataset-label").textContent = "";
  }
}

async function renderMonthlyTrend() {
  const res = await apiGet("/charts/monthly-sales-trend");
  const { months, sales } = res.data;
  Plotly.newPlot(
    "chart-monthly-trend",
    [{ x: months, y: sales, type: "scatter", mode: "lines+markers", line: { color: "#1a56db", width: 3 }, fill: "tozeroy", fillcolor: "rgba(26,86,219,0.08)" }],
    { ...PLOTLY_LAYOUT_BASE, height: 320 },
    PLOTLY_CONFIG
  );
}

async function renderSalesByRegion() {
  const res = await apiGet("/charts/sales-by-region");
  const { regions, sales } = res.data;
  Plotly.newPlot(
    "chart-sales-region",
    [{ labels: regions, values: sales, type: "pie", hole: 0.5, marker: { colors: BLUE_SHADES } }],
    { ...PLOTLY_LAYOUT_BASE, height: 320, showlegend: true },
    PLOTLY_CONFIG
  );
}

async function renderSalesByCategory() {
  const res = await apiGet("/charts/sales-by-category");
  const { categories, sales } = res.data;
  Plotly.newPlot(
    "chart-sales-category",
    [{ x: categories, y: sales, type: "bar", marker: { color: "#1a56db" } }],
    { ...PLOTLY_LAYOUT_BASE, height: 300 },
    PLOTLY_CONFIG
  );
}

async function renderTopProducts() {
  const res = await apiGet("/charts/top-products");
  const { products, sales } = res.data;
  Plotly.newPlot(
    "chart-top-products",
    [{ x: sales, y: products, type: "bar", orientation: "h", marker: { color: "#3b82f6" } }],
    { ...PLOTLY_LAYOUT_BASE, height: 300, yaxis: { automargin: true } },
    PLOTLY_CONFIG
  );
}

document.addEventListener("DOMContentLoaded", loadDashboard);
