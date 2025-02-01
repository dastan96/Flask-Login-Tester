document.addEventListener('DOMContentLoaded', function() {
    console.log("Dashboard.js is loaded");
    const canvas = document.getElementById('testChart');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Passed', 'Failed'],
                datasets: [{
                    label: 'Test Results',
                    data: [5, 1],
                    backgroundColor: ['#A8D5BA', '#F5A5A5'],
                    borderColor: ['#ffffff', '#ffffff'],
                    borderWidth: 2,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            font: {
                                size: 14
                            }
                        }
                    }
                },
                cutout: '50%',
            }
        });
    } else {
        console.error("Canvas with id 'testChart' not found.");
    }
});