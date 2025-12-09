# TODO:
# multi-threading (?)
# diepte kaart
#? stereo camera support 
# 2d punt krijgen
# 2d punt op "map" projecteren
# GUI
# verschil tussen cpu en gpu verwerking meten (?, de AI draait op cpu dus :shrug:)
#? kijken naar resoluties,fps waardes en compressie
# logging en debugging (gebeurt technisch gezien al hierboven)
# configuratie bestand voor instellingen (kan handig zijn gezien we 2 windows gaan hebben) 
# synchronisatie tussen twee camera's (is er al lijkt mij)
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
        self.model = AIModel()
        
        self.cameraResolution = (1920, 1080)
        self.camIds = (0, 2) # raspberry pi
        # self.camIds = (4, 2) # laptop

        self.ui.setParent(self)
        self.ui.setMinimumWidth(self.cameraResolution[0] * 2 + 50)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        self.setWindowTitle("Debug Window")

        self.camL = self.ui.findChild(QtWidgets.QLabel, "camL")
        self.camR = self.ui.findChild(QtWidgets.QLabel, "camR")
        self.fpsLabel = self.ui.findChild(QtWidgets.QLabel, "fpsLabel")
        self.frameTimeLabel = self.ui.findChild(QtWidgets.QLabel, "frameTimeLabel")
        
        self.camL.setMinimumSize(self.cameraResolution[0], self.cameraResolution[1])
        self.camL.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.camL.setScaledContents(True)
        
        self.camR.setMinimumSize(self.cameraResolution[0], self.cameraResolution[1])
        self.camR.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.camR.setScaledContents(True)

        self.camera1 = StereoCamera(self.camIds[1], self.cameraResolution)
        self.camera2 = StereoCamera(self.camIds[0], self.cameraResolution)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.start_capture)
        self.timer.start(10)  # Update every X ms

    def start_capture(self):
        time_start = time.time()
        capture1 = self.model.predict(self.camera1.get_frame())
        capture2 = self.model.predict(self.camera2.get_frame())
        time_end = time.time()

        self.update_metrics(time_start, time_end)

        self.camL.setPixmap(self.cv2_to_qt(capture1))
        self.camR.setPixmap(self.cv2_to_qt(capture2))
        
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
        self.setWindowTitle("Main Application")
        self.setGeometry(100, 100, 800, 600)
        # hier komt alleen die map met punten

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
        self.cam.set(cv2.CAP_PROP_FPS, 20.0)
        self.cam.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        self.cam.set(cv2.CAP_PROP_FOCUS, 10)
        print(f"Stereo Camera {index} initialized.")
        
    def get_frame(self):
        ret, frame = self.cam.read()
        if not ret:
            print("Failed to grab frame")
            return None
        return frame
    
   
    
class AIModel:
    def __init__(self):
        self.model = YOLO(model="./yolo11n_ncnn_model", task="detect")  # load a model

    def predict(self, capture): 
                   
        results = self.model(capture, verbose=False, conf=0.8)
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                
                cv2.circle(capture, (cx, cy), 4, (0, 255, 0), -1)
                distance = self.get_distance(x1, x2)
                cv2.putText(capture, f"D: {distance:.2f}m", (cx + 10, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            capture = r.plot()
            
        return capture
    
    def get_distance_2(self, x1, x2):
        
        # 101.3721 uit online calc
        # 83 diagonaal
        # 73 horizontal
        # 50 vertical
        
        theda_rad = math.radians(101.3721)
        disparity = (x1 - x2) if (x1 - x2) != 0 else 0.01  # prevent division by zero
        distance = (0.06 * 1280) / (2 * math.tan(theda_rad / 2) * disparity)
        # D = (9.8267716535 * 0.06) / disparity

        return distance
    
    def get_distance(self, x1, x2):
        baseline = 0.06
        width_px = 1920
        fov_deg = 73

        theta_rad = math.radians(fov_deg)
        f = width_px / (2 * math.tan(theta_rad / 2))

        disparity = x1 - x2
        if abs(disparity) < 0.001:
            return float('inf')
        
        distance = (f * baseline) / disparity
        return abs(distance)

    

# resolution options helper function (moet nog verder uitgewerkt worden)
def getResolution(resolution):
    options = [
        (640, 480),
        (1280, 720),
        (1920, 1080),
        (2560, 1440),
        (3840, 2160)
    ]
    if resolution not in options:
        options.insert(0, resolution)
        return options
    return options[resolution]

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = DebugWindow()
    window.show()
    sys.exit(app.exec())