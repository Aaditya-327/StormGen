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
            <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
            <style>
                html, body { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; }
                #map { position: absolute; top: 0; bottom: 0; left: 0; right: 0; }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map', {
                    zoomControl: true, // Enable zoom buttons
                    maxZoom: 25
                }).setView([37.0902, -95.7129], 4); // Center of US

                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 25,
                    maxNativeZoom: 19,
                    attribution: '© OpenStreetMap contributors'
                }).addTo(map);

                var marker;

                function onMapClick(e) {
                    if (marker) {
                        map.removeLayer(marker);
                    }
                    marker = L.marker(e.latlng).addTo(map);
                    // Send coordinates back to Python
                    // We can use the window title or console as a bridge if QWebChannel is too complex for now,
                    // but QWebChannel is cleaner. For simplicity in this step, we'll try a title hack or just basic JS bridge later.
                    // Actually, let's use the qeel (QtWebEngine equivalent) way or just simple console.log monitoring if possible, 
                    // but for now, we'll set the title title to coordinates and catch it in python.
                    document.title = "LOC:" + e.latlng.lat + "," + e.latlng.lng;
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
