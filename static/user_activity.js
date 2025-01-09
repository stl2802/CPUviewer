function fetchUserActivity() {
    fetch('/user_activity_data')
        .then(response => response.json())
        .then(data => {
          if (!data || data.length === 0) {
               console.error("Нет данных о действиях пользователя.");
               return;
           }
           const activityList = document.getElementById('activity-list');
            activityList.innerHTML = '';
            data.forEach(activity => {
                const listItem = document.createElement('li');
                listItem.textContent = `${new Date(activity.timestamp).toLocaleTimeString()}: ${activity.event_type} ${activity.event_detail}`;
                activityList.appendChild(listItem);
            });
        })
        .catch(error => {
            console.error('Error fetching user activity:', error);
        });
}

fetchUserActivity()