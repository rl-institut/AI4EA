// Initialize map
const map = L.map('map').setView([9.082, 1.0199], 5);

// Add tile layer
let currentTileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);


const geoCoderLayer = L.layerGroup().addTo(map);

function addTemporaryMarker(lat, lon) {
    geoCoderLayer.clearLayers();
    L.marker([lat, lon]).addTo(geoCoderLayer);
}

function country_color(country_iso) {
    switch (country_iso) {
        case "NGA": return "green"
        case "GHA": return "yellow"
        case "NER": return "blue"
        case "BEN": return "blue"
        case "TGO": return "magenta"
    }
};

let currentProperty = "hh_mean";

let geojson;
let colorScale = [];

function computeThresholds(data, property, numClasses = 10) {
    //debugger;
    const values = data.features
        .map(f => f.properties[property])
        .filter(v => typeof v === 'number')
        .sort((a, b) => a - b);

    const min = values[0];
    const max = values[values.length - 1];
    const thresholds = [];

    for (let i = 1; i < numClasses; i++) {
        thresholds.push(min + ((max - min) / numClasses) * i);
    }

    return thresholds;
}

const colors = [
    '#0000ff',  // blue
    '#0033ff',
    '#0066ff',
    '#0099ff',
    '#00ccff',
    '#00ffcc',
    '#00ff66',
    '#ffff00',
    '#ff9900',
    '#ff0000'   // red
];




function getLevelName(props){
    let name = ""
    if(props.adm1 == "dummy"){
        name = props.adm1
    }
    else{
        name = `${props.adm2} (${props.adm1})`;
    }
    return name
};



function highlightFeature(e) {

    var layer = e.target;

    layer.setStyle({
        weight: 5,
        color: '#666',
        dashArray: '',
        fillOpacity: 0.7
    });

    layer.bringToFront();
}

function resetHighlight(e) {
    geojson.resetStyle(e.target);
}

const conversion_Wh = 1/60;

function highlight_state(feature, layer) {

    country = { "name": feature.properties.ISO3, "peak_demand": 23 };

    layer.on('mouseover', highlightFeature);

    layer.on('mouseout', resetHighlight);

    // Add click event to show right panel
    layer.on('click', function () {
        geoCoderLayer.clearLayers();
    });

    const buttonId = `analyse-btn-${Math.random().toString(36).substr(2, 9)}`;


    // Add popup
    const popupContent = `
    <div class="p-3 min-w-[240px] max-w-[280px]">
        <h3 class="text-base font-semibold text-gray-900 mb-2 leading-tight"> ${getLevelName(feature.properties)} ${country.name}</h3>
        <div class="border-t border-gray-200 pt-2 pb-2">
            <div class="flex justify-between items-center py-1">
                <span class="text-gray-500 text-sm">Peak max:</span>
                <span class="font-bold text-gray-900 ml-2 text-sm">${(feature.properties.max/1e6).toFixed(2)} MW</span>
            </div>
            <div class="flex justify-between items-center py-1">
                <span class="text-gray-500 text-sm font-bold">Mean:</span>
                <span class="font-bold text-gray-900 ml-2 text-sm">${(feature.properties.mean/1e6).toFixed(2)} MW</span>
            </div>
            <div class="flex justify-between items-center py-1">
                <span class="text-gray-500 text-sm">Aggregated:</span>
                <span class="font-bold text-gray-900 ml-2 text-sm">${(conversion_Wh * (feature.properties.sum/1e6)).toFixed(0)} MWh/year</span>
            </div>
            <div class="flex justify-between items-center py-1">
                <span class="text-gray-500 text-sm">Estimated Households Number:</span>
                <span class="font-bold text-gray-900 ml-2 text-sm">${feature.properties.num_hh}</span>
            </div>
            <div class="flex justify-between items-center py-1">
                <span class="text-gray-500 text-sm">Household Peak max:</span>
                <span class="font-bold text-gray-900 ml-2 text-sm">${Math.round(feature.properties.hh_max * 100) / 100} W</span>
            </div>
            <div class="flex justify-between items-center py-1">
                <span class="text-gray-500 text-sm">Household mean:</span>
                <span class="font-bold text-gray-900 ml-2 text-sm">${Math.round(feature.properties.hh_mean * 100) / 100} W</span>
            </div>
            <div class="flex justify-between items-center py-1">
                <span class="text-gray-500 text-sm">Household aggregated:</span>
                <span class="font-bold text-gray-900 ml-2 text-sm">${Math.round(conversion_Wh * feature.properties.hh_sum/1e3)} kWh/year</span>
            </div>
        </div>
        <div class="pt-2 flex space-x-2 border-t border-gray-200">
            <button id="${buttonId}" class="flex-1 flex items-center justify-center space-x-1 px-3 py-2 text-xs bg-emerald-700 text-white rounded-md hover:bg-emerald-800 font-medium transition-colors duration-200">
                Analyze Region
            </button>
        </div>
    </div>
`;

    layer.bindPopup(popupContent, {
        maxWidth: 320,
        className: "custom-popup"
    });

    layer.on('popupopen', function () {
        document.getElementById(buttonId).addEventListener('click', function () {
            showRightPanel(feature.properties);
        });
    });

}


const layerNames = {
  "max": "Peak max",
  "mean": "Mean",
  "sum": "Aggregated",
  "hh_max": "Household Peak",
  "hh_mean": "Household Mean",
  "hh_sum": "Household Agg.",
  "hh_num": "Household Number",
  "cluster": "ML Cluster"
};

const layerUnits = {
    "max": "MW",
    "mean": "MW",
    "sum": "MWh/year",
    "hh_max": "W",
    "hh_mean": "W",
    "hh_sum": "kWh/year",
    "hh_num": "",
    "cluster": ""
};

const layerScalingFactor = {
    "max": 1e-6,
    "mean": 1e-6,
    "sum": conversion_Wh*1e-6,
    "hh_max": 1,
    "hh_mean": 1,
    "hh_sum": conversion_Wh*1e-3,
    "hh_num": 1,
    "cluster": 1
};


function updateChoropleth(data, currentProperty) {
    colorScale = computeThresholds(data, currentProperty);
    function getColor(value) {
        for (let i = colorScale.length - 1; i >= 0; i--) {
            if (value > colorScale[i]) {
                return colors[i + 1];
            }
        }
        return colors[0];
    }
    function set_country_color(feature, layer = null) {
        return {
            "fillColor": getColor(feature.properties[currentProperty]),
            "color": getColor(feature.properties[currentProperty]),
            "weight": 2,
            "fillOpacity": 0.8,
        };
    };
    if (geojson) {
        geojson.remove();
    }
    geojson = L.geoJson(data, { style: set_country_color, onEachFeature: highlight_state, }).addTo(map);


    function createLegend(thresholds, colors) {
        const container = document.createElement('div');
        container.className = "bg-white p-3 w-40 rounded-lg shadow-sm border border-gray-200";

        const label = document.createElement('label');
        label.className = "text-xs font-medium leading-tight";
        label.textContent = `${layerNames[currentProperty]} (${layerUnits[currentProperty]})`;
        container.appendChild(label);

        const spaceY1 = document.createElement('div');
        spaceY1.className = "space-y-1 mt-2";
        container.appendChild(spaceY1);

        for (let i = 0; i < thresholds.length; i++) {
            const row = document.createElement('div');
            row.className = "flex items-center space-x-2";

            const colorBox = document.createElement('div');
            colorBox.className = "w-4 h-2 rounded flex-shrink-0";
            colorBox.style.backgroundColor = colors[i];

            const labelSpan = document.createElement('span');
            labelSpan.className = "text-xs text-gray-600";
            labelSpan.textContent = `${(layerScalingFactor[currentProperty]*thresholds[i]).toFixed(2)}`;

            row.appendChild(colorBox);
            row.appendChild(labelSpan);
            spaceY1.appendChild(row);
        }

        return container;
    }



    // Usage example
    const legendContainer = document.getElementById('mapLegend');

    // Clear previous legend
    legendContainer.innerHTML = '';

    // Create and append new legend
    const legend = createLegend(colorScale, colors);
    legendContainer.appendChild(legend);
}


// Map style change functionality
document.getElementById('mapStyleSelect').addEventListener('change', function() {
    const style = this.value;
    let tileUrl;

    switch(style) {
        case 'Dark':
            tileUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
            break;
        case 'Satellite':
            tileUrl = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
            break;
        default:
            tileUrl = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
    }

    map.removeLayer(currentTileLayer);
    currentTileLayer = L.tileLayer(tileUrl, {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
});
