// history_dashboard.js

document.addEventListener('DOMContentLoaded', () => {
  fetch('/history')
    .then(response => response.json())
    .then(data => {
      // data.runs is an array of objects like:
      // { run_id: "20250301-020001", total: 5, passed: 5, date: "2025-03-01 02:00:01" }
      const runs = data.runs;

      // Extract labels (e.g., run dates), pass counts, and fail counts
      const labels = runs.map(run => run.date);
      const passCounts = runs.map(run => run.passed);
      const failCounts = runs.map(run => run.total - run.passed);

      // Prepare the chart
      const ctx = document.getElementById('historyChart').getContext('2d');
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Passed',
              data: passCounts,
              backgroundColor: '#4CAF50', // green
              borderRadius: 6,
              borderSkipped: false
            },
            {
              label: 'Failed',
              data: failCounts,
              backgroundColor: '#F44336', // red
              borderRadius: 6,
              borderSkipped: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: {
            duration: 2000,
            easing: 'easeInOutQuart'
          },
          scales: {
            x: {
              stacked: true,
              title: { display: true, text: 'Test Run Date' },
              ticks: {
                color: '#333',
                font: { size: 14 }
              },
              grid: { display: false }
            },
            y: {
              stacked: true,
              beginAtZero: true,
              title: { display: true, text: 'Number of Tests' },
              ticks: {
                color: '#333',
                font: { size: 14 }
              },
              grid: {
                color: '#ccc',
                borderDash: [2, 2]
              }
            }
          },
          plugins: {
            title: {
              display: true,
              text: 'Historical Test Results (Pass/Fail)',
              color: '#333',
              font: { size: 18 }
            },
            legend: {
              display: true,
              position: 'bottom'
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  // Example: "Passed: 3" or "Failed: 2"
                  return `${context.dataset.label}: ${context.parsed.y}`;
                }
              }
            }
          }
        }
      });
    })
    .catch(error => console.error("Error fetching run history:", error));
});
