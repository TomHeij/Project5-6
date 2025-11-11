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

        self.cameraDisplayScale = 1  # scaling factor for camera display size
        self.cameraResolution = (1280, 720)
        self.camIds = (0, 1)
        
        self.camL.setMinimumSize(self.cameraResolution[0], self.cameraResolution[1])
        self.camR.setMinimumSize(self.cameraResolution[0], self.cameraResolution[1])

        self.camera1 = StereoCamera(self.camIds[0], self.cameraResolution)
        self.camera2 = StereoCamera(self.camIds[1], self.cameraResolution)

        self.timer = QTimer()
        self.timer.timeout.connect(self.start_capture)
        self.timer.start(1)  # Update every 1 ms

    def start_capture(self):
        time_start = time.time()
        capture1, coords1 = self.camera1.get_frame()
        capture2, coords2 = self.camera2.get_frame()
        time_end = time.time()

        self.update_metrics(time_start, time_end)
        self.get_distance(coords1, coords2)
        

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
        display_height = int(self.cameraResolution[1] * self.cameraDisplayScale)
        display_width = int(self.cameraResolution[0] * self.cameraDisplayScale)
        scaled_pixmap = pixmap.scaled(display_width, display_height, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        return scaled_pixmap

    def get_distance(self, coords_left, coords_right):

        # model een center punt geven in obejct box
        # center punt naar 2d coördinaten omzetten
        for (x1, y1), (x2, y2) in zip(coords_left, coords_right):
            
            # 101.3721 uit online calc
            # 83 diagonaal
            # 73 horizontal
            # 50 vertical
            
            distance = (0.06 * self.cameraResolution[0]) / ( 2*(np.tan(np.degrees(83)/2)) * (x1 - x2) )
            print(f"Distance between points ({x1}, {y1}) and ({x2}, {y2}): {distance:.2f} meters")


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
        self.model = YOLO("./yolo11n_ncnn_model")  # load a model
        self.camera = Picamera2(self.index)
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
        results = self.model(frame, stream=True, verbose=False, conf=0.5)
        # 1 frame returnen ?
        coords = []
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                coords.append((cx, cy))
                # print(f"Camera {self.index} detected object at ({cx}, {cy})")
                
                cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
            
            frame = r.plot()
        
        return frame, coords
    
    


# resolution options helper function (moet nog verder uitgewekt worden)
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