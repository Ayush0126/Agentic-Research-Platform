/* ═══════════════════════════════════════════════════ */
/*  AGENTIC RESEARCH PLATFORM — Frontend Logic         */
/* ═══════════════════════════════════════════════════ */

const API_BASE = "http://localhost:8000";
const STORAGE_KEY = "agentic_reports";

// ══════════════════════════════════════════════════════
//  LANDING ↔ DASHBOARD NAVIGATION
// ══════════════════════════════════════════════════════

function enterDashboard() {
    localStorage.setItem("agentic_visited", "true");
    document.getElementById("landing").classList.remove("active");
    document.getElementById("dashboard").classList.add("active");
    updateGreeting();
    updateLibraryCount();
}

function goToLanding(e) {
    if (e) e.preventDefault();
    document.getElementById("dashboard").classList.remove("active");
    document.getElementById("landing").classList.add("active");
}

// Skip landing if user has visited before
function checkReturningUser() {
    if (localStorage.getItem("agentic_visited") === "true") {
        document.getElementById("landing").classList.remove("active");
        document.getElementById("dashboard").classList.add("active");
        updateGreeting();
        updateLibraryCount();
    }
}

// Landing page section scrolling
function scrollToAbout(e) { e.preventDefault(); document.getElementById("about-section").scrollIntoView({ behavior: "smooth" }); }
function scrollToCapabilities(e) { e.preventDefault(); document.getElementById("capabilities-section").scrollIntoView({ behavior: "smooth" }); }
function scrollToUseCases(e) { e.preventDefault(); document.getElementById("usecases-section").scrollIntoView({ behavior: "smooth" }); }

// ══════════════════════════════════════════════════════
//  SIDEBAR NAVIGATION
// ══════════════════════════════════════════════════════

function navigateTo(viewName, navElement, event) {
    if (event) event.preventDefault();

    // Switch active view
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    const targetView = document.getElementById(`${viewName}-view`);
    if (targetView) targetView.classList.add("active");

    // Update sidebar active state
    document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
    if (navElement) navElement.classList.add("active");

    // View-specific initialization
    if (viewName === "library") renderLibrary();
    if (viewName === "settings") loadHealthStatus();
    if (viewName === "home") updateGreeting();
    if (viewName === "new-research") {
        setTimeout(() => document.getElementById("new-research-input")?.focus(), 100);
    }
}

function showView(viewName) {
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    document.getElementById(`${viewName}-view`).classList.add("active");
}

// ══════════════════════════════════════════════════════
//  GREETING
// ══════════════════════════════════════════════════════

function updateGreeting() {
    const hour = new Date().getHours();
    let greeting;
    if (hour < 12) greeting = "Good morning,";
    else if (hour < 17) greeting = "Good afternoon,";
    else greeting = "Good evening,";
    const el = document.getElementById("greeting-message");
    if (el) el.textContent = greeting;
}

// ══════════════════════════════════════════════════════
//  REPORT STORAGE (localStorage)
// ══════════════════════════════════════════════════════

function getSavedReports() {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    } catch { return []; }
}

function saveReport(report) {
    const reports = getSavedReports();
    const entry = {
        id: Date.now().toString(),
        savedAt: new Date().toISOString(),
        report: report,
    };
    reports.unshift(entry); // newest first
    // Keep max 50 reports
    if (reports.length > 50) reports.pop();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reports));
    updateLibraryCount();
    return entry.id;
}

function deleteReport(id) {
    let reports = getSavedReports();
    reports = reports.filter((r) => r.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reports));
    updateLibraryCount();
    renderLibrary();
}

function clearLibrary() {
    if (confirm("Delete all saved reports? This cannot be undone.")) {
        localStorage.removeItem(STORAGE_KEY);
        updateLibraryCount();
        renderLibrary();
    }
}

function updateLibraryCount() {
    const count = getSavedReports().length;
    const badge = document.getElementById("library-count");
    if (badge) {
        badge.textContent = count > 0 ? count : "";
        badge.style.display = count > 0 ? "inline-flex" : "none";
    }
}

// ══════════════════════════════════════════════════════
//  LIBRARY RENDERING
// ══════════════════════════════════════════════════════

function renderLibrary() {
    const reports = getSavedReports();
    const emptyEl = document.getElementById("library-empty");
    const listEl = document.getElementById("library-list");

    if (reports.length === 0) {
        emptyEl.style.display = "block";
        listEl.innerHTML = "";
        return;
    }

    emptyEl.style.display = "none";
    listEl.innerHTML = reports
        .map((entry) => {
            const r = entry.report;
            const date = new Date(entry.savedAt).toLocaleDateString("en-US", {
                month: "short", day: "numeric", year: "numeric",
                hour: "2-digit", minute: "2-digit",
            });
            const sources = r.sources?.length || 0;
            const findings = r.key_findings?.length || 0;
            const totalTime = r.agent_trace
                ? r.agent_trace.reduce((s, t) => s + (t.duration_seconds || 0), 0).toFixed(0)
                : "?";

            return `
                <div class="library-card glass-card" onclick="viewSavedReport('${entry.id}')">
                    <div class="library-card-header">
                        <h4>${escapeHtml(r.title || "Untitled Report")}</h4>
                        <button class="delete-btn" onclick="event.stopPropagation(); deleteReport('${entry.id}')" title="Delete">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                        </button>
                    </div>
                    <p class="library-card-query">${escapeHtml(r.query || "")}</p>
                    <div class="library-card-meta">
                        <span>📅 ${date}</span>
                        <span>📚 ${sources} sources</span>
                        <span>🔬 ${findings} findings</span>
                        <span>⏱ ${totalTime}s</span>
                    </div>
                </div>
            `;
        })
        .join("");
}

function viewSavedReport(id) {
    const reports = getSavedReports();
    const entry = reports.find((r) => r.id === id);
    if (!entry) return;
    renderReport(entry.report);
    showView("results");
}

// ══════════════════════════════════════════════════════
//  EXPLORE — FILL AND SUBMIT
// ══════════════════════════════════════════════════════

function fillQuery(query) {
    const input = document.getElementById("query-input");
    input.value = query;
    input.focus();
}

function fillAndSubmit(query) {
    navigateTo("home", document.querySelector("[data-view=home]"));
    setTimeout(() => {
        document.getElementById("query-input").value = query;
        submitResearch(new Event("submit"));
    }, 100);
}

function submitResearchFrom(inputId, event) {
    event.preventDefault();
    const input = document.getElementById(inputId);
    const query = input.value.trim();
    if (!query) return;
    document.getElementById("query-input").value = query;
    submitResearch(event);
}

// ══════════════════════════════════════════════════════
//  SETTINGS — HEALTH STATUS
// ══════════════════════════════════════════════════════

async function loadHealthStatus() {
    const container = document.getElementById("settings-status");
    container.innerHTML = '<div class="status-loading">Checking status...</div>';

    try {
        const r = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(15000) });
        const data = await r.json();
        container.innerHTML = `
            <div class="status-grid">
                <div class="status-row">
                    <span>Platform</span>
                    <span class="status-badge success">● Running</span>
                </div>
                <div class="status-row">
                    <span>LLM Provider</span>
                    <span class="status-value">${data.llm_provider || "unknown"}</span>
                </div>
                <div class="status-row">
                    <span>Groq API</span>
                    <span class="status-badge ${data.groq_available ? "success" : "inactive"}">
                        ${data.groq_available ? "● Connected" : "○ " + (data.groq_configured ? "Unavailable" : "Not configured")}
                    </span>
                </div>
                <div class="status-row">
                    <span>Groq Model</span>
                    <span class="status-value">${data.groq_model || "-"}</span>
                </div>
                <div class="status-row">
                    <span>Ollama</span>
                    <span class="status-badge ${data.ollama_available ? "success" : "inactive"}">
                        ${data.ollama_available ? "● Available" : "○ Not running"}
                    </span>
                </div>
                <div class="status-row">
                    <span>Ollama Model</span>
                    <span class="status-value">${data.ollama_model || "-"}</span>
                </div>
            </div>
        `;
    } catch (e) {
        container.innerHTML = `
            <div class="status-badge error">● Backend unreachable</div>
            <p style="margin-top:8px;font-size:13px;opacity:0.6;">Make sure the server is running on ${API_BASE}</p>
        `;
    }
}

// ══════════════════════════════════════════════════════
//  PIPELINE ANIMATION
// ══════════════════════════════════════════════════════

const STEPS = ["router", "research", "extraction", "factcheck", "synthesis"];
let stepInterval = null;

function startPipelineAnimation() {
    STEPS.forEach((s) => {
        const el = document.getElementById(`step-${s}`);
        el.classList.remove("active", "done");
    });
    activateStep(0);
    let idx = 0;
    const durations = [8000, 25000, 50000, 25000, 25000];
    function advance() {
        if (idx < STEPS.length - 1) {
            completeStep(idx); idx++; activateStep(idx);
            if (idx < STEPS.length - 1) stepInterval = setTimeout(advance, durations[idx]);
        }
    }
    stepInterval = setTimeout(advance, durations[0]);
}

function stopPipelineAnimation() {
    if (stepInterval) { clearTimeout(stepInterval); stepInterval = null; }
    STEPS.forEach((s) => {
        const el = document.getElementById(`step-${s}`);
        el.classList.remove("active"); el.classList.add("done");
    });
}

function activateStep(i) { if (i < STEPS.length) document.getElementById(`step-${STEPS[i]}`).classList.add("active"); }
function completeStep(i) { if (i < STEPS.length) { const el = document.getElementById(`step-${STEPS[i]}`); el.classList.remove("active"); el.classList.add("done"); } }

// ══════════════════════════════════════════════════════
//  SUBMIT RESEARCH
// ══════════════════════════════════════════════════════

let isResearching = false;

async function submitResearch(event) {
    event.preventDefault();
    if (isResearching) return; // Prevent duplicate submissions

    const input = document.getElementById("query-input");
    const query = input.value.trim();
    if (!query) return;

    isResearching = true;

    document.getElementById("loading-query").textContent = `"${query}"`;
    showView("loading");
    startPipelineAnimation();

    try {
        const response = await fetch(`${API_BASE}/research`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query }),
        });

        stopPipelineAnimation();

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `Server error: ${response.status}`);
        }

        const report = await response.json();

        // Save to library
        saveReport(report);

        renderReport(report);
        showView("results");
    } catch (error) {
        stopPipelineAnimation();
        document.getElementById("error-message").textContent = error.message || "An unexpected error occurred.";
        showView("error");
    } finally {
        isResearching = false;
    }
}

// ══════════════════════════════════════════════════════
//  RENDER REPORT
// ══════════════════════════════════════════════════════

function renderReport(report) {
    document.getElementById("report-title").textContent = report.title || "Research Report";
    document.getElementById("report-query").textContent = `Query: ${report.query}`;

    const totalTime = report.agent_trace
        ? report.agent_trace.reduce((s, t) => s + (t.duration_seconds || 0), 0).toFixed(1) : "N/A";
    document.getElementById("results-time").textContent = `⏱ ${totalTime}s total`;
    document.getElementById("results-sources").textContent = `📚 ${report.sources?.length || 0} sources`;

    // Agent trace
    const tc = document.getElementById("trace-items");
    tc.innerHTML = (report.agent_trace || []).map((t) => {
        const ok = t.status === "success";
        return `<div class="trace-item"><div class="trace-name">${t.agent}</div><div class="trace-time">${t.duration_seconds?.toFixed(1) || "?"}</div><div class="trace-unit">seconds</div><div class="trace-status ${ok ? "success" : "error"}">${ok ? "✓ Success" : "✗ Failed"}</div></div>`;
    }).join("");

    // Summary
    document.getElementById("report-summary").textContent = report.summary || "No summary available.";

    // Findings
    const fc = document.getElementById("report-findings");
    fc.innerHTML = (report.key_findings?.length)
        ? report.key_findings.map((f) => `<div class="finding-card"><h4>${escapeHtml(f.finding || f.claim || "Finding")}</h4><p>${escapeHtml(f.details || f.evidence || "")}</p></div>`).join("")
        : '<p class="report-text">No findings extracted.</p>';

    // Methodology
    document.getElementById("report-methodology").textContent = report.methodology_overview || "N/A";

    // Fact checks
    const fcc = document.getElementById("report-factchecks");
    fcc.innerHTML = (report.fact_check_results?.length)
        ? report.fact_check_results.map((fc) => {
            const conf = Math.round((fc.confidence || 0) * 100);
            return `<div class="factcheck-card"><div class="factcheck-claim">${escapeHtml(fc.claim)}</div><div class="factcheck-meta"><span class="factcheck-badge badge-support">✓ ${fc.supporting_sources?.length || 0} supporting</span><span class="factcheck-badge badge-contradict">✗ ${fc.contradicting_sources?.length || 0} contradicting</span><span class="factcheck-badge badge-confidence">${conf}% confidence</span></div><div class="factcheck-nuance">${escapeHtml(fc.nuance || "")}</div></div>`;
        }).join("")
        : '<p class="report-text">No fact-check results.</p>';

    // Gaps
    const gc = document.getElementById("report-gaps");
    gc.innerHTML = (report.research_gaps?.length)
        ? report.research_gaps.map((g) => `<div class="gap-item"><div class="gap-bullet"></div><span>${escapeHtml(g)}</span></div>`).join("")
        : '<p class="report-text">No research gaps identified.</p>';

    // Sources
    const sc = document.getElementById("report-sources");
    sc.innerHTML = (report.sources?.length)
        ? report.sources.map((s, i) => `<div class="source-item"><div class="source-num">${i + 1}</div><div class="source-info"><div class="source-title">${escapeHtml(s.title || "Untitled")}</div><a class="source-url" href="${escapeHtml(s.url || "#")}" target="_blank" rel="noopener">${escapeHtml(s.url || "")}</a></div></div>`).join("")
        : '<p class="report-text">No sources recorded.</p>';
}

// ══════════════════════════════════════════════════════
//  UTILITY
// ══════════════════════════════════════════════════════

function escapeHtml(text) {
    if (!text) return "";
    const d = document.createElement("div");
    d.textContent = text;
    return d.innerHTML;
}

// ══════════════════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    checkReturningUser();
    updateGreeting();
    updateLibraryCount();
});
