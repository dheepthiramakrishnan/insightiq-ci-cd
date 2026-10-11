/*
  upload.js
  ----------
  Handles CSV file selection, drag-and-drop, upload submission, and
  rendering of upload history on the Upload Dataset page.
*/

const fileInput = document.getElementById("file-input");
const dropzone = document.getElementById("dropzone");
const dropzoneText = document.getElementById("dropzone-text");
const uploadBtn = document.getElementById("upload-btn");
const uploadForm = document.getElementById("upload-form");
const statusBox = document.getElementById("upload-status");

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    dropzoneText.textContent = `Selected: ${fileInput.files[0].name}`;
    uploadBtn.disabled = false;
  }
});

["dragover", "dragleave", "drop"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (e) => e.preventDefault());
});
dropzone.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  if (file) {
    fileInput.files = e.dataTransfer.files;
    dropzoneText.textContent = `Selected: ${file.name}`;
    uploadBtn.disabled = false;
  }
});

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!fileInput.files.length) return;

  uploadBtn.disabled = true;
  uploadBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Processing...`;
  statusBox.innerHTML = "";

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  try {
    const result = await apiPostForm("/upload", formData);
    statusBox.innerHTML = `
      <div class="alert alert-success">
        <i class="bi bi-check-circle-fill"></i> ${result.message}
        <div class="small mt-1">
          ${result.row_count} rows &middot; ${formatCurrency(result.total_sales)} total sales &middot; ${formatCurrency(result.total_profit)} total profit
        </div>
      </div>`;
    dropzoneText.textContent = "Click to choose a CSV file, or drag it here";
    fileInput.value = "";
    loadUploadHistory();
  } catch (err) {
    statusBox.innerHTML = `<div class="alert alert-danger"><i class="bi bi-x-circle-fill"></i> ${err.message}</div>`;
  } finally {
    uploadBtn.disabled = false;
    uploadBtn.innerHTML = `<i class="bi bi-upload"></i> Upload &amp; Process`;
  }
});

async function loadUploadHistory() {
  const historyBox = document.getElementById("upload-history");
  try {
    const history = await apiGet("/uploads");
    if (!history.length) {
      historyBox.innerHTML = `<p class="text-muted small">No uploads yet.</p>`;
      return;
    }
    historyBox.innerHTML = history
      .map(
        (item) => `
        <div class="d-flex justify-content-between align-items-center border-bottom py-2">
          <div>
            <div class="fw-semibold small">${item.filename}</div>
            <div class="text-muted small">${item.row_count} rows &middot; ${new Date(item.uploaded_at).toLocaleString()}</div>
          </div>
        </div>`
      )
      .join("");
  } catch (err) {
    historyBox.innerHTML = `<p class="text-danger small">Could not load history.</p>`;
  }
}

document.addEventListener("DOMContentLoaded", loadUploadHistory);
