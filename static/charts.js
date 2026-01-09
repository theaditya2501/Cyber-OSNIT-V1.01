// Global Chart Instances
let radarChart = null;

// Initialize Charts
document.addEventListener('DOMContentLoaded', function() {
    initRadarChart();
});

function initRadarChart() {
    const ctx = document.getElementById('vectorsChart').getContext('2d');
    
    radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Social', 'Dev', 'Geo', 'Breach', 'Contact'],
            datasets: [{
                label: 'Target Profile',
                data: [0, 0, 0, 0, 0], // Initial Empty Data
                backgroundColor: 'rgba(0, 255, 255, 0.2)',
                borderColor: '#00ffff',
                pointBackgroundColor: '#00ffff',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#00ffff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    pointLabels: {
                        color: '#fff',
                        font: {
                            size: 11,
                            family: "'Courier New', monospace"
                        }
                    },
                    ticks: {
                        display: false, // <--- THIS REMOVES THE 20, 40, 60 NUMBERS
                        backdropColor: 'transparent'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false // Hides the "Target Profile" label box
                }
            }
        }
    });
}

// Function called by index.html when data arrives
function updateRadarGraph(stats) {
    if (!radarChart) return;

    // Map the python stats to the chart array order
    // Order: Social, Dev, Geo, Breach, Contact
    const newData = [
        stats.Social || 0,
        stats.Dev || 0,
        stats.Geo || 0,
        stats.Breach || 0,
        stats.Contact || 0
    ];

    radarChart.data.datasets[0].data = newData;
    radarChart.update();
}