from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg

class MapView(QWidget):
    """2D Map Visualization with PyQtGraph for displaying object positions and trails."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the PlotWidget
        self.plot_widget = pg.PlotWidget(title="Object Locatie in 2D")
        self.layout.addWidget(self.plot_widget)
        
        # Lock the aspect ratio so the map doesn't look stretched
        self.plot_widget.setAspectLocked(True)

        
        # Configure the view
        self.plot_widget.showGrid(x=False, y=False)  # Turn off default grid initially
        self.plot_widget.getPlotItem().setMouseEnabled(
            x=False, y=False
        )  #lock pan/zoom
        self.plot_widget.getPlotItem().getViewBox().setAspectLocked(True)
        self.plot_widget.getPlotItem().getViewBox().setLimits(
            xMin=-10, xMax=10, yMin=0, yMax=10
        )
        self.plot_widget.getPlotItem().getViewBox().setRange(
            rect=pg.QtCore.QRectF(-10, 0, 20, 10)
        )
        
        # Add axis labels for coordinates
        self.plot_widget.setLabel("bottom", "Lateral Position (m)")
        self.plot_widget.setLabel("left", "Forward Distance (m)")
        
        # Create grid using native pyqtgraph function (much faster)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Text items for labels (stored to update/remove them)
        self.text_items = {}  # Maps object_id to TextItem
        
        # Color scheme for different object classes
        self.class_colors = {
            'person': (100, 149, 237),      # Cornflower blue
            'drone': (220, 20, 60),           # Crimson
            'ship': (178, 34, 34),         # Firebrick
            'chair': (50, 205, 50),       # Lime green
            'default': (169, 169, 169)      # Dark gray
        }

        # Trail visibility flag
        self.trails_enabled = True

    def set_trails_enabled(self, enabled: bool):
        """Enable or disable trail drawing."""
        self.trails_enabled = enabled

    
    def _get_class_color(self, class_name):
        """Get color for object class."""
        return self.class_colors.get(class_name.lower(), self.class_colors['default'])
    

    def update_object_positions(self, tracks):
        
        self.plot_widget.clear()
        
        # Remove old text items
        for text_item in self.text_items.values():
            self.plot_widget.removeItem(text_item)
        self.text_items.clear()
        

        if not tracks:
            return
    
        # Process extracted tracks
        for track in tracks:
            if not isinstance(track, dict):
                continue
            
            obj_id = track.get('id', 0)
            label = track.get('label', 'unknown')
            history = track.get('history', [])
            current_pos = track.get('current_pos', (0, 0))
            
            lateral, forward = current_pos
            
    
            # Get color for this object class
            color = self._get_class_color(label)
            
            # Plot trail (history) if trails are enabled
            if self.trails_enabled and len(history) > 1:
                trail_x = [pos[0] for pos in history]
                trail_y = [pos[1] for pos in history]
                # Create gradient effect - older points are more transparent
                for i in range(len(trail_x) - 1):
                    alpha = int(100 + (155 * i / len(trail_x)))
                    pen = pg.mkPen(color=color, width=2, style=Qt.SolidLine)
                    self.plot_widget.plot(
                        [trail_x[i], trail_x[i+1]], 
                        [trail_y[i], trail_y[i+1]], 
                        pen=pen
                    )
            
            # Plot current position as circle
            self.plot_widget.plot(
                [lateral], 
                [forward], 
                symbol='o', 
                symbolSize=15, 
                symbolBrush=pg.mkBrush(color=color),
                pen=pg.mkPen(color=(0, 0, 0), width=1)
            )
            
            # Add text label with object info
            # Use the most recent distance from history if available for display
            display_depth = history[-1][3] if history else forward
            
            label_text = f"{label}\nID:{obj_id}\n{display_depth:.2f}m"
            text_item = pg.TextItem(
                text=label_text,
                color=(0, 0, 0),
                anchor=(0.5, 1.5)  # Position below the point
            )
            text_item.setPos(lateral, forward)
            self.plot_widget.addItem(text_item)
            self.text_items[obj_id] = text_item