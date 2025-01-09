function updateCPUData() {
    fetch('http://127.0.0.1:5001/current_data')
        .then(response => response.json())
        .then(data => {
            console.log(data)
            const cpuUsageElement = document.querySelector('.cpu-usage');
            const topAppElement = document.querySelector('.top-app');
            cpuUsageElement.textContent = data.cpu_usage.toFixed(2);
            topAppElement.textContent = data.top_app;
        })
        .catch(error => {
            console.error('Error fetching current CPU data:', error);
        });
}

setInterval(updateCPUData, 1000);
updateCPUData();

let chart;
const showChartBtn = document.getElementById('showChartBtn');
const cpuChart = document.getElementById('cpuChart');
const showAppUsageBtn = document.getElementById('showAppUsageBtn');
const showSystemInfoBtn = document.getElementById('showSystemInfoBtn');
const showUserActivityBtn = document.getElementById('showUserActivityBtn');



showChartBtn.addEventListener('click', () => {
    fetchChartData();
    cpuChart.style.display = 'block';
     recordUserActivity("show cpu chart");
});

showAppUsageBtn.addEventListener('click', () => {
    window.open('/app_usage', '_blank');
     recordUserActivity("open app usage window");
});
showSystemInfoBtn.addEventListener('click', () => {
  window.open('/system_info', '_blank');
   recordUserActivity("open system info window");
});
showUserActivityBtn.addEventListener('click', () => {
   window.open('/user_activity', '_blank');
    recordUserActivity("open user activity window");
});


function fetchChartData() {
    fetch('/chart_data')
        .then(response => response.json())
        .then(data => {
            if (!data || data.length === 0) {
                console.error("Нет данных для построения графика.");
                return;
            }
            const timestamps = data.map(item => new Date(item.timestamp).toLocaleTimeString());
            const cpuUsages = data.map(item => item.cpu_usage);
            const topApps = data.map(item => item.top_app);
            const ctx = document.getElementById('cpuChart').getContext('2d');
            if (chart) {
                chart.destroy();
            }
             chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: timestamps,
                    datasets: [{
                        label: 'Загрузка CPU',
                        data: cpuUsages,
                        borderColor: 'rgba(255, 99, 132, 1)',
                         borderWidth: 2,
                         pointStyle: 'circle',
                           pointRadius: 4,
                           pointHoverRadius: 7,
                       }],
                   },
                options: {
                        scales: {
                           y: {
                                beginAtZero: true,
                                title: {
                                     display: true,
                                     text: 'Загрузка (%)',
                                 }
                            }
                        },
                     plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                     if (label) {
                                        label += ': ';
                                     }
                                    label += context.formattedValue + '%';
                                     const topApp = topApps[context.dataIndex];
                                    label += '  |  Top App: ' + topApp;
                                    return label;
                                 }
                            }
                         }
                     }
                }
            });
        })
        .catch(error => {
            console.error('Ошибка при получении данных для графика:', error);
        });
}
function recordUserActivity(event_type, event_detail = "") {
     fetch('/record_user_activity', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ event_type: event_type, event_detail: event_detail }),
    })
    .catch(error => {
       console.error('Ошибка при записи активности пользователя:', error);
    });
}