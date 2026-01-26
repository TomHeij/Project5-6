# TODO:
# multi-threading (?)
# diepte kaart
#? stereo camera support 
# 2d punt krijgen
# 2d punt op "map" projecteren
# GUI
# verschil tussen cpu en gpu verwerking meten (?, de AI draait op cpu dus :shrug:)
#? kijken naar resoluties,fps waardes en compressie
# configuratie bestand voor instellingen (kan handig zijn gezien we 2 windows gaan hebben) 
# niet real-time iets tekenen/zien maar per aantal frames updaten (zien dat de vierkant over een soort 2de layer gaat ipv direct op de camera feed)
# error handling
# code opschonen en documenteren
# first time install script
# toggle debug cameras on/off

# ncnn
# vulkan
# yolo model door ncnn converteren
# onnx
# yolo11n

from ultralytics import YOLO
import numpy as np
import math
import time
import cv2
import sys
import os

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer
from elements.ui_componenten import CameraView, MapView, MainContentArea, RightOffCanvas

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl

# debug window class
class DebugWindow(QtWidgets.QWidget):
    def __init__(self):
        super(DebugWindow, self).__init__()

        ui_path = os.path.join("elements", "DebugWindow.ui")
        loader = QUiLoader()
        ui_file = QFile(ui_path)
        if not ui_file.open(QFile.ReadOnly):
            raise RuntimeError(f"Failed to open UI file: {ui_path}")
        self.ui = loader.load(ui_file, None)
        ui_file.close()
        if self.ui is None:
            raise RuntimeError(f"Failed to load UI from: {ui_path}")
        
        self.cameraResolution = (1920, 1080)
        self.camIds = (0, 2) # raspberry pi
        # self.camIds = (4, 2) # laptop
        
        self.model = AIModel(self.cameraResolution)

        self.ui.setParent(self)
        self.ui.setMinimumWidth(self.cameraResolution[0])
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        self.setWindowTitle("Debug Window")

        self.cam = self.ui.findChild(QtWidgets.QLabel, "cam")
        self.fpsLabel = self.ui.findChild(QtWidgets.QLabel, "fpsLabel")
        self.frameTimeLabel = self.ui.findChild(QtWidgets.QLabel, "frameTimeLabel")
            
        self.cam.setMinimumSize(self.cameraResolution[0], self.cameraResolution[1])
        self.cam.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.cam.setScaledContents(True)
        
        self.cameraL = StereoCamera(self.camIds[1], self.cameraResolution)
        self.cameraR = StereoCamera(self.camIds[0], self.cameraResolution)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.start_capture)
        self.timer.start(10)  # Update every X ms

    def start_capture(self):
        time_start = time.time()
        captureL, captureR = self.model.predict([self.cameraL.get_frame(), self.cameraR.get_frame()])
        blended = cv2.addWeighted(captureR, 0.5, captureL, 1 - 0.5, 0)
        self.cam.setPixmap(self.cv2_to_qt(blended))
        time_end = time.time()

        self.update_metrics(time_start, time_end)
        
    def update_metrics(self, time_start=None, time_end=None):
        if time_start is not None and time_end is not None:
            frame_time = (time_end - time_start) * 1000  # in milliseconds
            fps = 1000 / frame_time if frame_time > 0 else 0
            self.fpsLabel.setText(f"FPS: {fps:.2f}")
            self.frameTimeLabel.setText(f"Frame Time: {frame_time:.2f} ms")
        else:
            self.fpsLabel.setText("FPS: N/A")
            self.frameTimeLabel.setText("Frame Time: N/A")

    def cv2_to_qt(self, cv_img):
        if cv_img is None:
            return QtGui.QPixmap()
        height, width, channel = cv_img.shape
        bytes_per_line = 3 * width
        q_img = QtGui.QImage(cv_img.data, width, height, bytes_per_line, QtGui.QImage.Format.Format_BGR888)
        pixmap = QtGui.QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(self.cameraResolution[0], self.cameraResolution[1], QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        return scaled_pixmap
    
    

# main application class

class MainApp(QtWidgets.QMainWindow):
    """ 
    Doet: 
    - Object-ID-tracking
    - Detecties converteren naar kaartformaat
    - De kaartweergave bijwerken
    """
    
    def __init__(self):
        super().__init__()
        #self.setWindowTitle("Main Application")
        #self.setGeometry(100, 100, 800, 600)
        # hier komt alleen die map met punten
        # Load UI file
        ui_file_path = os.path.join(os.path.dirname(__file__), "MainWindow.ui")
        if not os.path.exists(ui_file_path):
            ui_file_path = os.path.join("elements", "MainWindow.ui")
        
        loader = QUiLoader()
        ui_file = QFile(ui_file_path)
        if not ui_file.open(QFile.ReadOnly):
            raise RuntimeError(f"Failed to open UI file: {ui_file_path}")
        
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        
        if self.ui is None:
            raise RuntimeError(f"Failed to load UI from: {ui_file_path}")
        
        # Set the loaded widget as central widget
        self.setCentralWidget(self.ui)
        
        # Set window properties
        self.setWindowTitle("Main Application")
        self.resize(1200, 800)
        
        # Find the main content area container from UI
        main_content_container = self.ui.findChild(QtWidgets.QWidget, "mainContentArea")
        if not main_content_container:
            raise RuntimeError("Could not find 'mainContentArea' widget in UI file")
        
        # Create and add main content area
        self.main_content = MainContentArea(main_content_container)
        main_content_layout = QtWidgets.QVBoxLayout(main_content_container)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.addWidget(self.main_content)
        
        # Create and add right sidebar (on top of everything)
        # Sidebar needs to be a child of the UI widget
        self.sidebar = RightOffCanvas(self.ui, width=280)
        self.sidebar.raise_()
        
        # Camera and model references
        self.cameraL = None
        self.cameraR = None
        self.aimodel = None
        
        # Timer for updating map with detected objects
        self.map_update_timer = QtCore.QTimer(self)
        self.map_update_timer.timeout.connect(self._update_map_from_detections)
        
        # Object tracking data
        self._object_id_map = {}  # Maps (xL, yL) to object_id
        self._next_object_id = 1
        self.tracks = {} # Centralized tracking state: id -> {id, label, current_pos, history}

        # Install event filter to handle resize events
        self.ui.installEventFilter(self)

        #alarm state (single source of truth)
        self.alarm_muted = False
        self.alarm_active = False          # derived from detections

        self.alarm_should_sound = False    # derived from alarm_active and alarm_muted
        self._prev_alarm_should_sound = False

        #keyboard shortcuts(m)
        self.toggle_alarm_action = QAction("Toggle alarm mute", self)
        self.toggle_alarm_action.setShortcut("M")
        self.toggle_alarm_action.triggered.connect(self.toggle_alarm_mute)
        
        self.addAction(self.toggle_alarm_action)

        if self.sidebar and self.sidebar.btn_alarm:
            self.sidebar.btn_alarm.clicked.connect(self.on_alarm_button_clicked)

        self.filter_state = {
            "drones": True,
            "ships": True,
            "unknown": False,
            "trails": True,
        }

        sb = self.sidebar
        if sb:
            sb.cb_drones.toggled.connect(
                lambda v: self.on_filter_toggled("drones", v)
            )
            sb.cb_ships.toggled.connect(
                lambda v: self.on_filter_toggled("ships", v)
            )
            sb.cb_unknown.toggled.connect(
                lambda v: self.on_filter_toggled("unknown", v)
            )
            sb.cb_trails.toggled.connect(
                lambda v: self.on_filter_toggled("trails", v)
            )


        self.ALARM_CLASSES = {"drone", "ship", "boat", "chair"}
        
        self.alarm_sound = QSoundEffect(self)

        sound_path = os.path.join(os.path.dirname(__file__), "res", "alarm.wav")
        self.alarm_sound.setSource(QUrl.fromLocalFile(sound_path))

        if not self.alarm_sound.source().isValid():
            print("Warning: alarm sound file not found or invalid")

        self.alarm_sound.setLoopCount(QSoundEffect.Infinite.value)
        self.alarm_sound.setVolume(0.5)

        #test the alarm sound without camera
        #self.test_alarm(True)   # should start looping sound
        #self.test_alarm(False)  # should stop sound
    

    def on_filter_toggled(self, key: str, enabled: bool):
        self.filter_state[key] = enabled
        print(f"[FILTER] {key} = {enabled}")


    def test_alarm(self, active: bool):
        self.alarm_active = active
        self._update_alarm_sound()

    def on_alarm_button_clicked(self):
        self.toggle_alarm_mute()

    def toggle_alarm_mute(self):
        self.alarm_muted = not self.alarm_muted

        if self.sidebar:
            self.sidebar.set_alarm_muted(self.alarm_muted)

        self._update_alarm_sound()


    def _update_alarm_sound(self):
        # derive should-sound
        self.alarm_should_sound = self.alarm_active and not self.alarm_muted


        # edge detection
        if self.alarm_should_sound and not self._prev_alarm_should_sound:
            # ENTER sound state
            self.alarm_sound.play()

        elif not self.alarm_should_sound and self._prev_alarm_should_sound:
            # EXIT sound state
            self.alarm_sound.stop()

        # update memory ONCE
        self._prev_alarm_should_sound = self.alarm_should_sound

        if self.sidebar:
            if self.alarm_active:
                self.sidebar.start_alarm_pulse()
            else:
                self.sidebar.stop_alarm_pulse()
    
    def setup_cameras(self, cameraL, cameraR, aimodel):
      """Setup cameras and AI model. Delegates camera setup to CameraView."""
        self.cameraL = cameraL
        self.cameraR = cameraR
        self.aimodel = aimodel
        
        # Delegate camera view setup to the CameraView widget
        if self.main_content and hasattr(self.main_content, 'camera_view'):
            self.main_content.camera_view.setup_cameras(cameraL, cameraR, aimodel)
        
        # Start map update timer 
        self.map_update_timer.start(100)  # Update map every 100ms
    
    def _are_cameras_available(self):
        
        if not (self.cameraL and self.cameraR):
            return False
        
        if not (hasattr(self.cameraL, 'cam') and hasattr(self.cameraR, 'cam')):
            return False
        
        if not (self.cameraL.cam and self.cameraR.cam):
            return False
        
        return self.cameraL.cam.isOpened() and self.cameraR.cam.isOpened()
    
    # Helper for coordinate conversion
    def _pixel_to_meter(self, x, depth):
        """Convert pixel x-coordinate and depth to lateral meters."""
        if depth <= 0 or depth == float('inf'):
            return 0
            
        camera_resolution = (1280, 720)
        fov_deg = 60
        cam_center_x = camera_resolution[0] / 2
        
        fov_rad = math.radians(fov_deg)
        focal_length = camera_resolution[0] / (2 * math.tan(fov_rad / 2))
        
        pixel_offset_x = x - cam_center_x
        lateral_angle = math.atan2(pixel_offset_x, focal_length)
        lateral = depth * math.sin(lateral_angle)
        return lateral

    
    def _update_map_from_detections(self):
        """Update map with detected objects from AI model."""

        
        """# Testing with fake object
        if self.aimodel is None:
            # Create/Update fake object track
            fake_id = 999
            
            # Simple circular motion for testing trails
            import time
            t = time.time()
            fake_x_meter = 2.0 * math.sin(t)
            fake_depth = 5.0 + 1.0 * math.cos(t)
            
            if fake_id not in self.tracks:
                self.tracks[fake_id] = {
                    'id': fake_id,
                    'label': 'drone',
                    'history': []
                }
            
            # Add to history
            track = self.tracks[fake_id]
            track['current_pos'] = (fake_x_meter, fake_depth)
            track['history'].append((fake_x_meter, fake_depth, 'drone', fake_depth))
            if len(track['history']) > 20:
                track['history'].pop(0)

            # Apply filtering logic (same as real camera path)
            visible_tracks = []
            for track in self.tracks.values():
                label = track["label"]
                if label == "drone" and not self.filter_state["drones"]:
                    continue
                if label == "ship" and not self.filter_state["ships"]:
                    continue
                if label not in ("drone", "ship") and not self.filter_state["unknown"]:
                    continue
                visible_tracks.append(track)

            # Send tracks to map view
            if self.main_content and hasattr(self.main_content, 'map_view'):
                self.main_content.map_view.update_object_positions(visible_tracks)
                
                # Apply trails filter
                if hasattr(self.main_content.map_view, "set_trails_enabled"):
                    self.main_content.map_view.set_trails_enabled(
                        self.filter_state["trails"]
                    )

            # Update alarm state
            self.alarm_active = track['label'] in self.ALARM_CLASSES
            self._update_alarm_sound()
            return """
        # Check if cameras are available
        if not self._are_cameras_available() or not self.aimodel:
            return
               
        try:
            # Get frames
            frameL = self.cameraL.get_frame() 
            frameR = self.cameraR.get_frame() 
            
            if frameL is None or frameR is None:
                return
            
            # Use AIModel's get_detections method
            detections = self.aimodel.get_detections(frameL, frameR)
            
            # Match new detections to existing tracks or create new ones
            bound_pairs = detections['bound_pairs']
            current_track_ids = set()
            match_threshold = 50  # pixels (matching logic still uses pixels for now)
            
            for pair in bound_pairs:
                (xL, yL), (xR, yR), cls_id, class_name, confidence, distance = pair
                
                if distance == float('inf') or distance <= 0:
                    continue
                
                # Convert to meters
                lateral = self._pixel_to_meter(xL, distance)
                forward = distance
                
                # Find or create object ID
                obj_id = self._get_or_create_object_id((xL, yL), match_threshold)
                current_track_ids.add(obj_id)
                
                # Create track if not exists
                if obj_id not in self.tracks:
                    self.tracks[obj_id] = {
                        'id': obj_id,
                        'label': class_name,
                        'history': []
                    }
                
                # Update track data
                track = self.tracks[obj_id]
                # Always update label from source of truth
                track['label'] = class_name 
                track['current_pos'] = (lateral, forward)
                track['history'].append((lateral, forward, class_name, distance))
                
                # Limit history
                if len(track['history']) > 20:
                    track['history'].pop(0)

            # 2. Cleanup stale tracks
            start_ids = list(self.tracks.keys())
            stale_ids = [tid for tid in start_ids if tid not in current_track_ids]
            
            for tid in stale_ids:
                del self.tracks[tid]
            
            # 3. Cleanup pixel-based tracking map
            self._cleanup_stale_objects(bound_pairs, match_threshold)

            # 4. Update map view
            if self.main_content and hasattr(self.main_content, 'map_view'):
                
                visible_tracks = []
                for track in self.tracks.values():
                    label = track["label"]

                    if label == "drone" and not self.filter_state["drones"]:
                        continue
                    if label == "ship" and not self.filter_state["ships"]:
                        continue
                    if label not in ("drone", "ship") and not self.filter_state["unknown"]:
                        continue

                    visible_tracks.append(track)

                self.main_content.map_view.update_object_positions(visible_tracks)

            if hasattr(self.main_content.map_view, "set_trails_enabled"):
                self.main_content.map_view.set_trails_enabled(
                    self.filter_state["trails"]
                )


            
            # Update alarm state
            self.alarm_active = any(
                track['label'] in self.ALARM_CLASSES
                for track in self.tracks.values()
            )

            self._update_alarm_sound()
                
        except Exception as e:
            # Silently handle errors to avoid spam
            pass


    def _get_or_create_object_id(self, position, match_threshold):
        """Get existing object ID or create new one based on position matching."""
        xL, yL = position
        
        # Try to match with existing object
        for (prev_x, prev_y), prev_id in self._object_id_map.items():
            if abs(prev_x - xL) < match_threshold and abs(prev_y - yL) < match_threshold:
                # Update position and return existing ID
                del self._object_id_map[(prev_x, prev_y)]
                self._object_id_map[(xL, yL)] = prev_id
                return prev_id
        
        # Create new ID
        new_id = self._next_object_id
        self._next_object_id += 1
        self._object_id_map[(xL, yL)] = new_id
        return new_id
      
    def _cleanup_stale_objects(self, bound_pairs, match_threshold):
        """Remove object IDs for positions that are no longer detected."""
        current_positions = {(pair[0][0], pair[0][1]) for pair in bound_pairs}
        
        if not current_positions:
            return
        
        # Find positions to remove
        positions_to_remove = []
        for pos in self._object_id_map.keys():
            is_close = any(
                abs(pos[0] - xL) < match_threshold and abs(pos[1] - yL) < match_threshold
                for (xL, yL) in current_positions
            )
            if not is_close:
                positions_to_remove.append(pos)
        
        # Remove stale positions
        for pos in positions_to_remove:
            del self._object_id_map[pos]

    def eventFilter(self, obj, event):
        """Handle resize events to update sidebar position."""
        if obj == self.ui and event.type() == event.Type.Resize:
            self.sidebar.reposition()
        return super().eventFilter(obj, event)

# stereo camera class
class StereoCamera:
    def __init__(self, index, resolution):
        self.cam = cv2.VideoCapture(index)
        if not self.cam.isOpened():
            print(f"Camera {index} failed to open")
            return None
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        self.cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cam.set(cv2.CAP_PROP_FPS, 10.0)
        self.cam.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        print(f"Stereo Camera {index} initialized.")
        
    def get_frame(self):
        ret, frame = self.cam.read()
        if not ret:
            print("Failed to grab frame")
            return None
        # cv2.initUndistortRectifyMap(frame, None, None, None, (frame.shape[1], frame.shape[0]), cv2.CV_32FC1)
        # cv2.remap(frame, None, None, cv2.INTER_LINEAR)
        # frame = cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_LINEAR)
        return frame
    
   
    
class AIModel:
    def __init__(self, screen_resolution):
        self.model = YOLO(model="./yolo11n.onnx", task="detect")  # load a model
        self.confidence_threshold = 0.8
        self.distance_threshold = 200  # in pixels
        self.screen_resolution = screen_resolution

    def get_detections(self, frameL, frameR):

        # Run YOLO detection on both frames
            results = [
                self.model(frameL, verbose=False, conf=self.confidence_threshold),
                self.model(frameR, verbose=False, conf=self.confidence_threshold)
            ]
            
            # Extract objects from both cameras
            objects_left = self._extract_objects(results[0], include_metadata=True)
            objects_right = self._extract_objects(results[1], include_metadata=False)
            
            # Bind objects between cameras
            positions_left = [(x, y) for (x, y, *_) in objects_left]
            positions_right = [(x, y) for (x, y, *_) in objects_right]
            bound_pairs_positions = self.bind_objects(positions_left, positions_right)
            
            # Enrich bound pairs with metadata and distance
            bound_pairs = []
            for pair in bound_pairs_positions:
                (xL, yL), (xR, yR) = pair[0], pair[1]
                
                # Find metadata from objects_left
                metadata = next(
                    ((cls_id, class_name, confidence, bbox)
                    for (x, y, cls_id, class_name, confidence, bbox) in objects_left
                    if x == xL and y == yL),
                    (0, 'unknown', 0.5, None)
                )
                cls_id, class_name, confidence, bbox = metadata
                
                # Calculate distance
                distance = self.get_distance(xL, xR)
                
                bound_pairs.append(((xL, yL), (xR, yR), cls_id, class_name, confidence, distance))
            
            return {
                'objects_left': objects_left,
                'objects_right': objects_right,
                'bound_pairs': bound_pairs,
                'results': results
            }
    def _extract_objects(self, results, include_metadata=True):
     
        objects = []
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                bbox = (int(x1), int(y1), int(x2), int(y2))
                
                if include_metadata:
                    cls_id = int(box.cls[0].cpu().numpy())
                    class_name = r.names[cls_id] if hasattr(r, 'names') else 'unknown'
                    confidence = float(box.conf[0].cpu().numpy())
                    objects.append((cx, cy, cls_id, class_name, confidence, bbox))
                else:
                    objects.append((cx, cy, bbox))
        
        return objects
   
    # veranderen zodat het de middelpunten van die boxes pakt van beide cameras
    # kijken of we de frames kunnen overlappen en daar een vast object uit kunnen halen
    def predict(self, captures):
        # Get detections without modifying frames
        detections = self.get_detections(captures[0], captures[1])
        
        # Draw visualizations on frames
        self._draw_detections(captures[0], detections['objects_left'], is_left=True)
        self._draw_detections(captures[1], detections['objects_right'], is_left=False)
        self._draw_bound_pairs(captures, detections['bound_pairs'])
        
        return captures[0], captures[1]
    def _draw_detections(self, frame, objects, is_left=True):
        color = (0, 255, 0) if is_left else (0, 0, 255)
        
        for obj in objects:
            cx, cy = obj[0], obj[1]
            bbox = obj[-1]  # Last element is always bbox
            
            if bbox:
                x1, y1, x2, y2 = bbox
                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 1)
                # Draw center point
                cv2.circle(frame, (cx, cy), 4, color, -1)
    
    def _draw_bound_pairs(self, captures, bound_pairs):
        for pair in bound_pairs:
            (xL, yL), (xR, yR), cls_id, class_name, confidence, distance = pair
            
            # Draw connection lines on both frames
            cv2.line(captures[0], (xL, yL), (xR, yR), (255, 255, 0), 1)
            cv2.line(captures[1], (xL, yL), (xR, yR), (255, 255, 0), 1)
            
            # Draw distance text on right frame
            if distance != float('inf'):
                cv2.putText(
                    captures[1], 
                    f"{distance:.2f}m", 
                    (xL, yL - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1, 
                    (0, 255, 255), 
                    2
                )
    
    def bind_objects(self, objectsL, objectsR):
        #! ergens een buffer plaatsen voor als er geen object in 1 van de cameras is
        
        detectedObjects = []
        
        for (x1, y1) in objectsL:
                closest_obj = None
                closest_dist = float('inf')
                for (x2, y2) in objectsR:
                    dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                    if dist < closest_dist and dist < self.distance_threshold:  # threshold of 150 pixels
                        closest_dist = dist
                        closest_obj = (x2, y2)
                if closest_obj is not None:
                    detectedObjects.append([(x1, y1), closest_obj])
                    
        return detectedObjects
    
    # werkt blijkbaar
    def get_distance(self, x1, x2):
        baseline = 0.099    # distance between the two cameras in meters
        # fx = 1063.9      # focal length in pixels
        width_px = self.screen_resolution[0]    # camera resolution width in pixels
        fov_deg = 60        # camera field of view in degrees

        theta_rad = math.radians(fov_deg)
        # f = (width_px / 2) / math.tan(theta_rad / 2)
        f = width_px / (2 * math.tan(theta_rad / 2))

        disparity = x1 - x2
        if abs(disparity) < 0.001:
            return float('inf')
        
        distance = (f * baseline) / disparity
        return abs(distance) 

    
    

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    #window = DebugWindow()
    main_window = MainApp()

    # Initialize cameras and AI model
    cameraL = None
    cameraR = None
    aimodel = None
    
    try:
        camera_resolution = (1280, 720)
        cam_ids = (0, 2)  # raspberry pi
       
        
        aimodel = AIModel(camera_resolution)
        cameraL = StereoCamera(cam_ids[1], camera_resolution)
        cameraR = StereoCamera(cam_ids[0], camera_resolution)
        
        print("Het Systeem werkt goed")
    except Exception as e:
        print(f"Warning: Kan camera's niet initialiseren {e}")

    main_window.setup_cameras(cameraL, cameraR, aimodel)
    main_window.show()
    sys.exit(app.exec())