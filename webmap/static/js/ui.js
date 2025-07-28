// First, select the parent div by its ID
const container = document.getElementById('layer_select_btn');

// Then, select only buttons with the class 'data-layer-btn' inside this container
const buttons = container.querySelectorAll('.data-layer-btn');

// Attach event listeners to each button
buttons.forEach(button => {
    button.addEventListener('click', () => {
        const value = button.getAttribute('data-value');
        handleLayerSelection(value);
    });
});

let loadChart = null;


// The function that handles the click event
function handleLayerSelection(value) {
    updateChoropleth(webmap_layers, value);
}

function closeRightPanel() {
    const panel = document.getElementById('rightPanel');
    if (panel.classList.contains('w-[500px]')) {
        panel.classList.remove('w-[500px]');
        panel.classList.add('w-0', 'overflow-hidden');
    }
};

function openRightPanel() {
    const panel = document.getElementById('rightPanel');
    if (panel.classList.contains('w-0')) {
        panel.classList.remove('w-0', 'overflow-hidden');
        panel.classList.add('w-[500px]');
    }
};


// Right panel functionality
function showRightPanel(props) {
    const countryName = props.ISO3;

    let combinedString = null;
    if (countryName == "NGA") {
        combinedString = `('${props.level_1}', '${props.level_0}')`;
    } else {
        combinedString = `('${props.level_0}', '${props.level_1}')`;
    }

    if (combinedString) {
        const encodedSelector = encodeURIComponent(combinedString);
        // Call the FastAPI endpoint
        const baseUrl = `${window.location.protocol}//${window.location.host}`;
        fetch(`${baseUrl}/get_data/${encodedSelector}`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 404) {
                        console.log("Data not found (404).");
                    } else {
                        console.log(`Server error: ${response.status}`);
                    }
                }
                return response.json();
            })
            .then(ts_data => {
                console.log("Response from FastAPI with data", ts_data);
                function generateXfromY(yArray) {
                    const xArray = [];

                    for (let i = 0; i < yArray.length; i++) {
                        const hours = Math.floor(i / 60);
                        const minutes = i % 60;
                        const label = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
                        xArray.push(label);
                    }

                    return xArray;
                }

                const data = {
                    x: generateXfromY(ts_data),
                    y: ts_data
                };
                initializeChart(data);
            });
    }
    openRightPanel()
    //document.getElementById('rightPanel').style.transform = 'translateX(0)';
    // Update the content to show the selected country
    const content = document.querySelector('#rightPanel .bg-white .text-sm.text-gray-600');
    content.innerHTML = `Analyzing: <span class="font-medium text-gray-900">${countryName} ${combinedString}</span>`;
}

// Sidebar button functionality
document.addEventListener('DOMContentLoaded', function () {
    // Data layer buttons
    const dataLayerBtns = document.querySelectorAll('.data-layer-btn');
    dataLayerBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            dataLayerBtns.forEach(b => {
                b.className = 'data-layer-btn flex items-center justify-center py-6 px-4 h-auto text-sm transition-colors duration-200 border-emerald-500 bg-white text-emerald-700 hover:bg-emerald-50 hover:text-emerald-800 border rounded-md';
            });
            this.className = 'data-layer-btn flex items-center justify-center py-6 px-4 h-auto text-sm transition-colors duration-200 bg-emerald-700 text-white hover:bg-emerald-800 hover:text-white focus:bg-emerald-800 border-emerald-700 font-medium border rounded-md';
        });
    });

    // Time range buttons
    const timeRangeBtns = document.querySelectorAll('.time-range-btn');
    timeRangeBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            timeRangeBtns.forEach(b => {
                b.className = 'time-range-btn flex items-center justify-center p-3 h-auto transition-colors duration-200 bg-gray-200 text-gray-600 hover:bg-gray-300 hover:text-gray-600 border-gray-200 border rounded-md';
            });
            this.className = 'time-range-btn flex items-center justify-center p-3 h-auto transition-colors duration-200 bg-gray-500 text-white hover:bg-gray-600 hover:text-white border-gray-500 border rounded-md';
        });
    });

    // Load type buttons
    const loadTypeBtns = document.querySelectorAll('.load-type-btn');
    loadTypeBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            loadTypeBtns.forEach(b => {
                b.className = 'load-type-btn flex items-center justify-center p-3 h-auto transition-colors duration-200 bg-gray-200 text-gray-600 hover:bg-gray-300 hover:text-gray-600 border-gray-200 border rounded-md';
            });
            this.className = 'load-type-btn flex items-center justify-center p-3 h-auto transition-colors duration-200 bg-gray-500 text-white hover:bg-gray-600 hover:text-white border-gray-500 border rounded-md';
        });
    });
});

function initializeChartGPT(data) {
    const ctx = document.getElementById('loadChart').getContext('2d');
    if (loadChart) {
        loadChart.data.labels = data.x;
        loadChart.data.datasets[0].data = data.y;
        loadChart.update();
    } else {
        loadChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.x,
                datasets: [{
                    label: 'Load',
                    data: data.y,
                    borderColor: '#059669',
                    backgroundColor: 'rgba(5, 150, 105, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'hour',
                            tooltipFormat: 'HH:mm',
                            displayFormats: {
                                hour: 'HH:mm'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Time of Day'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Load (MW)'
                        }
                    }
                },
                plugins: {
                    decimation: {
                        enabled: true,
                        algorithm: 'lttb',
                        samples: 300
                    }
                }
            }
        });
    }
}

function initializeChart(data) {
    const ctx = document.getElementById('loadChart').getContext('2d');
    if (loadChart) {
        loadChart.destroy();
    }
    loadChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.x,
            datasets: [{
                label: 'Load',
                data: data.y,
                borderColor: '#059669',
                backgroundColor: 'rgba(5, 150, 105, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Load (MW)'
                    }
                }
            }
        }
    });
}



function performGeocoding(query) {
    if (!query) return;

    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                const result = data[0];
                const lat = parseFloat(result.lat);
                const lon = parseFloat(result.lon);

                // Center and zoom your Leaflet map
                map.setView([lat, lon], 8);  // or any zoom level you prefer

                // Optional: add marker
                addTemporaryMarker(lat, lon);
            } else {
                alert("Location not found");
            }
        })
        .catch(error => {
            console.error("Geocoding error:", error);
        });
}

document.getElementById("searchInput").addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        performGeocoding(this.value);
    }
});
