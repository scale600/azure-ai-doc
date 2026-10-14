"use strict";

const cfg = window.APP_CONFIG || {};
const API_BASE = cfg.functionAppUrl || "";
const API_KEY = cfg.apiKey || "";

const $ = (sel) => document.querySelector(sel);

let docs = [];
let currentFilter = "all";
let selectedFile = null;
let currentDetailId = null;

// --- HTTP helpers ----------------------------------------------------------

async function api(path, options = {}) {
  const headers = Object.assign(
    { "Content-Type": "application/json", "x-api-key": API_KEY },
    options.headers || {}
  );
  const res = await fetch(`${API_BASE}${path}`, Object.assign({}, options, { headers }));
  const text = await res.text();
  const body = text ? JSON.parse(text) : {};
  if (!res.ok) {
    throw new Error(body.error || `HTTP ${res.status}`);
  }
  return body;
}

function escapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function setStatus(text, show = true) {
  const el = $("#upload-status");
  el.hidden = !show;
  el.textContent = text;
}

// --- Rendering -------------------------------------------------------------

function statusBadge(status) {
  const cls = {
    UPLOADED: "badge-gray",
    PROCESSING: "badge-blue",
    REPROCESSING: "badge-blue",
    COMPLETED: "badge-green",
    FAILED: "badge-red",
    REJECTED: "badge-red",
  }[status] || "badge-gray";
  return `<span class="badge ${cls}">${status}</span>`;
}

function renderStats(list) {
  const total = list.length;
  const completed = list.filter((d) => d.status === "COMPLETED").length;
  const failed = list.filter((d) => d.status === "FAILED").length;
  const done = completed + failed;
  const rate = done > 0 ? Math.round((completed / done) * 100) + "%" : "—";

  $("#stat-total").textContent = total;
  $("#stat-completed").textContent = completed;
  $("#stat-failed").textContent = failed;
  $("#stat-rate").textContent = rate;
  $("#stats-bar").hidden = total === 0;
}

function renderFilterCounts(list) {
  $("#count-all").textContent = list.length;
  $("#count-processing").textContent = list.filter((d) =>
    ["UPLOADED", "PROCESSING", "REPROCESSING"].includes(d.status)
  ).length;
  $("#count-completed").textContent = list.filter((d) => d.status === "COMPLETED").length;
  $("#count-failed").textContent = list.filter((d) =>
    ["FAILED", "REJECTED"].includes(d.status)
  ).length;
}

function filteredDocs(list) {
  if (currentFilter === "all") return list;
  if (currentFilter === "PROCESSING") {
    return list.filter((d) => ["UPLOADED", "PROCESSING", "REPROCESSING"].includes(d.status));
  }
  if (currentFilter === "FAILED") {
    return list.filter((d) => ["FAILED", "REJECTED"].includes(d.status));
  }
  return list.filter((d) => d.status === currentFilter);
}

function renderList() {
  const tbody = $("#doc-list");
  const visible = filteredDocs(docs);
  if (!visible.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty">No documents</td></tr>';
    return;
  }
  tbody.innerHTML = visible
    .map((d) => {
      const actions = d.status === "FAILED"
        ? `<button class="link reprocess" data-id="${d.documentId}">Reprocess</button>`
        : "";
      return `
      <tr>
        <td>${escapeHtml(d.fileName)}</td>
        <td>${escapeHtml(d.documentType || "—")}</td>
        <td>${statusBadge(d.status)}</td>
        <td>${escapeHtml(d.uploadedAt ? new Date(d.uploadedAt).toLocaleString() : "—")}</td>
        <td>${actions} <button class="link view" data-id="${d.documentId}">View</button></td>
      </tr>`;
    })
    .join("");

  tbody.querySelectorAll("button.view").forEach((btn) =>
    btn.addEventListener("click", () => showDetail(btn.dataset.id))
  );
  tbody.querySelectorAll("button.reprocess").forEach((btn) =>
    btn.addEventListener("click", () => reprocess(btn.dataset.id))
  );
}

function confidenceGauge(c) {
  if (c == null) return '<span class="muted-note">—</span>';
  const pct = Math.round(c * 100);
  return `<div class="confidence"><div class="confidence-bar"><div class="confidence-fill" style="width:${pct}%"></div></div><span class="confidence-value">${pct}%</span></div>`;
}

function pills(items, cls, icon, emptyLabel) {
  if (!items || !items.length) return `<span class="muted-note">${emptyLabel}</span>`;
  return `<div class="pills">${items
    .map((i) => `<span class="pill ${cls}">${icon} ${escapeHtml(i)}</span>`)
    .join("")}</div>`;
}

function keyFieldsList(kf) {
  const entries = Object.entries(kf || {});
  if (!entries.length) return "";
  return `<h3>Key fields</h3><ul class="kv-list">${entries
    .map(
      ([k, v]) =>
        `<li><span class="k">${escapeHtml(k)}</span><span>${escapeHtml(String(v ?? ""))}</span></li>`
    )
    .join("")}</ul>`;
}

function renderDetail(d) {
  const body = $("#detail-body");
  const parts = [
    `<div class="detail-grid">
      <div>Status</div><div>${statusBadge(d.status)}</div>
      <div>Classification</div><div>${escapeHtml(d.classification || "—")}</div>
      <div>Confidence</div><div>${confidenceGauge(d.confidence)}</div>
      <div>Model</div><div>${escapeHtml(d.modelName || "—")}</div>
      <div>Uploaded</div><div>${escapeHtml(d.uploadedAt ? new Date(d.uploadedAt).toLocaleString() : "—")}</div>
      <div>Processed</div><div>${escapeHtml(d.processedAt ? new Date(d.processedAt).toLocaleString() : "—")}</div>
    </div>`,
  ];

  if (d.status === "FAILED") {
    parts.push(
      `<div class="error-box">⚠️ ${escapeHtml(d.errorMessage || "Processing failed")}</div>`
    );
    parts.push(`<button id="reprocess-btn">Reprocess</button>`);
  }

  parts.push(`<h3>Summary</h3><p>${escapeHtml(d.summary || "—")}</p>`);
  parts.push(keyFieldsList(d.keyFields));
  parts.push(`<h3>Risk flags</h3>${pills(d.riskFlags, "risk", "⚠️", "None")}`);
  parts.push(`<h3>Missing fields</h3>${pills(d.missingFields, "missing", "❗", "None")}`);

  body.innerHTML = parts.join("");

  const rbtn = body.querySelector("#reprocess-btn");
  if (rbtn) rbtn.addEventListener("click", () => reprocess(d.documentId));
}

// --- Data loading ----------------------------------------------------------

async function refreshList() {
  try {
    const data = await api("/api/documents");
    docs = data.documents || [];
    renderStats(docs);
    renderFilterCounts(docs);
    renderList();
  } catch (e) {
    $("#doc-list").innerHTML = `<tr><td colspan="5" class="empty">Error: ${escapeHtml(
      e.message
    )}</td></tr>`;
  }
}

async function showDetail(id) {
  try {
    const d = await api(`/api/documents/${id}`);
    currentDetailId = id;
    $("#detail-card").hidden = false;
    renderDetail(d);
    $("#detail-card").scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (e) {
    setStatus(`Failed to load document: ${e.message}`, true);
  }
}

// --- Upload ----------------------------------------------------------------

async function upload() {
  if (!selectedFile) return;
  const btn = $("#upload-btn");
  btn.disabled = true;
  setStatus("Uploading…", true);

  const form = new FormData();
  form.append("file", selectedFile);
  const hint = $("#type-select").value;
  if (hint) form.append("document_type", hint);

  try {
    const res = await fetch(`${API_BASE}/api/documents`, {
      method: "POST",
      headers: { "x-api-key": API_KEY },
      body: form,
    });
    const body = await res.json();
    if (!res.ok) throw new Error(body.error || `HTTP ${res.status}`);

    selectedFile = null;
    $("#file-input").value = "";
    $("#selected-file").textContent = "";
    setStatus("Processing…", true);
    await refreshList();
    pollUntilDone(body.documentId);
  } catch (err) {
    setStatus(`Upload failed: ${err.message}`, true);
  } finally {
    btn.disabled = false;
  }
}

async function pollUntilDone(id, attempts = 0) {
  if (attempts > 40) {
    await refreshList();
    return;
  }
  try {
    const d = await api(`/api/documents/${id}`);
    if (d.status === "COMPLETED" || d.status === "FAILED" || d.status === "REJECTED") {
      setStatus(`Done: ${d.status}`, true);
      await refreshList();
      if (currentDetailId === id) await showDetail(id);
      return;
    }
  } catch (_) {
    /* transient — keep polling */
  }
  setTimeout(() => pollUntilDone(id, attempts + 1), 2000);
}

// --- Reprocess -------------------------------------------------------------

async function reprocess(id) {
  setStatus("Reprocessing…", true);
  try {
    await api(`/api/documents/${id}/reprocess`, { method: "POST" });
    await refreshList();
    pollUntilDone(id);
  } catch (err) {
    setStatus(`Reprocess failed: ${err.message}`, true);
  }
}

// --- Event wiring ----------------------------------------------------------

function setupDropzone() {
  const dz = $("#dropzone");
  const input = $("#file-input");

  const setFile = (file) => {
    selectedFile = file;
    $("#selected-file").textContent = file ? file.name : "";
    $("#upload-btn").disabled = !file;
  };

  dz.addEventListener("click", () => input.click());
  dz.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      input.click();
    }
  });

  ["dragenter", "dragover"].forEach((ev) =>
    dz.addEventListener(ev, (e) => {
      e.preventDefault();
      dz.classList.add("dragover");
    })
  );
  ["dragleave", "drop"].forEach((ev) =>
    dz.addEventListener(ev, (e) => {
      e.preventDefault();
      dz.classList.remove("dragover");
    })
  );

  dz.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (file) setFile(file);
  });

  input.addEventListener("change", () => setFile(input.files[0] || null));
}

$("#upload-btn").addEventListener("click", upload);
$("#refresh-btn").addEventListener("click", refreshList);
$("#close-detail").addEventListener("click", () => {
  $("#detail-card").hidden = true;
  currentDetailId = null;
});

document.querySelectorAll(".filter-tab").forEach((tab) =>
  tab.addEventListener("click", () => {
    document.querySelectorAll(".filter-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    currentFilter = tab.dataset.filter;
    renderList();
  })
);

setupDropzone();
refreshList();
