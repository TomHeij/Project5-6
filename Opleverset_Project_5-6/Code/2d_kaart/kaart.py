
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

        self.map_x = [200.0, 399.0, 400.0, 411.0, 420.0, 500.0]
        self.map_y = [500.0, 499.0,488.0, 399.0, 299.0, 200.0]
        self.current_step = 0
        self.tail_length = 5
        
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


        self.start_animation()
        self.update_position()
        

    def start_animation(self):
        # Start timer (interval in milliseconds: 100ms = 10 updates/sec)
        self.current_step = 0
        self.timer.start(100)

    def update_position(self):

        if self.current_step < len(self.map_x):

            start_idx = max(0, self.current_step - self.tail_length)
            
            # 2. Get the slices of data for the tail
            tail_x = self.map_x[start_idx : self.current_step + 1]
            tail_y = self.map_y[start_idx : self.current_step + 1]
            
            self.plot_widget.clear()
            
            # 3. Plot the tail (the line)
            self.plot_widget.plot(tail_x, tail_y, pen='b')
            x = [self.map_x[self.current_step]]
            y = [self.map_y[self.current_step]]
            
            # Update your plot widget
            # We clear or overwrite the previous point to show 'movement'
            #self.plot_widget.clear() 
            self.plot_widget.plot(x, y, symbol='o', symbolSize=20, symbolBrush='b')
            
            print(f"Moving to: {x}, {y}")
            self.current_step += 1
        else:
            # reset
            self.current_step = 0
            


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