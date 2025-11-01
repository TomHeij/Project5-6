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

from picamera2 import Picamera2
from ultralytics import YOLO
import numpy as np
import threading
import time
import cv2
import sys
import os

from PyQt6 import QtCore, QtWidgets, QtGui, uic
from PyQt6.QtCore import QTimer


# debug window class

class DebugWindow(QtWidgets.QWidget):
    def __init__(self):
        super(DebugWindow, self).__init__()
        uic.loadUi(os.path.join("elements", "DebugWindow.ui"), self)
        self.setWindowTitle("Debug Window")

        self.cameraDisplaySize = 0.5  # 50% van de originele resolutie
        self.cameraResolution = (640, 380)
        self.camIds = (0, 1)
        
        self.camL.setMinimumSize(self.cameraResolution[0], self.cameraResolution[1])
        self.camR.setMinimumSize(self.cameraResolution[0], self.cameraResolution[1])

        self.camera1 = StereoCamera(self.camIds[1], self.cameraResolution)
        self.camera2 = StereoCamera(self.camIds[0], self.cameraResolution)

        self.timer = QTimer()
        self.timer.timeout.connect(self.start_capture)
        self.timer.start(1)  # Update every 1 ms

    def start_capture(self):
        time_start = time.time()
        capture1 = self.camera1.get_frame()
        capture2 = self.camera2.get_frame()
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
        height, width, channel = cv_img.shape
        bytes_per_line = 3 * width
        q_img = QtGui.QImage(cv_img.data, width, height, bytes_per_line, QtGui.QImage.Format.Format_BGR888)
        pixmap = QtGui.QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(self.cameraResolution[0] * self.cameraDisplaySize, self.cameraResolution[1] * self.cameraDisplaySize, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
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
        self.index = index
        self.camera = Picamera2(self.index)
        self.model = YOLO("yolo11n_ncnn_model")
        self.config = self.camera.create_preview_configuration(
            main={"format": "BGR888", "size": (resolution[0], resolution[1])}
        )
        self.camera.configure(self.config)
        self.camera.start()
        print(f"Stereo Camera {self.index} initialized.")
        
    def get_frame(self):
        frame = self.camera.capture_array()    
        frame = cv2.flip(frame, -1)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        # frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)    
        
        # results returnen ?
        results = self.model(frame, stream=True)
        # 1 frame returnen ?
        for r in results:
            frame = r.plot()
        
        return frame
        
            
            
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = DebugWindow()
    window.show()
    sys.exit(app.exec())