from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import pyqtSignal, QUrl
import jinja2
import os

class MapWidget(QWidget):
    location_selected = pyqtSignal(float, float)  # Signal emitting lat, lon

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)
        
        self._init_map()

    def _init_map(self):
        # We will use a simple Leaflet map via HTML/JS
        # This allows clicking to get coordinates
        map_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Map</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <link rel="stylesheet" href="https://unpkg.com/leaflet-geosearch@3.0.0/dist/geosearch.css" />
            <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
            <script src="https://unpkg.com/leaflet-geosearch@3.0.0/dist/geosearch.umd.js"></script>
            <style>
                html, body { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; }
                #map { position: absolute; top: 0; bottom: 0; left: 0; right: 0; }
                /* Fix for dark mode filter affecting search input text availability */
                .leaflet-control-geosearch form input { color: black !important; }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                // Define Base Layers
                var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: '© OpenStreetMap contributors'
                });

                var satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                    maxZoom: 19,
                    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                });

                var map = L.map('map', {
                    zoomControl: true, 
                    maxZoom: 19,
                    layers: [osm] // Default to OSM
                }).setView([37.0902, -95.7129], 4); 

                // Layer Control
                var baseMaps = {
                    "Street Map": osm,
                    "Satellite": satellite
                };
                L.control.layers(baseMaps).addTo(map);

                // Search Control
                const provider = new GeoSearch.OpenStreetMapProvider();
                const searchControl = new GeoSearch.GeoSearchControl({
                    provider: provider,
                    style: 'button',
                    autoClose: true,
                    keepResult: true,
                    showMarker: false, // We handle our own marker
                });
                map.addControl(searchControl);

                var marker;

                // Handle map clicks
                function onMapClick(e) {
                    updateMarker(e.latlng);
                }

                // Handle search results
                map.on('geosearch/showlocation', function(result) {
                    var latlng = result.location;
                    updateMarker({lat: latlng.y, lng: latlng.x});
                });

                function updateMarker(latlng) {
                    if (marker) {
                        map.removeLayer(marker);
                    }
                    marker = L.marker(latlng).addTo(map);
                    // Send coordinates back to Python
                    document.title = "LOC:" + latlng.lat + "," + latlng.lng;
                }

                map.on('click', onMapClick);
            </script>
        </body>
        </html>
        """
        
        self.web_view.setHtml(map_html)
        self.web_view.titleChanged.connect(self._on_title_changed)

    def _on_title_changed(self, title):
        if title.startswith("LOC:"):
            try:
                coords = title.split(":")[1].split(",")
                lat = float(coords[0])
                lon = float(coords[1])
                self.location_selected.emit(lat, lon)
            except Exception as e:
                print(f"Error parsing coordinates: {e}")

    def set_theme(self, is_dark):
        if is_dark:
            # Simple CSS filter for dark mode on the map tiles
            # Inverts colors and rotates hue to make it look like a dark map
            js_filter = "document.querySelector('.leaflet-tile-pane').style.filter = 'invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)';"
            self.web_view.page().runJavaScript(js_filter)
        else:
            js_filter = "document.querySelector('.leaflet-tile-pane').style.filter = 'none';"
            self.web_view.page().runJavaScript(js_filter)

    def set_marker_location(self, lat, lon):
        """
        Updates the map view and places a marker at the given coordinates.
        This is called when the user manually enters coordinates and clicks Fetch.
        """
        js_code = f"""
            var newLatLng = new L.LatLng({lat}, {lon});
            if (marker) {{
                map.removeLayer(marker);
            }}
            marker = L.marker(newLatLng).addTo(map);
            map.setView(newLatLng, 12); // Zoom in to level 12 for better context
            // We do NOT update document.title here to avoid a feedback loop
        """
        self.web_view.page().runJavaScript(js_code)
