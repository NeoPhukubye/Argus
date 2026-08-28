const API_BASE = window.location.origin;

async function analyze(repo, mode) {
  const loading = document.getElementById("loading");
  const result = document.getElementById("result");
  const error = document.getElementById("error");
  const btn = document.getElementById("submit-btn");

  loading.classList.remove("hidden");
  result.classList.add("hidden");
  error.classList.add("hidden");
  btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo, mode }),
    });
    if (!res.ok) {
      let msg = res.statusText;
      try {
        const data = await res.json();
        msg = data.detail || data.message || msg;
      } catch {
        msg = (await res.text()) || msg;
      }
      throw new Error(msg);
    }
    const data = await res.json();
    render(data);
  } catch (err) {
    error.textContent = err.message;
    error.classList.remove("hidden");
  } finally {
    loading.classList.add("hidden");
    btn.disabled = false;
  }
}

function render(data) {
  const result = document.getElementById("result");
  const scoreFill = document.getElementById("score-fill");
  const scoreText = document.getElementById("score-text");
  const modeBadge = document.getElementById("mode-badge");
  const narrative = document.getElementById("narrative");
  const dimensions = document.getElementById("dimensions");
  const report = document.getElementById("report");

  const pct = Math.round(data.overall_score * 100);
  scoreFill.style.width = pct + "%";
  scoreText.textContent = pct + "%";
  modeBadge.textContent = data.mode;
  narrative.textContent = data.narrative || "No narrative provided.";

  dimensions.innerHTML = "";
  for (const dim of data.dimensions) {
    const card = document.createElement("div");
    card.className = "dim-card";
    const dimPct = Math.round(dim.score * 100);
    const findingsHtml = dim.findings.map(f => `<li><strong>${f.passed ? "PASS" : "FAIL"}</strong> ${f.check_id}: ${f.evidence}</li>`).join("");
    card.innerHTML = `
      <div class="dim-header">
        <div class="dim-title">${dim.name}</div>
        <div class="dim-score">${dimPct}%</div>
      </div>
      <ul class="findings">${findingsHtml || "<li>No findings</li>"}</ul>
    `;
    dimensions.appendChild(card);
  }

  report.innerHTML = `<pre>${escapeHtml(data.markdown || JSON.stringify(data, null, 2))}</pre>`;
  result.classList.remove("hidden");
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

document.getElementById("analyze-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const repo = document.getElementById("repo").value.trim();
  const mode = document.getElementById("mode").value;
  if (!repo) return;
  analyze(repo, mode);
});
