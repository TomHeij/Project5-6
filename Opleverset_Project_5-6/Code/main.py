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
from PySide6.QtCore import QFile


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
    def __init__(self):
        super(MainApp, self).__init__()
        #self.setWindowTitle("Main Application")
        #self.setGeometry(100, 100, 800, 600)
        # hier komt alleen die map met punten
        # Load UI file
        ui_file_path = os.path.join(os.path.dirname(__file__), "MainWindow.ui")
        if not os.path.exists(ui_file_path):
            # Try alternative path
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
        
        # Install event filter to handle resize events
        self.ui.installEventFilter(self)
    
    def _check_cameras_available(self, cameraL=None, cameraR=None):
        """Helper method to check if cameras are available."""
        checkL = cameraL if cameraL is not None else self.cameraL
        checkR = cameraR if cameraR is not None else self.cameraR
        
        if not (checkL and checkR):
            return False
        
        if not (hasattr(checkL, 'cam') and hasattr(checkR, 'cam')):
            return False
        
        if not (checkL.cam and checkR.cam):
            return False
        
        return checkL.cam.isOpened() and checkR.cam.isOpened()
    
    def _update_dummy_data_state(self, cameras_available):
        """Update dummy data state based on camera availability."""
        if not (self.main_content and hasattr(self.main_content, 'map_view')):
            return
        
        if not cameras_available:
            if not self.main_content.map_view.use_dummy_data:
                print("Starting dummy data mode - cameras not available")
                self.main_content.map_view.start_dummy_data()
        else:
            if self.main_content.map_view.use_dummy_data:
                self.main_content.map_view.stop_dummy_data()
    
    def setup_cameras(self, cameraL, cameraR, aimodel):
        """Setup cameras and AI model from main.py."""
        self.cameraL = cameraL
        self.cameraR = cameraR
        self.aimodel = aimodel
        
        # Setup camera view with cameras
        if self.main_content and hasattr(self.main_content, 'camera_view'):
            self.main_content.camera_view.setup_cameras(cameraL, cameraR, aimodel)
        
        # Check if cameras are available and update dummy data state
        cameras_available = self._check_cameras_available(cameraL, cameraR)
        self._update_dummy_data_state(cameras_available)
        
        # Start map update timer (this will check for cameras and use dummy data if needed)
        self.map_update_timer.start(100)  # Update map every 100ms
    
    def _update_map_from_detections(self):
        """Update map with detected objects from AI model."""
        # Check if cameras are available
        cameras_available = self._check_cameras_available()
        
        # Update dummy data state
        self._update_dummy_data_state(cameras_available)
        
        # If cameras not available, return early (dummy data will handle updates)
        if not cameras_available:
            return
        
        try:
            # Get frames
            frameL = self.cameraL.get_frame() if self.cameraL else None
            frameR = self.cameraR.get_frame() if self.cameraR else None
            
            if frameL is None or frameR is None:
                return
            
            # Run detection (without modifying frames for display)
            if not hasattr(self.aimodel, 'model') or self.aimodel.model is None:
                return
                
            results = [
                self.aimodel.model(frameL, verbose=False, conf=self.aimodel.confidence_threshold),
                self.aimodel.model(frameR, verbose=False, conf=self.aimodel.confidence_threshold)
            ]
            
            # Extract object centers with class information
            objects_left = []  # List of (cx, cy, class_id, class_name, confidence)
            objects_right = []  # List of (cx, cy)
            
            # Process left camera results
            for r in results[0]:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    cls_id = int(box.cls[0].cpu().numpy())
                    class_name = r.names[cls_id] if hasattr(r, 'names') else 'unknown'
                    confidence = float(box.conf[0].cpu().numpy())
                    objects_left.append((cx, cy, cls_id, class_name, confidence))
            
            # Process right camera results
            for r in results[1]:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    objects_right.append((cx, cy))
            
            # Bind objects between cameras using AIModel's bind_objects method
            # First, get position-only lists for binding
            positions_left = [(x, y) for (x, y, cls_id, class_name, confidence) in objects_left]
            
            # Use AIModel's bind_objects method (reusing existing logic)
            bound_pairs = self.aimodel.bind_objects(positions_left, objects_right)
            
            # Merge class metadata back with bound pairs
            detected_pairs = []
            for pair in bound_pairs:
                (xL, yL), (xR, yR) = pair[0], pair[1]
                # Find the original object_left entry to get metadata
                for (x, y, cls_id, class_name, confidence) in objects_left:
                    if x == xL and y == yL:
                        detected_pairs.append(((xL, yL), (xR, yR), cls_id, class_name, confidence))
                        break
            
            # Calculate distances and prepare data for map
            map_objects = []
            
            # Track object IDs based on position (simple tracking)
            if not hasattr(self, '_object_id_map'):
                self._object_id_map = {}  # Maps (xL, yL) to object_id
                self._next_object_id = 1
            
            for pair_data in detected_pairs:
                if len(pair_data) == 5:
                    (xL, yL), (xR, yR), cls_id, class_name, confidence = pair_data
                else:
                    (xL, yL), (xR, yR) = pair_data[:2]
                    cls_id = 0
                    class_name = 'unknown'
                    confidence = 0.5
                
                distance = self.aimodel.get_distance(xL, xR)
                if distance != float('inf') and distance > 0:
                    # Try to match with existing object ID (simple position-based tracking)
                    obj_id = None
                    match_threshold = 50  # pixels
                    for (prev_x, prev_y), prev_id in self._object_id_map.items():
                        if abs(prev_x - xL) < match_threshold and abs(prev_y - yL) < match_threshold:
                            obj_id = prev_id
                            # Update position
                            del self._object_id_map[(prev_x, prev_y)]
                            self._object_id_map[(xL, yL)] = obj_id
                            break
                    
                    # If no match found, assign new ID
                    if obj_id is None:
                        obj_id = self._next_object_id
                        self._next_object_id += 1
                        self._object_id_map[(xL, yL)] = obj_id
                    
                    # Create object data dict
                    obj_data = {
                        'id': obj_id,
                        'x': xL,  # Pixel x coordinate (will be converted to meters)
                        'y': yL,  # Pixel y coordinate
                        'depth': distance,  # Stereo depth in meters
                        'label': class_name  # Object class name
                    }
                    map_objects.append(obj_data)
            
            # Clean up old object IDs (objects that are no longer detected)
            current_positions = set()
            for pair_data in detected_pairs:
                if len(pair_data) >= 2:
                    (xL, yL), _ = pair_data[0], pair_data[1]
                    current_positions.add((xL, yL))
            
            # Remove IDs for positions that are no longer detected
            if current_positions:
                positions_to_remove = []
                for pos in self._object_id_map.keys():
                    # Check if this position is close to any current position
                    is_close = any(abs(pos[0] - xL) < 50 and abs(pos[1] - yL) < 50 
                                  for (xL, yL) in current_positions)
                    if not is_close:
                        positions_to_remove.append(pos)
                
                for pos in positions_to_remove:
                    del self._object_id_map[pos]
            
            # Update map view
            if self.main_content and hasattr(self.main_content, 'map_view'):
                self.main_content.map_view.update_object_positions(map_objects)
                
        except Exception as e:
            # Silently handle errors to avoid spam
            pass
    
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

    # veranderen zodat het de middelpunten van die boxes pakt van beide cameras
    # kijken of we de frames kunnen overlappen en daar een vast object uit kunnen halen
    def predict(self, captures):
        results = [self.model(captures[0], verbose=False, conf=self.confidence_threshold), self.model(captures[1], verbose=False, conf=self.confidence_threshold)]
        objects = [[], []]
        
        for result in results:
            for r in result:
                capture = captures[0] if result == results[0] else captures[1]
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    objects[0 if result == results[0] else 1].append((cx, cy))
                    
                    # tekent vierkant om object
                    cv2.rectangle(capture, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 1)
                    
                    # tekent midden punt en afstand
                    if capture is captures[0]:
                        cv2.circle(capture, (cx, cy), 4, (0, 255, 0), -1)
                    else:
                        cv2.circle(capture, (cx, cy), 4, (0, 0, 255), -1)        
                
                capture = r.plot()
                
        detectedObjects = self.bind_objects(objects[0], objects[1])
          
        for ((xL, yL), (xR, yR)) in detectedObjects:
            distance = self.get_distance(xL, xR)
            cv2.line(captures[0], (xL, yL), (xR, yR), (255, 255, 0), 1)
            cv2.line(captures[1], (xL, yL), (xR, yR), (255, 255, 0), 1)
            cv2.putText(captures[1], f"{distance:.2f}m", (xL, yL - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
          
        return captures[0], captures[1]
    
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