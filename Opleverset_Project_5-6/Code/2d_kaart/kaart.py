"""
2D Map Visualization with PyQtGraph.

References:
---------------------
1. PyQtGraph Documentation - PlotWidget and PlotItem:
   https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/plotitem.html
   
2. PySide6 (Qt for Python) Documentation:
   https://doc.qt.io/qtforpython-6/
   
3. PyQtGraph PlotCurveItem for drawing lines (grid overlay):
   https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/plotcurveitem.html

4. Qt ViewBox for controlling zoom/pan and axis limits:
   https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/viewbox.html

"""

# TODO: 
# integrating the map with main.py
# receiving (x, y) coordinates from yolo for the detected objects
# plot shapes of the objects on the map
# shapes move as the detected objects move in real time
# show the past location of the objects with a line


# kaart.py
import sys
import random
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import QTimer, Qt
import pyqtgraph as pg



import warnings
#warnings.filterwarnings("ignore", category=RuntimeWarning) # Ignore runtime warnings
warnings.filterwarnings("ignore", message="Failed to disconnect") # Ignore disconnect warnings for pyqtgraph specifically

# --- Configuration ---
# Set the background to white for a "Map-like" feel (default is black)
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')



class MapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # 1. Create the PlotWidget
        self.plot_widget = pg.PlotWidget(title="Object Locatie Kaart")
        self.layout.addWidget(self.plot_widget)
        
        # OPTIONAL: Lock the aspect ratio so the map doesn't look stretched
        self.plot_widget.setAspectLocked(True)
        
        # Configure the view
        self.plot_widget.showGrid(x=False, y=False)  # Turn off default grid
        self.plot_widget.getPlotItem().setMouseEnabled(x=False, y=False)  # Optional: lock pan/zoom
        self.plot_widget.getPlotItem().getViewBox().setAspectLocked(True)
        self.plot_widget.getPlotItem().getViewBox().setLimits(xMin=0, xMax=1000, yMin=0, yMax=1000)
        self.plot_widget.getPlotItem().getViewBox().setRange(rect=pg.QtCore.QRectF(0, 0, 1000, 1000))
        
        # Add axis labels for coordinates
        self.plot_widget.setLabel('bottom', 'X(km)')
        self.plot_widget.setLabel('left', 'Y(km)')

        # 4. Add Grid Overlay (net of rectangles)
        self.add_grid(grid_size=100)  # 100m x 100m cells (10x10 grid)


    def add_grid(self, grid_size=100, map_size=1000):
        """
        Add a grid overlay of rectangles to the map.
        
        Parameters:
        - grid_size: Size of each grid cell in meters (default 100m)
        - map_size: Total size of the map in meters (default 1000m)
        """
        # Grid line style - semi-transparent gray lines
        grid_pen = pg.mkPen(color=(100, 100, 100, 100), width=2)
        
        # Draw vertical lines
        for x in range(0, map_size + 1, grid_size):
            line = pg.PlotCurveItem(
                x=[x, x], 
                y=[0, map_size], 
                pen=grid_pen
            )
            self.plot_widget.addItem(line)
        
        # Draw horizontal lines
        for y in range(0, map_size + 1, grid_size):
            line = pg.PlotCurveItem(
                x=[0, map_size], 
                y=[y, y], 
                pen=grid_pen
            )
            self.plot_widget.addItem(line)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D Kaart")
        self.resize(1000, 800)

        #UI Setup
        self.map_display = MapWidget()
        self.setCentralWidget(self.map_display)

      

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())