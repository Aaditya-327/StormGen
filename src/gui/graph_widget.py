from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.canvas)
        self.ax = self.figure.add_subplot(111)
        self.is_dark = False # Default to light
        
    def plot_data(self, df, is_metric=False):
        self.figure.clear() # Clear the entire figure
        self.ax = self.figure.add_subplot(111) # Re-add subplot
        
        # Apply current theme to new axes
        self.set_theme(self.is_dark)
        
        # Plot incremental rainfall as bars
        hours = df["Hours"].values
        
        if is_metric:
            incremental = df["Incremental Rainfall (mm)"].values
            cumulative = df["Cumulative Rainfall (mm)"].values
            unit_label = "(mm)"
            color_inc = 'orange' # Different color for metric? Or keep same? Let's keep blue/green standard
        else:
            incremental = df["Incremental Rainfall (in)"].values
            cumulative = df["Cumulative Rainfall (in)"].values
            unit_label = "(in)"

        # Bar plot for incremental (hyetograph)
        self.ax.bar(hours, incremental, width=0.1, align='edge', label=f'Incremental {unit_label}', color='blue', alpha=0.7)
        
        # Line plot for cumulative on secondary axis
        self.ax2 = self.ax.twinx()
        self.ax2.plot(hours, cumulative, color='green', label=f'Cumulative {unit_label}', linewidth=2)
        self.ax2.set_ylabel(f'Cumulative Rainfall {unit_label}', color='green')
        
        self.ax.set_xlabel('Time (hours)')
        self.ax.set_ylabel(f'Incremental Rainfall {unit_label}', color='blue')
        self.ax.set_title('24-Hour Rainfall Hyetograph')
        
        # Legend
        # Combine legends
        lines, labels = self.ax.get_legend_handles_labels()
        lines2, labels2 = self.ax2.get_legend_handles_labels()
        self.ax.legend(lines + lines2, labels + labels2, loc='lower right')
        
        self.ax.grid(True, linestyle='--', alpha=0.7)
        
        # Apply theme to new axes (both ax and ax2)
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
        
        # Axis lines and labels
        self.ax.spines['bottom'].set_color(fg)
        self.ax.spines['top'].set_color(fg) 
        self.ax.spines['left'].set_color(fg)
        self.ax.spines['right'].set_color(fg)
        self.ax.xaxis.label.set_color(fg)
        self.ax.yaxis.label.set_color(fg)
        self.ax.tick_params(axis='x', colors=fg)
        self.ax.tick_params(axis='y', colors=fg)
        self.ax.title.set_color(fg)
        
        # Grid color
        self.ax.grid(True, linestyle='--', alpha=0.7, color=grid)
        
        # Style ax2 if it exists
        if hasattr(self, 'ax2'):
            self.ax2.spines['bottom'].set_color(fg)
            self.ax2.spines['top'].set_color(fg) 
            self.ax2.spines['left'].set_color(fg)
            self.ax2.spines['right'].set_color(fg)
            # Y-label is already green, but let's ensure ticks are visible
            self.ax2.tick_params(axis='y', colors='green') 
            # Or use fg for ticks if preferred, but green matches line
        
        # Update legend if exists
        legend = self.ax.get_legend()
        if legend:
            plt.setp(legend.get_texts(), color=fg)
            legend.get_frame().set_facecolor(bg)
            legend.get_frame().set_edgecolor(grid)
            
        self.canvas.draw()
