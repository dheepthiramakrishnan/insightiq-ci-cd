/*
  common.js
  ----------
  Shared helpers used across all InsightIQ pages: API base URL,
  a small fetch wrapper, currency formatting, and active nav-link
  highlighting.
*/

const API_BASE = "/api";

/** Wrapper around fetch() that throws a readable error on non-2xx responses. */
async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

async function apiPostForm(path, formData) {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

function formatCurrency(value) {
  if (value === null || value === undefined || isNaN(value)) return "$0.00";
  return "$" + Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/** Highlight the sidebar link matching the current page path. */
function highlightActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll(".iq-sidebar .nav-link").forEach((link) => {
    const href = link.getAttribute("href");
    if (href === path || (href === "/" && path === "/")) {
      link.classList.add("active");
    }
  });
}

document.addEventListener("DOMContentLoaded", highlightActiveNav);
