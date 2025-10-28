# TODO:
# multi-threading
# diepte kaart
# stereo camera support
# 2d punt krijgen
# 2d punt op "map" projecteren
# GUI
# verschil tussen cpu en gpu verwerking meten (?)
# kijken naar resoluties,fps waardes en compressie
# configuratie bestand voor instellingen
# synchronisatie tussen twee camera's
# niet real-time iets tekenen/zien maar per aantal frames updaten
# logging en debugging
# error handling
# code opschonen en documenteren

# toggle debug cameras on/off

from picamera2 import Picamera2
import numpy as np
import threading
import time
import cv2
import sys
import os

from PyQt6 import QtCore, QtWidgets, QtGui, uic
from PyQt6.QtCore import QTimer




# debug window class

class DebugWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(DebugWindow, self).__init__()
        uic.loadUi(os.path.join("elements", "DebugWindow.ui"), self)
        self.setWindowTitle("Debug Window")

        self.cameraResolution = (1280, 720)
        
        self.camL.setMinimumSize(self.cameraResolution[0], self.cameraResolution[1])
        self.camR.setMinimumSize(self.cameraResolution[0], self.cameraResolution[1])

        self.camera1 = StereoCamera(0, self.cameraResolution)
        self.camera2 = StereoCamera(1, self.cameraResolution)

        self.timer = QTimer()
        self.timer.timeout.connect(self.start_capture)
        self.timer.start(1)  # Update every 1 ms

    def start_capture(self):
        capture1 = self.camera1.get_frame()
        capture2 = self.camera2.get_frame()
        
        self.camL.setPixmap(self.cv2_to_qt(capture1))
        self.camR.setPixmap(self.cv2_to_qt(capture2))
        
    def cv2_to_qt(self, cv_img):
        height, width, channel = cv_img.shape
        bytes_per_line = 3 * width
        q_img = QtGui.QImage(cv_img.data, width, height, bytes_per_line, QtGui.QImage.Format.Format_BGR888)
        pixmap = QtGui.QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(self.cameraResolution[0], self.cameraResolution[1], QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        return scaled_pixmap
        
        
        
        


# main application class

# sterio camera class

class StereoCamera:
    def __init__(self, index, resolution):
        self.index = index
        self.camera = Picamera2(self.index)
        self.config = self.camera.create_preview_configuration(
            main={"format": "RGB888", "size": resolution}
        )
        self.camera.configure(self.config)
        self.camera.start()
        print(f"Stereo Camera {self.index} initialized.")
        
    def get_frame(self):
        frame = self.camera.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        # frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)
        return frame
        
            
            
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = DebugWindow()
    window.show()
    sys.exit(app.exec())