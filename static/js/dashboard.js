document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('testChart');
    if (canvas) {
        fetch('/welcome?api=true')
            .then(response => response.json())
            .then(data => {
                const pendingTests = 2; // UI tests pending
                new Chart(canvas.getContext('2d'), {
                    type: 'doughnut',
                    data: {
                        labels: ['Passed', 'Failed', 'Pending'],
                        datasets: [{
                            label: 'Test Results',
                            data: [data.backend_passed, data.backend_failed, pendingTests],
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
            })
            .catch(error => console.error("Error fetching API data:", error));
    } else {
        console.error("Canvas with id 'testChart' not found.");
    }
});