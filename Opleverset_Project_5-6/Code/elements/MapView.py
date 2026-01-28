from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
import yaml

class MapView(QWidget):
    """2D Map Visualization with PyQtGraph for displaying object positions and trails."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.parent_widget = parent
        
        # Create the PlotWidget
        self.plot_widget = pg.PlotWidget(title="Object Locatie in 2D")
        self.layout.addWidget(self.plot_widget)
        
        # Lock the aspect ratio so the map doesn't look stretched
        self.plot_widget.setAspectLocked(True)
        
        with open("config.yaml", 'r') as file:
            self.config = yaml.safe_load(file)
            
        map_scale = self.config['MapScale']

        
        # Configure the view
        self.plot_widget.showGrid(x=False, y=False)  # Turn off default grid initially
        self.plot_widget.getPlotItem().setMouseEnabled(
            x=False, y=False
        )  #lock pan/zoom
        self.plot_widget.getPlotItem().getViewBox().setAspectLocked(True)
        self.plot_widget.getPlotItem().getViewBox().setLimits(
            xMin=-map_scale, xMax=map_scale, yMin=0, yMax=map_scale
        )
        self.plot_widget.getPlotItem().getViewBox().setRange(
            rect=pg.QtCore.QRectF(-map_scale, 0, map_scale*2, map_scale)
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
        
        # Object tracking for persistent IDs and history
        self._tracked_objects = {}  # Maps object_id to {name, lateral, distance, history, last_seen}
        self._next_object_id = 0
        self._max_history = 20
        self._match_threshold = 1.5  # meters, for matching objects between frames
        self._last_bound_object_data = None  # Store last data for redrawing when settings change
        
        # Connect to sidebar checkbox signals if parent has sidebar
        self._connect_sidebar_signals()

    def set_trails_enabled(self, enabled: bool):
        """Enable or disable trail drawing."""
        self.trails_enabled = enabled
    
    def _connect_sidebar_signals(self):
        """Connect sidebar checkbox signals to redraw the map."""
        if not hasattr(self.parent_widget, 'sidebar') or not self.parent_widget.sidebar:
            return
        
        sidebar = self.parent_widget.sidebar
        
        # Connect checkbox signals to redraw
        if sidebar.cb_trails:
            sidebar.cb_trails.stateChanged.connect(self._on_settings_changed)
        if sidebar.cb_labels:
            sidebar.cb_labels.stateChanged.connect(self._on_settings_changed)
        if sidebar.cb_grid:
            sidebar.cb_grid.stateChanged.connect(self._on_grid_changed)
    
    def _on_settings_changed(self):
        """Redraw map when trails or labels checkbox changes."""
        if self._last_bound_object_data:
            self.update_map(self._last_bound_object_data)
    
    def _on_grid_changed(self):
        """Handle grid checkbox change."""
        if not hasattr(self.parent_widget, 'sidebar') or not self.parent_widget.sidebar:
            return
        
        is_grid_on = self.parent_widget.sidebar.is_grid_enabled()
        self.plot_widget.showGrid(x=is_grid_on, y=is_grid_on, alpha=0.3)
        
        # Redraw if we have data
        if self._last_bound_object_data:
            self.update_map(self._last_bound_object_data)

    def _get_class_color(self, class_name):
        """Get color for a given object class."""
        return self.class_colors.get(class_name, self.class_colors['default'])
    
    def update_map(self, bound_object_data):
        """
        Update map with detected objects from boundObjectData.
        Maintains persistent object IDs and trails across frames.
        
        Args:
            bound_object_data: Dict with keys 'objectName', 'objectDistance', 'objectPosition'
        """
        # Store data for redrawing when settings change
        self._last_bound_object_data = bound_object_data
        
        self.plot_widget.clear()
        self.text_items.clear()
        
        # Extract data from dictionary
        object_names = bound_object_data.get('objectName', [])
        distances = bound_object_data.get('objectDistance', [])
        pixel_positions = bound_object_data.get('objectPosition', [])
        
        if not object_names or not distances or not pixel_positions:
            # Clear stale objects if no detections
            self._tracked_objects.clear()
            return
        
        # Convert detections to meters
        detections = []
        for name, distance, (pixel_x, pixel_y) in zip(object_names, distances, pixel_positions):
            lateral = ((pixel_x - 320) / 1052.42) * distance
            detections.append({
                'name': name,
                'distance': distance,
                'lateral': lateral,
                'pixel_pos': (pixel_x, pixel_y)
            })
        
        # Match detections to existing tracked objects
        matched_ids = set()
        for detection in detections:
            obj_id = self._find_matching_object(detection)
            matched_ids.add(obj_id)
            
            # Update or create tracked object
            if obj_id not in self._tracked_objects:
                self._tracked_objects[obj_id] = {
                    'name': detection['name'],
                    'history': [],
                    'last_seen': 0
                }
            
            track = self._tracked_objects[obj_id]
            track['name'] = detection['name']
            track['lateral'] = detection['lateral']
            track['distance'] = detection['distance']
            track['last_seen'] = 0
            
            # Add to history
            track['history'].append((detection['lateral'], detection['distance']))
            if len(track['history']) > self._max_history:
                track['history'].pop(0)
        
        # Remove stale tracked objects (not seen in this frame)
        stale_ids = [oid for oid in self._tracked_objects.keys() if oid not in matched_ids]
        for stale_id in stale_ids:
            del self._tracked_objects[stale_id]
        
        # Render all tracked objects
        for obj_id, track in self._tracked_objects.items():
            name = track['name']
            lateral = track['lateral']
            distance = track['distance']
            history = track['history']
            
            color = self._get_class_color(name)
            
            # Check if trails should be enabled (from sidebar checkbox)
            trails_enabled = self.trails_enabled
            if hasattr(self.parent_widget, 'sidebar') and self.parent_widget.sidebar:
                trails_enabled = trails_enabled and self.parent_widget.sidebar.is_trails_enabled()
            
            # Plot trail if enabled and has history
            if trails_enabled and len(history) > 1:
                trail_x, trail_y = zip(*history)
                self.plot_widget.plot(
                    trail_x, trail_y,
                    pen=pg.mkPen(color=color, width=2, style=Qt.SolidLine)
                )
            
            # Plot current position
            self.plot_widget.plot(
                [lateral], [distance], 
                symbol='o', symbolSize=15, 
                symbolBrush=pg.mkBrush(color=color),
                pen=pg.mkPen(color=(0, 0, 0), width=1)
            )
            
            # Add text label if labels are enabled (from sidebar checkbox)
            labels_enabled = True
            if hasattr(self.parent_widget, 'sidebar') and self.parent_widget.sidebar:
                labels_enabled = self.parent_widget.sidebar.is_labels_enabled()
            
            if labels_enabled:
                label_text = f"{name}\nID:{obj_id}\n{distance:.2f}m"
                text_item = pg.TextItem(text=label_text, color=(255, 255, 255), anchor=(0.5, 1.25))
                text_item.setPos(lateral, distance)
                self.plot_widget.addItem(text_item)
                self.text_items[obj_id] = text_item
    
    def _find_matching_object(self, detection):
        """
        Find existing tracked object that matches the detection.
        Returns existing object_id or creates new one.
        """
        detection_lateral = detection['lateral']
        detection_distance = detection['distance']
        
        # Try to match with existing objects
        best_match_id = None
        best_distance = self._match_threshold
        
        for obj_id, track in self._tracked_objects.items():
            if 'lateral' not in track or 'distance' not in track:
                continue
            
            # Calculate distance between detection and tracked position
            dx = detection_lateral - track['lateral']
            dy = detection_distance - track['distance']
            dist = (dx**2 + dy**2) ** 0.5
            
            if dist < best_distance:
                best_distance = dist
                best_match_id = obj_id
        
        if best_match_id is not None:
            return best_match_id
        
        # Create new object ID
        new_id = self._next_object_id
        self._next_object_id += 1
        return new_id

    def update_object_positions(self, tracks):
        """Legacy method for compatibility with track dictionaries."""
        self.plot_widget.clear()
        self.text_items.clear()

        if not tracks:
            return
    
        for track in tracks:
            if not isinstance(track, dict):
                continue
            
            obj_id = track.get('id', 0)
            label = track.get('label', 'unknown')
            history = track.get('history', [])
            lateral, forward = track.get('current_pos', (0, 0))
            
            color = self._get_class_color(label)
            
            # Plot trail as a single line if trails are enabled
            if self.trails_enabled and len(history) > 1:
                trail_x, trail_y = zip(*[(pos[0], pos[1]) for pos in history])
                self.plot_widget.plot(
                    trail_x, trail_y,
                    pen=pg.mkPen(color=color, width=2, style=Qt.SolidLine)
                )
            
            # Plot current position as circle
            self.plot_widget.plot(
                [lateral], [forward], 
                symbol='o', symbolSize=15, 
                symbolBrush=pg.mkBrush(color=color),
                pen=pg.mkPen(color=(0, 0, 0), width=1)
            )
            
            # Add text label
            display_depth = history[-1][3] if history else forward
            label_text = f"{label}\nID:{obj_id}\n{display_depth:.2f}m"
            text_item = pg.TextItem(text=label_text, color=(0, 0, 0), anchor=(0.5, 1.5))
            text_item.setPos(lateral, forward)
            self.plot_widget.addItem(text_item)
            self.text_items[obj_id] = text_item