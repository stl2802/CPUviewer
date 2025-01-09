function fetchSystemInfo() {
  fetch('/system_info_data')
    .then(response => response.json())
    .then(data => {
      if (!data || data.length === 0) {
         console.error("Нет данных о системе.");
        return;
     }
        const latestInfo = data[data.length -1]
      document.getElementById('os-name').textContent = latestInfo.os_name;
      document.getElementById('cpu-model').textContent = latestInfo.cpu_model;
      document.getElementById('ram-total').textContent = latestInfo.ram_total.toFixed(2);
    })
    .catch(error => {
      console.error('Error fetching system info:', error);
    });
}

fetchSystemInfo();