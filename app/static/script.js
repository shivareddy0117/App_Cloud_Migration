function submitRequest() {
    const latitude = document.getElementById('latitude').value;
    const longitude = document.getElementById('longitude').value;
    const taxiPreference = document.getElementById('taxiPreference').value;

    const requestData = {
        user_id: "User001",  // This should be dynamically generated or retrieved
        location: {
            type: "Point",
            coordinates: [parseFloat(longitude), parseFloat(latitude)]
        },
        taxi_preference: taxiPreference
    };

    fetch('/request_taxi', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        const responseDiv = document.getElementById('response');
        responseDiv.innerHTML = `<h3>Available Taxis</h3><pre>${JSON.stringify(data, null, 2)}</pre>`;
    })
    .catch(error => {
        const responseDiv = document.getElementById('response');
        responseDiv.innerHTML = `<h3>Error</h3><pre>${error}</pre>`;
        console.error('Error:', error);
    });
}
