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

# from cv2_enumerate_cameras import enumerate_cameras
# from ultralytics import YOLO
import numpy as np
import math
import yaml
import time
import cv2
import sys
import os

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, QUrl
from PySide6.QtGui import QAction, QKeySequence, QPixmap
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QLabel

from elements.SideBar import RightOffCanvas
from elements.TearOffTabs import TearOffTabManager
from elements.CameraView import CameraView
from elements.MapView import MapView

# main application class

class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        # load yaml config
        with open("config.yaml", 'r') as file:
            self.config = yaml.safe_load(file)
        
        # initialize main window
        super(MainApp, self).__init__()
        self.setWindowTitle("Stereo Camera Object Detection")
        self.setGeometry(0, 0, self.config['UiResolution']['width'], self.config['UiResolution']['height'])
        self.setStyleSheet("background: #2c3e50;")
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Main content area widget
        self.mainContentArea = QWidget()
        self.mainContentArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mainContentArea.layout = QVBoxLayout(self.mainContentArea)
        self.mainContentArea.layout.setSpacing(0)
        self.mainContentArea.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.mainContentArea)
        self.setCentralWidget(self.mainContentArea)
        
        # company logo
        self.company_logo = QLabel(self)
        self.company_logo.setScaledContents(True)
        self.company_logo.setFixedSize(140, 44)
        logo_path = os.path.join("imgs", "Logo-Tidalis.jpg")
        if os.path.exists(logo_path):
           self.company_logo.setPixmap(QPixmap(logo_path))
           self.company_logo.show()
        else:
           print(f"Warning: Logo not found at {logo_path}")
           self.company_logo = None
                
        # sidebar
        self.sidebar = RightOffCanvas(self, width=280)
        # self.sidebar.raise_()
        
        # Create tear off tab manager
        self.tab_manager = TearOffTabManager(self.mainContentArea)
        
        # Create camera and map views
        self.camera_view = CameraView()
        self.map_view = MapView()
    
        self.tab_manager.add_view("Camera", self.camera_view)
        self.tab_manager.add_view("Map", self.map_view)
        self.mainContentArea.layout.addWidget(self.tab_manager)
        
        
        # setup stereo camera
        cameraName = self.config['cameraName']
        cameraIDs = getCameraId(cameraName)
        
        self.cameraL = StereoCamera(cameraIDs[0], self.config)
        self.cameraR = StereoCamera(cameraIDs[1], self.config)
        
        # timer for capture updates
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.start_capture)
        self.timer.start(self.config['UiRefreshRate'])  # Update every X ms
        

    def start_capture(self):
        pass
    
    def update_metrics(self):
        pass
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.company_logo:
            self.company_logo.move(self.width() - self.company_logo.width() - 10, 0)
            self.company_logo.raise_()
        if self.sidebar:
            self.sidebar.reposition()
            self.sidebar.raise_()


# stereo camera class
class StereoCamera:
    def __init__(self, index, config=None):
        self.cam = cv2.VideoCapture(index, cv2.CAP_V4L2)
        if not self.cam.isOpened():
            print(f"Camera {index} failed to open")
            return None
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, config['resolution']['width'])
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, config['resolution']['height'])
        self.cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cam.set(cv2.CAP_PROP_FPS, config['cameraFPS'])
        self.cam.set(cv2.CAP_PROP_AUTOFOCUS, config['cameraAutoFocus'])
        print(f"Stereo Camera {index} initialized.")
        
    def get_frame(self):
        ret, frame = self.cam.read()
        if not ret:
            print("Failed to grab frame")
            return None
        return frame
    
def getCameraId():
    cameraName = "Arducam"
    cameraIDs = []
    
    for camera_info in enumerate_cameras():
        if cameraName.lower() in camera_info.name.lower():
            if int(str(camera_info.index)[-1]) not in cameraIDs:
                cameraIDs.append(int(str(camera_info.index)[-1]))
        else:
            print(f"Camera '{camera_info.name}' does not match the specified name '{cameraName}'.")
        
    print(cameraIDs)
    return cameraIDs
   
    
class AIModel:
    def __init__(self, screen_resolution):
        self.convertToOnnx()
        # try catch block toevoegen
        self.model = YOLO(model="./yolo11n.onnx", task="detect")  # load a model
        self.model.to("cuda")
        self.confidence_threshold = 0.8
        self.distance_threshold = 200  # in pixels
        self.screen_resolution = screen_resolution
        
    def convertToOnnx(self):
        if not os.path.exists("./yolo11n.onnx"):
            print("exporting YOLO model to ONNX format...")
            os.system("yolo export model=./yolo11n.pt format=onnx simplify=True")
            print("ONNX model done")
        print("ONNX model already exists.")

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
                    if dist < closest_dist and dist < self.distance_threshold:
                        closest_dist = dist
                        closest_obj = (x2, y2)
                if closest_obj is not None:
                    detectedObjects.append([(x1, y1), closest_obj])
                    
        return detectedObjects
    

    def get_distance(self, x_left, x_right):
        fx = 1052.42              # uit camera 0 intrinsic
        baseline = 0.1026         # meters, uit ||T||

        disparity = x_left - x_right
        if abs(disparity) < 0.5:
            return float('inf')

        distance = (fx * baseline) / disparity
        return abs(distance)

    
    
    
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())
    pass