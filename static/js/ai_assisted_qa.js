const AI_REPORT_INDEX_ENDPOINT = "/api/ai-reports";
const TRUSTED_PULL_REQUEST_PATTERN = /^\/dastan96\/Flask-Login-Tester\/pull\/([1-9]\d*)$/;
const SUMMARY_PREVIEW_LENGTH = 320;
const INITIAL_CHANGED_FILE_COUNT = 5;

let selectedChangedFiles = [];
let showAllChangedFiles = false;

document.addEventListener("DOMContentLoaded", () => {
    const reportSelect = document.getElementById("aiReportSelect");

    if (!reportSelect) {
        return;
    }

    setupTabs();
    setupExpandableControls();
    reportSelect.addEventListener("change", () => {
        const prNumber = Number(reportSelect.value);
        if (Number.isInteger(prNumber) && prNumber > 0) {
            loadReport(prNumber);
        }
    });
    loadReportIndex();
});

async function loadReportIndex() {
    showLoading("Retrieving the latest persisted QA report...");

    try {
        const index = await fetchApiData(AI_REPORT_INDEX_ENDPOINT);
        const reports = Array.isArray(index.reports)
            ? index.reports.filter(report => Number.isInteger(report.pr_number) && report.pr_number > 0)
            : [];

        if (reports.length === 0) {
            showUnavailable("AI reports are not available yet.", true);
            return;
        }

        populateReportSelect(reports);
        await loadReport(reports[0].pr_number);
    } catch (_error) {
        showUnavailable("AI reports are not available yet.", true);
    }
}

async function loadReport(prNumber) {
    showLoading("Loading the selected Pull Request analysis...");

    try {
        const report = await fetchApiData(`/api/ai-reports/${prNumber}`);
        renderReport(report, prNumber);
    } catch (_error) {
        showUnavailable("This AI analysis is temporarily unavailable.", false);
    }
}

async function fetchApiData(url) {
    const response = await fetch(url, {headers: {"Accept": "application/json"}});
    let payload;

    try {
        payload = await response.json();
    } catch (_error) {
        throw new Error("Invalid API response");
    }

    if (!response.ok || !payload || payload.available !== true || !isObject(payload.data)) {
        throw new Error("Report data unavailable");
    }

    return payload.data;
}

function populateReportSelect(reports) {
    const reportSelect = document.getElementById("aiReportSelect");
    reportSelect.replaceChildren();

    reports.forEach(report => {
        const option = document.createElement("option");
        option.value = String(report.pr_number);
        option.textContent = `PR #${report.pr_number} — ${displayText(report.title, "Untitled Pull Request")}`;
        reportSelect.appendChild(option);
    });

    reportSelect.value = String(reports[0].pr_number);
    reportSelect.disabled = false;
}

function renderReport(report, requestedPrNumber) {
    if (!isObject(report.source) || !isObject(report.change_summary) || !isObject(report.analysis)) {
        throw new Error("Malformed report");
    }

    const source = report.source;
    const summary = report.change_summary;
    const analysis = report.analysis;
    const prNumber = source.pr_number;

    if (!Number.isInteger(prNumber) || prNumber !== requestedPrNumber) {
        throw new Error("Mismatched report");
    }

    setText("aiPrNumber", `Pull Request #${prNumber}`);
    setText("aiReportTitle", source.pr_title, "Untitled Pull Request");
    setText("aiMergedSummary", source.merged_at ? `Merged ${formatTimestamp(source.merged_at)}` : "Merge date unavailable");
    setText("aiCommitSummary", shortCommit(source.commit_sha));
    renderRiskBadge(analysis.risk_level);
    renderMetric("aiFilesChanged", summary.files_changed);
    renderMetric("aiAdditions", summary.additions, "+");
    renderMetric("aiDeletions", summary.deletions, "-");
    renderMetric("aiTotalChanges", summary.total_changes);

    renderSummary(analysis.change_summary);
    renderKeyFindings(analysis);
    renderChangedFiles(report.changed_files);
    renderAffectedAreas(analysis.affected_areas);
    renderCoverageGaps(analysis.coverage_gaps);
    renderExistingCoverage(analysis.relevant_existing_tests);
    renderRecommendations(analysis.recommended_tests);
    renderDetails(report, analysis, source, prNumber);
    configureReportLinks(source.github_url, prNumber);
    activateTab("overview");

    document.getElementById("aiReportLoading").classList.add("d-none");
    document.getElementById("aiReportUnavailable").classList.add("d-none");
    const content = document.getElementById("aiReportContent");
    content.classList.remove("d-none");
    content.setAttribute("aria-busy", "false");
    document.getElementById("aiReportSelect").disabled = false;
    setText("aiReportUpdateStatus", `Loaded AI-assisted QA analysis for Pull Request ${prNumber}.`);
}

function setupTabs() {
    const tabs = Array.from(document.querySelectorAll("[data-report-tab]"));

    tabs.forEach((tab, index) => {
        tab.addEventListener("click", () => activateTab(tab.dataset.reportTab, true));
        tab.addEventListener("keydown", event => {
            let nextIndex;
            if (event.key === "ArrowRight") {
                nextIndex = (index + 1) % tabs.length;
            } else if (event.key === "ArrowLeft") {
                nextIndex = (index - 1 + tabs.length) % tabs.length;
            } else if (event.key === "Home") {
                nextIndex = 0;
            } else if (event.key === "End") {
                nextIndex = tabs.length - 1;
            } else {
                return;
            }

            event.preventDefault();
            activateTab(tabs[nextIndex].dataset.reportTab, true);
        });
    });
}

function activateTab(tabName, moveFocus = false) {
    document.querySelectorAll("[data-report-tab]").forEach(tab => {
        const isActive = tab.dataset.reportTab === tabName;
        tab.classList.toggle("active", isActive);
        tab.setAttribute("aria-selected", String(isActive));
        tab.tabIndex = isActive ? 0 : -1;
        if (isActive && moveFocus) {
            tab.focus();
        }
    });

    document.querySelectorAll("[data-report-panel]").forEach(panel => {
        panel.hidden = panel.dataset.reportPanel !== tabName;
    });
}

function setupExpandableControls() {
    document.getElementById("aiSummaryToggle").addEventListener("click", toggleSummary);
    document.getElementById("aiChangedFilesToggle").addEventListener("click", () => {
        showAllChangedFiles = !showAllChangedFiles;
        renderChangedFileRows();
    });
}

function renderSummary(value) {
    const summary = document.getElementById("aiChangeSummary");
    const toggle = document.getElementById("aiSummaryToggle");
    const text = displayText(value);
    summary.textContent = text;
    const isLong = text.length > SUMMARY_PREVIEW_LENGTH;
    summary.classList.toggle("summary-collapsed", isLong);
    toggle.classList.toggle("d-none", !isLong);
    toggle.setAttribute("aria-expanded", "false");
    toggle.textContent = "Show more";
}

function toggleSummary() {
    const summary = document.getElementById("aiChangeSummary");
    const toggle = document.getElementById("aiSummaryToggle");
    const isExpanded = toggle.getAttribute("aria-expanded") === "true";
    toggle.setAttribute("aria-expanded", String(!isExpanded));
    toggle.textContent = isExpanded ? "Show more" : "Show less";
    summary.classList.toggle("summary-collapsed", isExpanded);
}

function renderKeyFindings(analysis) {
    const container = document.getElementById("aiKeyFindings");
    const gaps = asArray(analysis.coverage_gaps).map(item => ({
        label: "Coverage Gap",
        level: "review",
        title: displayText(item.area, "Unspecified coverage area"),
        detail: displayText(item.reason),
    }));
    const recommendations = asArray(analysis.recommended_tests)
        .filter(item => item.priority === "high" || item.priority === "medium")
        .sort((left, right) => priorityRank(left.priority) - priorityRank(right.priority))
        .map(item => ({
            label: "Suggested Test",
            level: item.priority,
            title: `${displayText(item.test_type, "Other").toUpperCase()} — ${displayText(item.title, "Untitled recommendation")}`,
            detail: displayText(item.rationale),
        }));
    const affectedAreas = asArray(analysis.affected_areas).map(item => ({
        label: "Affected Area",
        level: "info",
        title: displayText(item.area, "Unspecified area"),
        detail: displayText(item.evidence),
    }));
    const findings = [...gaps, ...recommendations, ...affectedAreas].slice(0, 3);

    container.replaceChildren();
    if (findings.length === 0) {
        appendEmptyState(container, "No key review finding was identified from the supplied evidence.");
        return;
    }

    findings.forEach(finding => {
        container.appendChild(createReviewRow(finding.label, finding.title, finding.detail, finding.level));
    });
}

function renderChangedFiles(changedFiles) {
    selectedChangedFiles = Array.isArray(changedFiles) ? changedFiles : [];
    showAllChangedFiles = false;
    renderChangedFileRows(Array.isArray(changedFiles));
}

function renderChangedFileRows(hasChangedFileMetadata = true) {
    const container = document.getElementById("aiChangedFiles");
    const toggle = document.getElementById("aiChangedFilesToggle");
    container.replaceChildren();

    if (!hasChangedFileMetadata) {
        appendEmptyState(container, "Per-file change details are not available for this older report.");
        toggle.classList.add("d-none");
        return;
    }

    if (selectedChangedFiles.length === 0) {
        appendEmptyState(container, "No changed files were recorded for this report.");
        toggle.classList.add("d-none");
        return;
    }

    const visibleFiles = showAllChangedFiles
        ? selectedChangedFiles
        : selectedChangedFiles.slice(0, INITIAL_CHANGED_FILE_COUNT);

    visibleFiles.forEach(file => {
        const row = document.createElement("div");
        row.className = "changed-file-row";
        const identity = document.createElement("div");
        identity.className = "changed-file-identity";
        const filename = document.createElement("code");
        filename.textContent = displayText(file.filename, "Unknown file");
        const status = document.createElement("span");
        status.className = "changed-file-status";
        status.textContent = displayText(file.status, "changed");
        identity.append(filename, status);

        const stats = document.createElement("div");
        stats.className = "changed-file-stats";
        const additions = document.createElement("span");
        additions.className = "text-success";
        additions.textContent = `+${safeCount(file.additions)}`;
        const deletions = document.createElement("span");
        deletions.className = "text-danger";
        deletions.textContent = `-${safeCount(file.deletions)}`;
        stats.append(additions, deletions);
        row.append(identity, stats);
        container.appendChild(row);
    });

    const canExpand = selectedChangedFiles.length > INITIAL_CHANGED_FILE_COUNT;
    toggle.classList.toggle("d-none", !canExpand);
    toggle.setAttribute("aria-expanded", String(showAllChangedFiles));
    toggle.textContent = showAllChangedFiles
        ? `Show first ${INITIAL_CHANGED_FILE_COUNT} files`
        : `Show all ${selectedChangedFiles.length} files`;
}

function renderAffectedAreas(items) {
    const container = document.getElementById("aiAffectedAreas");
    container.replaceChildren();
    const values = asArray(items);

    if (values.length === 0) {
        appendEmptyState(container, "No specific affected area was identified from the supplied evidence.");
        return;
    }

    values.forEach(item => {
        container.appendChild(createReviewRow("Affected Area", item.area, item.evidence, "info"));
    });
}

function renderCoverageGaps(items) {
    const container = document.getElementById("aiCoverageGaps");
    container.replaceChildren();
    const values = asArray(items);

    if (values.length === 0) {
        appendEmptyState(container, "No specific coverage gap was identified from the supplied evidence.");
        return;
    }

    values.forEach(item => {
        container.appendChild(createReviewRow("Potential Coverage Gap", item.area, item.reason, "review"));
    });
}

function renderExistingCoverage(items) {
    const container = document.getElementById("aiExistingCoverage");
    container.replaceChildren();
    const values = asArray(items);

    if (values.length === 0) {
        appendEmptyState(container, "No directly relevant existing automated test was identified.");
        return;
    }

    values.forEach(item => {
        const row = document.createElement("article");
        row.className = "test-impact-row";
        if (typeof item.test_id === "string" && item.test_id.trim()) {
            const testId = document.createElement("span");
            testId.className = "ai-test-id";
            testId.textContent = item.test_id;
            row.appendChild(testId);
        }
        const content = document.createElement("div");
        const label = document.createElement("span");
        label.className = "review-item-label";
        label.textContent = "Existing Coverage";
        const title = document.createElement("h3");
        title.textContent = displayText(item.title, "Untitled test");
        const reason = document.createElement("p");
        reason.textContent = displayText(item.reason);
        content.append(label, title, reason);
        row.appendChild(content);
        container.appendChild(row);
    });
}

function renderRecommendations(items) {
    const container = document.getElementById("aiRecommendations");
    container.replaceChildren();
    const values = asArray(items);

    if (values.length === 0) {
        appendEmptyState(container, "No additional test was recommended from the supplied evidence.");
        return;
    }

    values.forEach(item => {
        const row = document.createElement("article");
        row.className = "test-impact-row recommendation-row";
        const badge = document.createElement("span");
        const priority = ["high", "medium", "low"].includes(item.priority) ? item.priority : "unknown";
        badge.className = `ai-priority-badge ai-priority-${priority}`;
        badge.textContent = `${priority.toUpperCase()} · ${displayText(item.test_type, "other").toUpperCase()}`;
        const content = document.createElement("div");
        const label = document.createElement("span");
        label.className = "review-item-label";
        label.textContent = "Recommended Test";
        const title = document.createElement("h3");
        title.textContent = displayText(item.title, "Untitled recommendation");
        const rationale = document.createElement("p");
        rationale.textContent = displayText(item.rationale);
        content.append(label, title, rationale);
        row.append(badge, content);
        container.appendChild(row);
    });
}

function renderDetails(report, analysis, source, prNumber) {
    setText("aiRiskRationale", analysis.risk_rationale);
    renderTextList("aiNotes", analysis.qa_notes, "No additional QA notes were recorded.");
    renderTextList(
        "aiLimitations",
        analysis.analysis_limitations,
        "No explicit limitations were recorded. Human review is still required."
    );
    setText("aiModel", report.model);
    setText("aiPromptVersion", report.prompt_version);
    setText("aiReportVersion", report.report_version);
    setText("aiGeneratedAt", formatTimestamp(report.generated_at));
    setText("aiMergedAt", source.merged_at ? formatTimestamp(source.merged_at) : "Not available");
    setText("aiCommitSha", source.commit_sha);
    document.getElementById("aiCommitSha").title = displayText(source.commit_sha);
    setText("aiMetadataPrNumber", `#${prNumber}`);
}

function createReviewRow(labelText, titleText, detailText, level) {
    const row = document.createElement("article");
    row.className = "review-row";
    const label = document.createElement("span");
    label.className = `review-finding-badge review-finding-${level}`;
    label.textContent = labelText;
    const content = document.createElement("div");
    const title = document.createElement("h3");
    title.textContent = displayText(titleText, "Unspecified finding");
    const detail = document.createElement("p");
    detail.textContent = displayText(detailText);
    content.append(title, detail);
    row.append(label, content);
    return row;
}

function renderTextList(elementId, items, emptyMessage) {
    const list = document.getElementById(elementId);
    list.replaceChildren();
    const values = asArray(items).filter(item => typeof item === "string" && item.trim());

    if (values.length === 0) {
        const item = document.createElement("li");
        item.className = "ai-empty-item";
        item.textContent = emptyMessage;
        list.appendChild(item);
        return;
    }

    values.forEach(value => {
        const item = document.createElement("li");
        item.textContent = value;
        list.appendChild(item);
    });
}

function configureReportLinks(value, prNumber) {
    const trustedUrl = trustedPullRequestUrl(value, prNumber);
    const externalLinks = [
        document.getElementById("aiPullRequestLink"),
        document.getElementById("aiDetailsPrLink"),
        document.getElementById("aiFullDiffLink"),
    ];

    externalLinks.forEach(link => {
        if (!trustedUrl) {
            link.removeAttribute("href");
            link.classList.add("d-none");
            return;
        }
        link.href = trustedUrl;
        link.setAttribute("aria-label", `View Pull Request ${prNumber} on GitHub`);
        link.classList.remove("d-none");
    });

    const rawLinks = [
        document.getElementById("aiRawReportLink"),
        document.getElementById("aiDetailsRawLink"),
    ];
    rawLinks.forEach(link => {
        link.href = `/api/ai-reports/${prNumber}`;
        link.setAttribute("aria-label", `View raw AI-assisted QA report for Pull Request ${prNumber}`);
    });
}

function trustedPullRequestUrl(value, prNumber) {
    if (typeof value !== "string") {
        return null;
    }

    try {
        const url = new URL(value);
        const match = TRUSTED_PULL_REQUEST_PATTERN.exec(url.pathname);
        if (
            url.protocol !== "https:" ||
            url.hostname !== "github.com" ||
            url.username ||
            url.password ||
            url.search ||
            url.hash ||
            !match ||
            Number(match[1]) !== prNumber
        ) {
            return null;
        }
        return url.href;
    } catch (_error) {
        return null;
    }
}

function showLoading(message) {
    setText("aiLoadingMessage", message);
    document.getElementById("aiReportLoading").classList.remove("d-none");
    document.getElementById("aiReportUnavailable").classList.add("d-none");
    const content = document.getElementById("aiReportContent");
    content.classList.add("d-none");
    content.setAttribute("aria-busy", "true");
    document.getElementById("aiReportSelect").disabled = true;
}

function showUnavailable(message, clearSelector) {
    document.getElementById("aiReportLoading").classList.add("d-none");
    document.getElementById("aiReportContent").classList.add("d-none");
    setText("aiUnavailableMessage", message);
    document.getElementById("aiReportUnavailable").classList.remove("d-none");

    const reportSelect = document.getElementById("aiReportSelect");
    if (clearSelector) {
        const option = document.createElement("option");
        option.textContent = "No reports available";
        reportSelect.replaceChildren(option);
        reportSelect.disabled = true;
    } else {
        reportSelect.disabled = false;
    }
}

function renderRiskBadge(riskLevel) {
    const risk = ["low", "medium", "high"].includes(riskLevel) ? riskLevel : "unknown";
    const badge = document.getElementById("aiRiskBadge");
    badge.className = `ai-risk-badge ai-risk-${risk}`;
    badge.textContent = `${risk.toUpperCase()} RISK`;
}

function renderMetric(elementId, value, prefix = "") {
    setText(elementId, `${prefix}${safeCount(value)}`);
}

function appendEmptyState(container, message) {
    const empty = document.createElement("p");
    empty.className = "ai-empty-state";
    empty.textContent = message;
    container.appendChild(empty);
}

function formatTimestamp(value) {
    if (typeof value !== "string" || !value.trim()) {
        return "Not available";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }
    return new Intl.DateTimeFormat(undefined, {dateStyle: "medium", timeStyle: "short"}).format(date);
}

function shortCommit(value) {
    const commit = displayText(value);
    return commit === "Not available" ? commit : commit.slice(0, 7);
}

function priorityRank(priority) {
    return priority === "high" ? 0 : priority === "medium" ? 1 : 2;
}

function safeCount(value) {
    return Number.isInteger(value) && value >= 0 ? value : 0;
}

function asArray(value) {
    return Array.isArray(value) ? value : [];
}

function setText(elementId, value, fallback = "Not available") {
    document.getElementById(elementId).textContent = displayText(value, fallback);
}

function displayText(value, fallback = "Not available") {
    return typeof value === "string" && value.trim() ? value : fallback;
}

function isObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}
