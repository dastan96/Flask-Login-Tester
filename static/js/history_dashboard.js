document.addEventListener('DOMContentLoaded', () => {
    fetch('/history')
      .then(response => response.json())
      .then(data => {
        // Expecting data.runs to be an array of objects:
        // { run_id: "20250301-020001", total: 5, passed: 5, date: "2025-03-01 02:00:01" }
        const runs = data.runs;
        
        // Calculate the pass percentage for each run
        const labels = runs.map(run => run.date);  // Use the date for x-axis labels
        const passPercentages = runs.map(run => {
          return run.total ? Math.round((run.passed / run.total) * 10000) / 100 : 0;
        });
        
        // Set bar colors: green if 100%, red otherwise.
        const barColors = passPercentages.map(pct => pct === 100 ? 'green' : 'red');
        
        // Create a bar chart as a histogram
        const ctx = document.getElementById('historyChart').getContext('2d');
        new Chart(ctx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: 'Pass Percentage',
              data: passPercentages,
              backgroundColor: barColors
            }]
          },
          options: {
            responsive: true,
            scales: {
              y: {
                beginAtZero: true,
                max: 100,
                title: {
                  display: true,
                  text: 'Pass Percentage (%)'
                }
              },
              x: {
                title: {
                  display: true,
                  text: 'Test Run Date'
                }
              }
            },
            plugins: {
              legend: { display: false },
              title: {
                display: true,
                text: 'Historical Test Run Pass Percentage'
              }
            }
          }
        });
      })
      .catch(error => console.error("Error fetching run history:", error));
  });
  