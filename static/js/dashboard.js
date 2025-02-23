document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('testChart');
    const testBody = document.getElementById("apiTestBody");
  
    fetch('/welcome?api=true')
      .then(response => response.json())
      .then(data => {
        // Compute aggregate counts for the chart
        let passedCount = 0;
        let failedCount = 0;
  
        data.test_cases.forEach(test => {
          if (test.status === "Passed") {
            passedCount++;
          } else {
            failedCount++;
          }
        });
  
        const pendingTests = 2; // UI tests pending
  
        // Render the doughnut chart
        if (canvas) {
          new Chart(canvas.getContext('2d'), {
            type: 'doughnut',
            data: {
              labels: ['Passed', 'Failed', 'Pending'],
              datasets: [{
                label: 'Test Results',
                data: [passedCount, failedCount, pendingTests],
                backgroundColor: ['#A8D5BA', '#F5A5A5', '#FFE599'],
                borderColor: ['#ffffff', '#ffffff', '#ffffff'],
                borderWidth: 2
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  display: true,
                  position: 'bottom',
                  labels: { font: { size: 20 } }
                }
              },
              cutout: '50%',
            }
          });
        }
  
        // Populate the test results table dynamically
        if (testBody && data.test_cases) {
          testBody.innerHTML = ""; // Clear existing rows
  
          data.test_cases.forEach(test => {
            let resultIcon = test.status === "Passed" ? "✅" : "❌";
            // Combine test_id and test_name into one friendly string:
            const featureDisplay = `${test.test_id}: ${test.test_name}`;
            let tr = document.createElement("tr");
            tr.innerHTML = `
              <td>${featureDisplay}</td>
              <td>Under Development</td>
              <td>${test.status} ${resultIcon}</td>
              <td>${test.last_run}</td>
            `;
            testBody.appendChild(tr);
          });
        }
      })
      .catch(error => console.error("Error fetching API data:", error));
  });
  