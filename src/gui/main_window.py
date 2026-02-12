from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QDoubleSpinBox, QPushButton, 
                             QTableWidget, QTabWidget, QTableWidgetItem, QMessageBox,
                             QScrollArea, QApplication)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from src.gui.map_widget import MapWidget
from src.gui.graph_widget import GraphWidget
from src.core.atlas14 import Atlas14Fetcher
from src.core.generator import RainfallGenerator

class FetchWorker(QThread):
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, lat, lon):
        super().__init__()
        self.lat = lat
        self.lon = lon
        self.fetcher = Atlas14Fetcher()

    def run(self):
        try:
            data = self.fetcher.fetch_data(self.lat, self.lon)
            self.result_ready.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StormGen: Automated NOAA Rainfall Distribution Tool")
        self.resize(1200, 800)
        
        self.generator = RainfallGenerator()
        self.fetched_data = None
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QHBoxLayout(self.central_widget)
        
        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        # Left Panel (Controls)
        self.left_panel = QScrollArea()
        self.left_panel.setWidgetResizable(True)
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_panel.setWidget(self.left_widget)
        self.left_panel.setFixedWidth(350)
        
        # Coordinates
        self.left_layout.addWidget(QLabel("<b>Location Selection</b>"))
        self.lbl_coords = QLabel("Lat, Lon:")
        self.left_layout.addWidget(self.lbl_coords)
        
        coords_layout = QHBoxLayout()
        self.input_lat = QDoubleSpinBox()
        self.input_lat.setRange(-90, 90)
        self.input_lat.setDecimals(6)
        
        self.input_lon = QDoubleSpinBox()
        self.input_lon.setRange(-180, 180)
        self.input_lon.setDecimals(6)
        
        coords_layout.addWidget(QLabel("Lat:"))
        coords_layout.addWidget(self.input_lat)
        coords_layout.addWidget(QLabel("Lon:"))
        coords_layout.addWidget(self.input_lon)
        self.left_layout.addLayout(coords_layout)
        
        self.btn_fetch = QPushButton("Fetch NOAA Data")
        self.left_layout.addWidget(self.btn_fetch)
        
        self.left_layout.addWidget(self._make_line())
        
        # Results / Info
        self.left_layout.addWidget(QLabel("<b>Fetch Results</b>"))
        
        # Return Period Selection
        rp_layout = QHBoxLayout()
        rp_layout.addWidget(QLabel("Return Period:"))
        self.combo_return_period = QComboBox()
        self.combo_return_period.addItems(["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr", "1000yr"])
        self.combo_return_period.setCurrentText("25yr") # Default
        rp_layout.addWidget(self.combo_return_period)
        self.left_layout.addLayout(rp_layout)
        
        self.lbl_results = QLabel("No data fetched yet.")
        self.lbl_results.setWordWrap(True)
        # Removing background color as requested, keeping border for structure
        self.lbl_results.setStyleSheet("padding: 5px; border: 1px solid #ddd; border-radius: 3px;")
        self.left_layout.addWidget(self.lbl_results)
        
        self.left_layout.addWidget(self._make_line())
        
        # Generator Inputs
        self.left_layout.addWidget(QLabel("<b>Generation Parameters</b>"))
        
        self.lbl_depth = QLabel("24h Rainfall Depth (in):")
        self.left_layout.addWidget(self.lbl_depth)
        self.input_depth = QDoubleSpinBox()
        self.input_depth.setRange(0, 500) # Increased range for 500yr events
        self.input_depth.setDecimals(2)
        self.left_layout.addWidget(self.input_depth)
        
        self.lbl_pattern = QLabel("Distribution Pattern:")
        self.left_layout.addWidget(self.lbl_pattern)
        self.combo_pattern = QComboBox()
        self.combo_pattern.addItems([
            "Auto-Select (Best Available)",
            "NOAA Region A",
            "NOAA Region B",
            "NOAA Region C",
            "NOAA Region D",
            "SCS Type I (Legacy/Pacific)", 
            "SCS Type IA (Legacy/Pacific)", 
            "SCS Type II (Legacy/Standard)", 
            "SCS Type III (Legacy/Gulf)",
            "Custom (Paste Table)"
        ])
        self.left_layout.addWidget(self.combo_pattern)
        
        # Add a help tip regarding distributions
        self.lbl_dist_help = QLabel("<i>Note: NOAA Atlas 14 distributions (A/B/C/D) are site-specific. <br>Auto-Select uses the best standard proxy. <br>Use 'Custom' for exact regional data.</i>")
        self.lbl_dist_help.setWordWrap(True)
        self.lbl_dist_help.setStyleSheet("color: #666; font-size: 10px;")
        self.left_layout.addWidget(self.lbl_dist_help)
        
        self.btn_generate = QPushButton("Generate Rainfall")
        self.btn_generate.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
        self.left_layout.addWidget(self.btn_generate)
        
        # Add attribution
        self.lbl_attribution = QLabel("Made by Aadi Bhattarai (aaditya.r.bhattarai@gmail.com)")
        self.lbl_attribution.setAlignment(Qt.AlignCenter)
        self.left_layout.addWidget(self.lbl_attribution)
        
        # Add note about 48h data
        self.lbl_note_48h = QLabel("<b>Note:</b> Output includes an additional 24h tail of zero rainfall (48h total duration).")
        self.lbl_note_48h.setWordWrap(True)
        self.left_layout.addWidget(self.lbl_note_48h)
        
        self.left_layout.addStretch()
        
        # Theme Toggle
        self.btn_theme = QPushButton("Dark Mode") 
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.setFixedSize(100, 40) # Make it wider for text
        self.btn_theme.setStyleSheet("font-size: 14px; border-radius: 20px; border: 1px solid #ccc;")
        self.left_layout.addWidget(self.btn_theme)
        
        # Right Panel (Tabs)
        self.tabs = QTabWidget()
        self.tab_map = MapWidget()
        self.tab_graph = GraphWidget()
        
        # Atlas 14 Tab with Copy Button
        self.atlas14_container = QWidget()
        self.atlas14_layout = QVBoxLayout(self.atlas14_container)
        self.btn_copy_atlas14 = QPushButton("Copy Atlas 14 Table")
        self.btn_copy_atlas14.setStyleSheet("padding: 2px; height: 25px;")
        self.tab_atlas14 = QTableWidget()
        self.atlas14_layout.addWidget(self.btn_copy_atlas14)
        self.atlas14_layout.addWidget(self.tab_atlas14)
        
        # Results Tab with Copy Button
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.btn_copy_results = QPushButton("Copy Results Table")
        self.btn_copy_results.setStyleSheet("padding: 2px; height: 25px;")
        self.tab_table = QTableWidget()
        self.results_layout.addWidget(self.btn_copy_results)
        self.results_layout.addWidget(self.tab_table)
        
        self.tabs.addTab(self.tab_map, "Map Selection")
        self.tabs.addTab(self.atlas14_container, "Atlas 14 Data")
        self.tabs.addTab(self.results_container, "Formatted Results")
        self.tabs.addTab(self.tab_graph, "Hyetograph")
        
        self.layout.addWidget(self.left_panel)
        self.layout.addWidget(self.tabs)
        
        # Initialize Theme
        self.is_dark_mode = False
        self._apply_theme()

    def _make_line(self):
        line = QWidget()
        line.setFixedHeight(1)
        line.setObjectName("separator_line") # Use ID for styling
        return line

    def _connect_signals(self):
        self.tab_map.location_selected.connect(self._on_map_location)
        self.btn_fetch.clicked.connect(self._on_fetch_clicked)
        self.btn_generate.clicked.connect(self._on_generate_clicked)
        self.btn_theme.clicked.connect(self._toggle_theme)
        self.input_lat.valueChanged.connect(self._update_coords_label)
        self.input_lon.valueChanged.connect(self._update_coords_label)
        self.combo_return_period.currentTextChanged.connect(self._update_display_values)
        self.btn_copy_results.clicked.connect(lambda: self._copy_table_to_clipboard(self.tab_table))
        self.btn_copy_atlas14.clicked.connect(lambda: self._copy_table_to_clipboard(self.tab_atlas14))

    def _toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self._apply_theme()
        
    def _apply_theme(self):
        if self.is_dark_mode:
            self.btn_theme.setText("Light Mode") # Switch to Light
            # Dark Theme Palette
            bg_color = "#2b2b2b"
            fg_color = "#ffffff"
            input_bg = "#3c3f41"
            border_color = "#555"
            link_color = "#8ab4f8"
            
            # App-wide stylesheet
            self.setStyleSheet(f"""
                QMainWindow, QWidget {{ background-color: {bg_color}; color: {fg_color}; }}
                QScrollArea {{ border: none; background-color: {bg_color}; }}
                QLabel {{ color: {fg_color}; }}
                QLineEdit, QDoubleSpinBox, QComboBox {{ 
                    background-color: {input_bg}; 
                    color: {fg_color}; 
                    border: 1px solid {border_color}; 
                    padding: 4px;
                    border-radius: 4px;
                }}
                QComboBox::drop-down {{ border: none; }}
                QPushButton {{ 
                    background-color: #0d6efd; 
                    color: white; 
                    border: 1px solid #0a58ca; 
                    padding: 6px; 
                    border-radius: 4px; 
                }}
                QPushButton:hover {{ background-color: #0b5ed7; }}
                QTableWidget {{ 
                    background-color: {input_bg}; 
                    color: {fg_color}; 
                    gridline-color: {border_color};
                }}
                QHeaderView::section {{
                    background-color: {input_bg};
                    color: {fg_color};
                    border: 1px solid {border_color};
                }}
                QTabWidget::pane {{ border: 1px solid {border_color}; }}
                QTabBar::tab {{ background-color: {input_bg}; color: {fg_color}; padding: 8px; margin-right: 2px; }}
                QTabBar::tab:selected {{ background-color: #0d6efd; color: white; }}
            """)
            
            # Specific Widgets
            self.lbl_results.setStyleSheet(f"padding: 5px; border: 1px solid {border_color}; border-radius: 3px; color: {fg_color};")
            self.lbl_dist_help.setStyleSheet(f"color: #aaa; font-size: 10px;")
            self.lbl_attribution.setStyleSheet(f"color: #888; font-size: 10px; margin-top: 10px;")
            self.lbl_note_48h.setStyleSheet(f"color: #ddd; font-size: 11px; margin-top: 5px;")
            
            # Lines need specific object name styling if possible or manual update
            # Since _make_line returns lines that are already added, updating stylesheets globally handles most, 
            # but specific color overrides need attention.
            # We used objectName "separator_line" in _make_line
            # We can append this to the main stylesheet
            self.setStyleSheet(self.styleSheet() + f" QWidget#separator_line {{ background-color: #555; }}")
            
        else:
            self.btn_theme.setText("Dark Mode") # Switch to Dark
            # Light Theme
            bg_color = "#ffffff"
            fg_color = "#000000"
            input_bg = "#ffffff"
            border_color = "#ccc"
            
            self.setStyleSheet("") # Clear to default, then apply specifics
            self.central_widget.setStyleSheet("")
            
            # Re-apply basic styling for buttons/inputs if we want a "premium" light look
            self.setStyleSheet(f"""
                QMainWindow {{ background-color: #f8f9fa; }}
                QScrollArea {{ background-color: #f8f9fa; border: none; }}
                QWidget {{ background-color: #f8f9fa; color: #212529; }} /* Explicitly set QWidget background */
                QLabel {{ color: #212529; }}
                QLineEdit, QDoubleSpinBox, QComboBox {{ 
                    background-color: #fff; 
                    color: #212529; 
                    border: 1px solid #ced4da; 
                    padding: 4px;
                    border-radius: 4px;
                }}
                QPushButton {{ 
                    background-color: #0d6efd; 
                    color: white; 
                    border: 1px solid #0a58ca; 
                    padding: 6px; 
                    border-radius: 4px; 
                }}
                QPushButton:hover {{ background-color: #0b5ed7; }}
                QTableWidget {{ background-color: white; alternate-background-color: #f2f2f2; }}
            """)
            
            # Specific Widgets
            self.lbl_results.setStyleSheet(f"padding: 5px; border: 1px solid #ddd; border-radius: 3px; color: #000;")
            self.lbl_dist_help.setStyleSheet("color: #666; font-size: 10px;")
            self.lbl_attribution.setStyleSheet("color: #888; font-size: 10px; margin-top: 10px;")
            self.lbl_note_48h.setStyleSheet("color: #000; font-size: 11px; margin-top: 5px;")
            
            self.setStyleSheet(self.styleSheet() + f" QWidget#separator_line {{ background-color: #ccc; }}")
            
        # Update child widgets
        self.tab_graph.set_theme(self.is_dark_mode)
        self.tab_map.set_theme(self.is_dark_mode)
        
        # Update btn_generate specifically if needed (it overrides the global QPushButton style)
        self.btn_generate.setStyleSheet("background-color: #198754; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")

    def _on_map_location(self, lat, lon):
        self.input_lat.setValue(lat)
        self.input_lon.setValue(lon)

    def _update_coords_label(self):
        pass # Optional logic

    def _on_fetch_clicked(self):
        lat = self.input_lat.value()
        lon = self.input_lon.value()
        
        if lat == 0 and lon == 0:
            QMessageBox.warning(self, "Invalid Location", "Please select a location on the map or enter coordinates.")
            return

        # Update map to reflect manually entered coordinates (as requested by user)
        self.tab_map.set_marker_location(lat, lon)
            
        self.btn_fetch.setEnabled(False)
        self.btn_fetch.setText("Fetching...")
        self.lbl_results.setText("Fetching data from NOAA Atlas 14...")
        
        self.worker = FetchWorker(lat, lon)
        self.worker.result_ready.connect(self._on_fetch_success)
        self.worker.error_occurred.connect(self._on_fetch_error)
        self.worker.start()

    def _on_fetch_success(self, data):
        self.btn_fetch.setEnabled(True)
        self.btn_fetch.setText("Fetch NOAA Data")
        
        self.fetched_data = data
        self.full_atlas_data = data.get("full_data", {}) # Store the full dataset
        
        # Trigger update based on current selection
        self._update_display_values()
        
        # Populate Atlas 14 Table
        self._populate_atlas14_table(self.full_atlas_data)
        
    def _update_display_values(self):
        if not self.fetched_data or not hasattr(self, 'full_atlas_data'):
            return
            
        rp_text = self.combo_return_period.currentText()
        try:
            rp = int(rp_text.replace("yr", ""))
        except ValueError:
            rp = 25 # Default fallback
            
        # Retrieve values from full data
        # Note: keys in atlas14.py might include '60-min' and '24-hr'
        d60m = self.full_atlas_data.get("60-min", {}).get(rp, 0.0)
        d24h = self.full_atlas_data.get("24-hr", {}).get(rp, 0.0)
        
        # If not found (e.g. 1000yr might be missing in some regions), fallback or show 0
        
        # Calculate Ratio
        ratio = self.generator.calculate_ratio(d60m, d24h)
        type_name, proxy_name = self.generator.suggest_type(ratio)
        
        # Update Results Label
        info = (f"<b>Fetched Data ({rp_text}):</b><br>"
                f"60-min: {d60m:.2f} in<br>"
                f"24-hr: {d24h:.2f} in<br>"
                f"Ratio: {ratio:.3f}<br><br>"
                f"<b>Recommendation:</b><br>"
                f"Region: {type_name}<br>"
                f"Pattern: {proxy_name}")
        self.lbl_results.setText(info)
        
        # Auto-fill logic as requested
        self.input_depth.setValue(d24h)
        
        # Auto-select proxy if "Auto-Select" is chosen
        if self.combo_pattern.currentText().startswith("Auto-Select"):
            # Find the proxy in the combo box
            index = self.combo_pattern.findText(proxy_name, Qt.MatchContains)
            if index >= 0:
                self.combo_pattern.setCurrentIndex(index)

    def _on_fetch_error(self, error_msg):
        self.btn_fetch.setEnabled(True)
        self.btn_fetch.setText("Fetch NOAA Data")
        self.lbl_results.setText(f"<font color='red'>Error: {error_msg}</font>")
        QMessageBox.critical(self, "Fetch Error", f"Failed to fetch data:\n{error_msg}")

    def _on_generate_clicked(self):
        depth = self.input_depth.value()
        pattern = self.combo_pattern.currentText()
        
        if pattern.startswith("Auto-Select"):
            # Recalculate if still on auto
            if self.fetched_data and hasattr(self, 'full_atlas_data'):
                 # Get current RP
                 rp_text = self.combo_return_period.currentText()
                 try:
                     rp = int(rp_text.replace("yr", ""))
                 except ValueError:
                     rp = 25

                 d60m = self.full_atlas_data.get("60-min", {}).get(rp, 0.0)
                 d24h = self.full_atlas_data.get("24-hr", {}).get(rp, 0.0)
                 
                 ratio = self.generator.calculate_ratio(d60m, d24h)
                 _, proxy_name = self.generator.suggest_type(ratio)
                 pattern = proxy_name
            elif self.fetched_data:
                 # Fallback
                 d60m = self.fetched_data["60m_25yr"]
                 d24h = self.fetched_data["24h_25yr"]
                 ratio = self.generator.calculate_ratio(d60m, d24h)
                 _, proxy_name = self.generator.suggest_type(ratio)
                 pattern = proxy_name
            else:
                QMessageBox.warning(self, "No Data", "Please fetch data first for Auto-Select.")
                return

        # Check if Custom
        if pattern.startswith("Custom"):
            # TODO: Implement a dialog to paste the table
            # For now, just show a warning that it's not implemented fully in this snippet
            QMessageBox.information(self, "Custom Distribution", "Please assume a flat distribution for now or implement the paste dialog.")
            # For the sake of the generator, we need to pass a valid dict if name is "Custom"
            # generator.generate expects custom_curve argument if name is "Custom"
            # Let's just return for now or implement a simple input dialog
            pass

        try:
            df = self.generator.generate(depth, pattern)
            
            # Populate Table
            self.tab_table.setRowCount(len(df))
            self.tab_table.setColumnCount(len(df.columns))
            self.tab_table.setHorizontalHeaderLabels(df.columns)
            
            for i, row in df.iterrows():
                for j, val in enumerate(row):
                    self.tab_table.setItem(i, j, QTableWidgetItem(str(val)))
            
            self.tab_table.resizeColumnsToContents()
            
            # Plot Graph
            self.tab_graph.plot_data(df)
            
            self.tabs.setCurrentIndex(2) # Switch to Graph tab
            
        except Exception as e:
            QMessageBox.critical(self, "Generation Error", str(e))

    def _populate_atlas14_table(self, data_map):
        """
        Populates the Atlas 14 Data tab with the full fetched dataset.
        Rows: Durations
        Cols: Return Periods
        """
        if not data_map:
            return

        # Define preferred sort order for durations
        duration_order = [
            "5-min", "10-min", "15-min", "30-min", "60-min", 
            "2-hr", "3-hr", "6-hr", "12-hr", "24-hr",
            "2-day", "3-day", "4-day", "7-day", "10-day", 
            "20-day", "30-day", "45-day", "60-day"
        ]
        
        # Get available durations and sort them
        available_durations = list(data_map.keys())
        # Sort based on index in duration_order, put unknowns at the end
        available_durations.sort(key=lambda x: duration_order.index(x) if x in duration_order else 999)
        
        if not available_durations:
            return

        # Get available return periods from the first duration (assuming consistent)
        first_dur = available_durations[0]
        return_periods = sorted([int(rp) for rp in data_map[first_dur].keys()])
        
        # Setup Table
        self.tab_atlas14.setRowCount(len(available_durations))
        self.tab_atlas14.setColumnCount(len(return_periods))
        
        # Set Headers
        info_header = [f"{rp}-yr" for rp in return_periods]
        self.tab_atlas14.setHorizontalHeaderLabels(info_header)
        self.tab_atlas14.setVerticalHeaderLabels(available_durations)
        
        # Fill Data
        for row_idx, dur in enumerate(available_durations):
            row_data = data_map[dur]
            for col_idx, rp in enumerate(return_periods):
                val = row_data.get(rp, "")
                if isinstance(val, (int, float)):
                    item = QTableWidgetItem(f"{val:.3f}")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.tab_atlas14.setItem(row_idx, col_idx, item)
                else:
                    self.tab_atlas14.setItem(row_idx, col_idx, QTableWidgetItem(""))
        
        self.tab_atlas14.resizeColumnsToContents()

    def _copy_table_to_clipboard(self, table):
        """Copies the contents of a QTableWidget to the clipboard in TSV format."""
        if table.rowCount() == 0:
            return

        text = ""
        # Add Headers
        headers = []
        for j in range(table.columnCount()):
            headers.append(str(table.horizontalHeaderItem(j).text()) if table.horizontalHeaderItem(j) else "")
        
        if table == self.tab_atlas14:
            # Add vertical header if it's the Atlas 14 table (Durations)
            text += "\t" + "\t".join(headers) + "\n"
            for i in range(table.rowCount()):
                row_label = table.verticalHeaderItem(i).text() if table.verticalHeaderItem(i) else ""
                row_data = []
                for j in range(table.columnCount()):
                    item = table.item(i, j)
                    row_data.append(item.text() if item else "")
                text += row_label + "\t" + "\t".join(row_data) + "\n"
        else:
            text += "\t".join(headers) + "\n"
            for i in range(table.rowCount()):
                row_data = []
                for j in range(table.columnCount()):
                    item = table.item(i, j)
                    row_data.append(item.text() if item else "")
                text += "\t".join(row_data) + "\n"

        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied", "Table data copied to clipboard.")
