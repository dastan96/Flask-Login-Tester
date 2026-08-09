document.addEventListener('DOMContentLoaded', () => {
  const state = {
    chart: null,
    tests: [],
    showAllTests: false,
  };

  const DEFAULT_VISIBLE_TESTS = 5;
  const SUITE_CATEGORIES = [
    { name: 'Login API', aliases: ['Login API'] },
    { name: 'UI Tests', aliases: ['UI Tests'] },
    { name: 'Web Routes', aliases: ['Web Routes'] },
  ];

  const elements = {
    loading: document.getElementById('dashboardLoading'),
    unavailable: document.getElementById('dashboardUnavailable'),
    content: document.getElementById('dashboardContent'),
    metadata: document.getElementById('dashboardMetadata'),
    links: document.getElementById('dashboardLinks'),
    summaryStatus: document.getElementById('summaryStatus'),
    summaryTotal: document.getElementById('summaryTotal'),
    summaryPassed: document.getElementById('summaryPassed'),
    summaryFailed: document.getElementById('summaryFailed'),
    summarySkipped: document.getElementById('summarySkipped'),
    summaryDuration: document.getElementById('summaryDuration'),
    suiteSummaries: document.getElementById('suiteSummaries'),
    emptySuitesMessage: document.getElementById('emptySuitesMessage'),
    testResultsBody: document.getElementById('testResultsBody'),
    emptyTestsMessage: document.getElementById('emptyTestsMessage'),
    testCasesToggle: document.getElementById('testCasesToggle'),
    chartCanvas: document.getElementById('testChart'),
  };

  function show(element) {
    if (element) {
      element.classList.remove('d-none');
    }
  }

  function hide(element) {
    if (element) {
      element.classList.add('d-none');
    }
  }

  function setText(element, value) {
    if (element) {
      element.textContent = value;
    }
  }

  function formatStatus(status) {
    if (!status) {
      return 'Unknown';
    }
    return `${status.charAt(0).toUpperCase()}${status.slice(1)}`;
  }

  function formatDuration(duration) {
    if (typeof duration !== 'number') {
      return 'Unavailable';
    }
    return `${duration.toFixed(3)}s`;
  }

  function formatCompletedAt(value) {
    if (!value) {
      return 'Unavailable';
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleString();
  }

  function shortCommit(sha) {
    if (!sha) {
      return 'Unavailable';
    }
    return sha.slice(0, 7);
  }

  function statusClass(status) {
    if (status === 'passed') {
      return 'text-success';
    }
    if (status === 'failed') {
      return 'text-danger';
    }
    return 'text-warning';
  }

  function clearElement(element) {
    if (element) {
      element.textContent = '';
    }
  }

  function clearChart() {
    if (state.chart) {
      state.chart.destroy();
      state.chart = null;
    }
  }

  function renderChart(data) {
    clearChart();
    if (!elements.chartCanvas || typeof Chart === 'undefined') {
      return;
    }

    state.chart = new Chart(elements.chartCanvas.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: ['Passed', 'Failed', 'Skipped'],
        datasets: [{
          label: 'Test Results',
          data: [data.passed, data.failed, data.skipped],
          backgroundColor: ['#A8D5BA', '#F5A5A5', '#FFE599'],
          borderColor: ['#ffffff', '#ffffff', '#ffffff'],
          borderWidth: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'bottom',
            labels: { font: { size: 16 } },
          },
        },
        cutout: '50%',
      },
    });
  }

  function createLink(href, label) {
    const link = document.createElement('a');
    link.className = 'btn btn-outline-primary btn-sm';
    link.href = href;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = label;
    return link;
  }

  function isWorkflowRunUrl(value) {
    return typeof value === 'string'
      && value.startsWith('https://github.com/dastan96/Flask-Login-Tester/actions/');
  }

  function renderLinks(payload, data) {
    clearElement(elements.links);
    if (isWorkflowRunUrl(data.workflow_run_url)) {
      elements.links.appendChild(createLink(data.workflow_run_url, 'Workflow Run'));
    }
    if (payload.results_page_url) {
      elements.links.appendChild(createLink(payload.results_page_url, 'Public Results Page'));
    }
  }

  function renderSummary(data) {
    setText(elements.summaryStatus, formatStatus(data.status));
    elements.summaryStatus.className = `fs-4 fw-bold ${statusClass(data.status)}`;
    setText(elements.summaryTotal, data.total);
    setText(elements.summaryPassed, data.passed);
    setText(elements.summaryFailed, data.failed);
    setText(elements.summarySkipped, data.skipped);
    setText(elements.summaryDuration, formatDuration(data.duration));

    const metadata = [
      `Completed ${formatCompletedAt(data.completed_at)}`,
      `Branch ${data.branch || 'Unavailable'}`,
      `Commit ${shortCommit(data.commit_sha)}`,
    ];
    setText(elements.metadata, metadata.join(' | '));
  }

  function renderSuites(suites) {
    clearElement(elements.suiteSummaries);
    hide(elements.emptySuitesMessage);

    if (!Array.isArray(suites)) {
      suites = [];
    }

    const suitesByName = new Map(suites.map((suite) => [suite.name, suite]));
    const orderedSuites = SUITE_CATEGORIES.map((category) => ({
      category,
      suite: category.aliases.map((name) => suitesByName.get(name)).find(Boolean),
    }));

    if (!orderedSuites.length) {
      show(elements.emptySuitesMessage);
      return;
    }

    orderedSuites.forEach(({ category, suite }) => {
      const col = document.createElement('div');
      col.className = 'col-12';

      const card = document.createElement('div');
      card.className = 'border rounded p-3 h-100';

      const title = document.createElement('div');
      title.className = 'fw-bold';
      title.textContent = category.name;

      card.appendChild(title);

      if (!suite) {
        const unavailable = document.createElement('div');
        unavailable.className = 'text-muted small mt-1';
        unavailable.textContent = 'No results in latest run';
        card.appendChild(unavailable);
        col.appendChild(card);
        elements.suiteSummaries.appendChild(col);
        return;
      }

      const status = document.createElement('div');
      status.className = statusClass(suite.status);
      status.textContent = formatStatus(suite.status);

      const counts = document.createElement('div');
      counts.className = 'text-muted small';
      counts.textContent = `${suite.passed}/${suite.total} passed, ${suite.failed} failed, ${suite.skipped} skipped`;

      const duration = document.createElement('div');
      duration.className = 'text-muted small';
      duration.textContent = formatDuration(suite.duration);

      card.appendChild(status);
      card.appendChild(counts);
      card.appendChild(duration);
      col.appendChild(card);
      elements.suiteSummaries.appendChild(col);
    });
  }

  function appendCell(row, value) {
    const cell = document.createElement('td');
    cell.textContent = value;
    row.appendChild(cell);
  }

  function updateTestCasesToggle(total) {
    if (!elements.testCasesToggle) {
      return;
    }

    if (total <= DEFAULT_VISIBLE_TESTS) {
      hide(elements.testCasesToggle);
      elements.testCasesToggle.setAttribute('aria-expanded', 'false');
      return;
    }

    show(elements.testCasesToggle);
    elements.testCasesToggle.setAttribute('aria-expanded', state.showAllTests ? 'true' : 'false');
    elements.testCasesToggle.textContent = state.showAllTests
      ? 'Show Less ^'
      : 'Show More v';
  }

  function renderTests(tests) {
    clearElement(elements.testResultsBody);
    state.tests = Array.isArray(tests) ? tests : [];

    if (!state.tests.length) {
      show(elements.emptyTestsMessage);
      updateTestCasesToggle(0);
      return;
    }

    hide(elements.emptyTestsMessage);
    const visibleTests = state.showAllTests
      ? state.tests
      : state.tests.slice(0, DEFAULT_VISIBLE_TESTS);

    visibleTests.forEach((test) => {
      const row = document.createElement('tr');
      appendCell(row, test.id || '');
      appendCell(row, test.name);
      appendCell(row, test.suite);

      const statusCell = document.createElement('td');
      statusCell.className = statusClass(test.status);
      statusCell.textContent = formatStatus(test.status);
      row.appendChild(statusCell);

      appendCell(row, formatDuration(test.duration));
      elements.testResultsBody.appendChild(row);
    });

    updateTestCasesToggle(state.tests.length);
  }

  function renderAvailable(payload) {
    const data = payload.data;
    hide(elements.loading);
    hide(elements.unavailable);
    show(elements.content);

    renderSummary(data);
    renderLinks(payload, data);
    renderChart(data);
    renderSuites(Array.isArray(data.suites) ? data.suites : []);
    state.showAllTests = false;
    renderTests(Array.isArray(data.tests) ? data.tests : []);
  }

  function renderUnavailable(message) {
    hide(elements.loading);
    hide(elements.content);
    clearChart();
    clearElement(elements.testResultsBody);
    state.tests = [];
    state.showAllTests = false;
    updateTestCasesToggle(0);
    show(elements.emptyTestsMessage);
    setText(elements.unavailable, message || 'Latest test results are temporarily unavailable.');
    show(elements.unavailable);
  }

  if (elements.testCasesToggle) {
    elements.testCasesToggle.addEventListener('click', () => {
      state.showAllTests = !state.showAllTests;
      renderTests(state.tests);
    });
  }

  fetch('/api/test-results/latest')
    .then((response) => response.json().then((payload) => ({ response, payload })))
    .then(({ response, payload }) => {
      if (!response.ok || !payload.available) {
        const message = payload.error && payload.error.message;
        renderUnavailable(message);
        return;
      }
      renderAvailable(payload);
    })
    .catch(() => {
      renderUnavailable('Latest test results are temporarily unavailable.');
    });
});
