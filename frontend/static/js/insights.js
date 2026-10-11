/*
  insights.js
  ------------
  Loads (or triggers generation of) AI business insights from the
  Gemini-powered /api/insights endpoint and renders them.
*/

async function loadInsights() {
  const emptyState = document.getElementById("empty-state");
  const loadingState = document.getElementById("loading-state");
  const content = document.getElementById("insights-content");
  const errorState = document.getElementById("error-state");

  loadingState.classList.remove("d-none");

  try {
    const insights = await apiGet("/insights");

    loadingState.classList.add("d-none");
    content.classList.remove("d-none");

    document.getElementById("executive-summary").textContent = insights.executive_summary;
    fillList("key-trends", insights.key_trends);
    fillList("best-products", insights.best_performing_products);
    fillList("weak-regions", insights.weak_performing_regions);
    fillList("recommendations", insights.recommendations);
  } catch (err) {
    loadingState.classList.add("d-none");
    if (err.message && err.message.toLowerCase().includes("no uploaded dataset")) {
      emptyState.classList.remove("d-none");
    } else {
      errorState.textContent = err.message || "Something went wrong generating insights.";
      errorState.classList.remove("d-none");
    }
  }
}

function fillList(elementId, items) {
  const el = document.getElementById(elementId);
  if (!items || !items.length) {
    el.innerHTML = `<li class="text-muted">No data available.</li>`;
    return;
  }
  el.innerHTML = items.map((item) => `<li>${item}</li>`).join("");
}

document.addEventListener("DOMContentLoaded", loadInsights);
