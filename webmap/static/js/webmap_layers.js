fetch('/static/data/webmap_layers.geojson')
  .then(response => response.json())
  .then(data => {
    const webmap_layers = data;
    console.log(webmap_layers);
    updateChoropleth(webmap_layers, "max");
  });
