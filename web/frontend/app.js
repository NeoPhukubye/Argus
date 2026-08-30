const API_BASE = location.protocol + "//" + location.host;
const FALLBACK_API_BASE = "https://argus-uh8y.onrender.com";

async function resolveApiBase() {
  const candidates = [API_BASE, FALLBACK_API_BASE];
  for (const base of candidates) {
    try {
      const res = await fetch(`${base}/api/health`, { method: "GET", mode: "cors" });
      if (res.ok) return base;
    } catch {
      continue;
    }
  }
  return FALLBACK_API_BASE;
}

let activeApiBase = null;
async function getApiBase() {
  if (!activeApiBase) {
    activeApiBase = await resolveApiBase();
  }
  return activeApiBase;
}

function scoreClass(pct) {
  if (pct >= 75) return "score-high";
  if (pct >= 50) return "score-mid";
  return "score-low";
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

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
    const apiBase = await getApiBase();
    const res = await fetch(`${apiBase}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo, mode }),
    });
    const text = await res.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      const raw = text.replace(/</g, "&lt;").slice(0, 500);
      throw new Error(`<b>Backend returned non-JSON (status ${res.status}):</b><br><pre>${raw}</pre>`);
    }
    if (!res.ok) {
      throw new Error(data.detail || data.message || res.statusText || "Request failed");
    }
    render(data);
  } catch (err) {
    const errorEl = document.getElementById("error");
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      errorEl.innerHTML = `<strong>Network Error</strong><br/>Unable to reach the analysis service. Please check your internet connection and try again.`;
    } else {
      errorEl.innerHTML = err.message;
    }
    errorEl.classList.remove("hidden");
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
  const resultTime = document.getElementById("result-time");
  const narrative = document.getElementById("narrative");
  const dimensions = document.getElementById("dimensions");
  const report = document.getElementById("report");

  const pct = Math.round(data.overall_score * 100);
  scoreFill.style.width = "0%";
  scoreText.textContent = "0%";
  scoreFill.className = "score-fill";
  scoreText.className = "score-text";

  modeBadge.textContent = data.mode;
  modeBadge.setAttribute("data-mode", data.mode);
  resultTime.textContent = new Date().toLocaleString();

  narrative.textContent = data.narrative || "No narrative provided.";

  dimensions.innerHTML = "";
  for (const dim of data.dimensions) {
    const card = document.createElement("div");
    card.className = "dim-card";
    const dimPct = Math.round(dim.score * 100);
    const dimScoreEl = document.createElement("div");
    dimScoreEl.className = `dim-score ${scoreClass(dimPct)}`;
    dimScoreEl.textContent = `${dimPct}%`;

    const findingsHtml = dim.findings.map(f => {
      const cls = f.passed ? "pass" : "fail";
      const label = f.passed ? "PASS" : "FAIL";
      return `<li><strong class="${cls}">${label}</strong> ${f.check_id}: ${f.evidence}</li>`;
    }).join("");

    card.innerHTML = `
      <div class="dim-header">
        <div class="dim-title">${dim.name}</div>
      </div>
    `;
    card.appendChild(dimScoreEl);
    const ul = document.createElement("ul");
    ul.className = "findings";
    ul.innerHTML = findingsHtml || "<li>No findings</li>";
    card.appendChild(ul);
    dimensions.appendChild(card);
  }

  report.innerHTML = `<pre>${escapeHtml(data.markdown || JSON.stringify(data, null, 2))}</pre>`;

  result.classList.remove("hidden");

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      scoreFill.style.width = pct + "%";
      scoreFill.classList.add(scoreClass(pct));
      scoreText.textContent = pct + "%";
      scoreText.classList.add(scoreClass(pct));
    });
  });
}

document.getElementById("analyze-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const repo = document.getElementById("repo").value.trim();
  const mode = document.getElementById("mode").value;
  if (!repo) return;
  analyze(repo, mode);
});
