from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

class IDFWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.ax = self.figure.add_subplot(111)
        self.is_dark = False
        
    def plot_data(self, atlas_data):
        """
        Plot IDF curves on a log-log scale.
        atlas_data: dict containing '60-min', '24-hr', etc. or the structured full_data from Atlas14
        
        Expected structure of atlas_data (from full_atlas_data in MainWindow):
        {
            "5-min": {2: val, 5: val, ...},
            "15-min": {...},
            ...
        }
        """
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.set_theme(self.is_dark)
        
        if not atlas_data:
            self.ax.text(0.5, 0.5, "No Data Available", 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, color='gray')
            self.canvas.draw()
            return

        # Define standard durations in minutes and their label for plotting
        # dur_map = {"5-min": 5, "15-min": 15, "60-min": 60, "2-hr": 120, "3-hr": 180, "6-hr": 360, "12-hr": 720, "24-hr": 1440}
        # But we need to check what keys are actually in atlas_data.
        # Based on atlas14.py, keys are like "5-min", "60-min", "24-hr".
        
        # Helper to parse duration key to minutes
        def parse_dur(k):
            if "-min" in k: return int(k.replace("-min", ""))
            if "-hr" in k: return int(k.replace("-hr", "")) * 60
            return None

        # Prepare X (Duration in min) and Y (Intensity in in/hr)
        # We want a line for each Return Period.
        # Identify available Return Periods first.
        
        # We look at the first available duration to get RPs
        first_key = list(atlas_data.keys())[0]
        rps = sorted(atlas_data[first_key].keys()) # e.g. [1, 2, 5, 10, 25, 50, 100, 200, 500, 1000]
        
        # Collect data for each RP
        # X axis: Duration (minutes)
        # Y axis: Intensity (in/hr)
        
        durations = []
        for k in atlas_data.keys():
            m = parse_dur(k)
            if m: durations.append((k, m))
        
        # Sort by duration minutes
        durations.sort(key=lambda x: x[1])
        
        x_vals = [d[1] for d in durations] # minutes
        
        # Define colors/markers for standard RPs
        # Use a colormap or fixed list
        colors = plt.cm.jet(np.linspace(0, 1, len(rps)))
        
        for i, rp in enumerate(rps):
            y_vals = [] # Intensity
            
            for k, m in durations:
                depth = atlas_data[k].get(rp, np.nan)
                # Intensity = Depth / (Duration_in_hours)
                intensity = depth / (m / 60.0)
                y_vals.append(intensity)
            
            # Plot
            label = f"{rp}-yr"
            self.ax.loglog(x_vals, y_vals, marker='o', linestyle='-', label=label, color=colors[i], markersize=4)

        self.ax.set_xlabel('Duration (min)')
        self.ax.set_ylabel('Intensity (in/hr)')
        self.ax.set_title('Intensity-Duration-Frequency (IDF) Curves')
        
        # Set X-ticks to standard durations for readability
        ticks = [5, 15, 60, 180, 720, 1440]
        tick_labels = ["5m", "15m", "1h", "3h", "12h", "24h"]
        self.ax.set_xticks(ticks)
        self.ax.set_xticklabels(tick_labels)
        self.ax.minorticks_on()
        self.ax.grid(True, which="both", linestyle='--', alpha=0.5)
        
        # Legend outside or best fit
        self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
        
        # Adjust layout to make room for legend
        self.figure.tight_layout()
        
        # Re-apply theme colors to new elements
        self.set_theme(self.is_dark)
        
        self.canvas.draw()

    def set_theme(self, is_dark):
        self.is_dark = is_dark
        if is_dark:
            bg = "#2b2b2b"
            fg = "#ffffff"
            grid = "#555555"
        else:
            bg = "#ffffff"
            fg = "#000000"
            grid = "#cccccc"
            
        self.figure.patch.set_facecolor(bg)
        self.ax.set_facecolor(bg)
        
        self.ax.spines['bottom'].set_color(fg)
        self.ax.spines['top'].set_color(fg) 
        self.ax.spines['left'].set_color(fg)
        self.ax.spines['right'].set_color(fg)
        self.ax.xaxis.label.set_color(fg)
        self.ax.yaxis.label.set_color(fg)
        self.ax.tick_params(axis='x', colors=fg, which='both')
        self.ax.tick_params(axis='y', colors=fg, which='both')
        self.ax.title.set_color(fg)
        
        self.ax.grid(True, which="major", linestyle='-', alpha=0.7, color=grid)
        self.ax.grid(True, which="minor", linestyle=':', alpha=0.4, color=grid)
        
        legend = self.ax.get_legend()
        if legend:
            plt.setp(legend.get_texts(), color=fg)
            legend.get_frame().set_facecolor(bg)
            legend.get_frame().set_edgecolor(grid)
            
        self.canvas.draw()
