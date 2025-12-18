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
        self.plot_widget.setLabel('bottom', 'X(m)')
        self.plot_widget.setLabel('left', 'Y(m)')

        #creating grid using native pyqtgraph function (faster)
        self.plot_widget.showGrid(x=True, y=True)



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