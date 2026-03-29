/**
 * main.js — Client-side logic
 * Handles: sidebar toggle, generate button loading state,
 *          conflict panel fetch, print-to-PDF helper.
 */

document.addEventListener("DOMContentLoaded", () => {

  // ── Sidebar toggle (mobile) ──
  const toggle  = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    document.addEventListener("click", (e) => {
      if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
        sidebar.classList.remove("open");
      }
    });
  }

  // ── Generate button — loading spinner ──
  const generateForm = document.getElementById("generateForm");
  if (generateForm) {
    generateForm.addEventListener("submit", (e) => {
      const btn = generateForm.querySelector("[data-loading]");
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Running Algorithm…`;
      }
    });
  }

  // ── Conflict Count Badge (async fetch) ──
  const conflictBadge = document.getElementById("conflictCount");
  if (conflictBadge) {
    fetch("/api/conflicts")
      .then(r => r.json())
      .then(data => {
        conflictBadge.textContent = data.total_edges;
        const panel = document.getElementById("conflictPanel");
        if (panel && data.conflict_pairs.length > 0) {
          let html = data.conflict_pairs.map(p =>
            `<li class="list-group-item list-group-item-warning py-1 px-2 small">
               <i class="bi bi-exclamation-triangle-fill text-warning me-1"></i>
               <strong>${p.a}</strong> ↔ <strong>${p.b}</strong>
             </li>`
          ).join("");
          panel.innerHTML = `<ul class="list-group list-group-flush rounded-3" style="max-height:220px;overflow-y:auto;">${html}</ul>`;
        } else if (panel) {
          panel.innerHTML = `<p class="text-muted small mb-0"><i class="bi bi-check-circle-fill text-success me-1"></i>No conflicts detected.</p>`;
        }
      })
      .catch(() => { if (conflictBadge) conflictBadge.textContent = "?"; });
  }

  // ── Print / PDF helper (browser print dialog) ──
  const printBtn = document.getElementById("printBtn");
  if (printBtn) {
    printBtn.addEventListener("click", () => window.print());
  }

  // ── Auto-dismiss flash alerts after 4 seconds ──
  document.querySelectorAll(".alert").forEach(alert => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 4000);
  });

});
