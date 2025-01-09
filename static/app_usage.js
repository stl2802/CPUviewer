let chart;
function fetchAppData() {
  fetch('/app_usage_data')
      .then(response => {
          if(!response.ok){
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json()
        })
      .then(data => {
        if (!data || data.length === 0) {
           console.error("Нет данных для построения графика.");
           return;
         }
         console.log("Data from /app_usage_data:", data);
        const timestamps = data.map(item => new Date(item.timestamp).toLocaleTimeString());
        const appNames = data.map(item => item.app_name);
        const durations = data.map(item => item.duration);


        const ctx = document.getElementById('appChart').getContext('2d');
        if (chart) {
            chart.destroy();
        }
        chart = new Chart(ctx, {
            type: 'bar',
            data: {
               labels: appNames,
                datasets: [{
                   label: 'Длительность использования (сек)',
                    data: durations,
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                   borderWidth: 1
                }]
            },
           options: {
               scales: {
                   y: {
                        beginAtZero: true,
                         title: {
                              display: true,
                              text: 'Длительность использования (сек)'
                           }
                    }
                }
            }
        });
    })
    .catch(error => {
        console.error('Ошибка при получении данных:', error);
    });
}

fetchAppData();