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

        self.cameraL = StereoCamera(self.camIds[1], self.cameraResolution)
        self.cameraR = StereoCamera(self.camIds[0], self.cameraResolution)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.start_capture)
        self.timer.start(10)  # Update every X ms

    def start_capture(self):
        time_start = time.time()
        captureL, captureR = self.model.predict([self.cameraL.get_frame(), self.cameraR.get_frame()])
        time_end = time.time()

        self.update_metrics(time_start, time_end)

        self.camL.setPixmap(self.cv2_to_qt(captureL))
        self.camR.setPixmap(self.cv2_to_qt(captureR))
        
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
        self.cam.set(cv2.CAP_PROP_AUTOFOCUS, 1)
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
        self.confidence_threshold = 0.6

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
                
        # self.bind_objects(objects[0], objects[1])
          
        return captures[0], captures[1], objects
    
    def bind_objects(self, objectsL, objectsR):
        #! ergens een buffer plaatsen voor als er geen object in 1 van de cameras is
        # voor elk object in left camera, kijk naar het dichtsbijzijnde object in de right camera
        # gebruik waarde die uit offset komt
        # return een lijst van tuples met gekoppelde objecten
        pass
    
    # hoeft maar eenmalig te runnen
    def get_offset(self):
        
        camL = StereoCamera(0, (1920, 1080))
        camR = StereoCamera(2, (1920, 1080))
        
        model = AIModel()
        
        while True:
            frameL = camL.get_frame()
            frameR = camR.get_frame()
            
            frameL, frameR, objects = model.predict([frameL, frameR])
            
            detectedObjects = []
            
            # find closest objects within a certain threshold and draw lines between them
            for (x1, y1) in objects[0]:
                closest_obj = None
                closest_dist = float('inf')
                for (x2, y2) in objects[1]:
                    dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                    if dist < closest_dist and dist < 150:  # threshold of 100 pixels
                        closest_dist = dist
                        closest_obj = (x2, y2)
                if closest_obj is not None:
                    cv2.line(frameL, (x1, y1), closest_obj, (0, 255, 255), 1)
                    cv2.line(frameR, closest_obj, (x1, y1), (0, 255, 255), 1)
                    detectedObjects.append([(x1, y1), closest_obj])
            
            
            # for (x1, y1) in objects[1]:
            #     closest_obj = None
            #     closest_dist = float('inf')
            #     for (x2, y2) in objects[0]:
            #         dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
            #         if dist < closest_dist:
            #             closest_dist = dist
            #             closest_obj = (x2, y2)
            #     if closest_obj is not None:
            #         cv2.line(frameL, (closest_obj[0], closest_obj[1]), (x1, y1), (0, 255, 255), 1)
            #         cv2.line(frameR, (x1, y1), closest_obj, (0, 255, 255), 1)
            #         detectedObjects.append([(closest_obj[0], closest_obj[1]), (x1, y1)])
                    
            for ((xL, yL), (xR, yR)) in detectedObjects:
                distance = self.get_distance(xL, xR)
                cv2.putText(frameL, f"{distance:.2f}m", (xL, yL - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 1)
                cv2.putText(frameR, f"{distance:.2f}m", (xR, yR - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 1)
                
            
            blended = cv2.addWeighted(frameR, 0.5, frameL, 1 - 0.5, 0)
            cv2.imshow('Blended', blended)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # maak 
        pass
    
    # werkt blijkbaar
    def get_distance(self, x1, x2):
        baseline = 0.099    # distance between the two cameras in meters
        width_px = 1920     # camera resolution width in pixels
        fov_deg = 60        # camera field of view in degrees

        theta_rad = math.radians(fov_deg)
        f = (width_px / 2) / math.tan(theta_rad / 2)
        # f = width_px / (2 * math.tan(theta_rad / 2))

        disparity = x1 - x2
        if abs(disparity) < 0.001:
            return float('inf')
        
        distance = (f * baseline) / disparity
        return abs(distance)

    
    
    
# if __name__ == "__main__":
#     app = QtWidgets.QApplication(sys.argv)
#     window = DebugWindow()
#     window.show()
#     sys.exit(app.exec())

if __name__ == "__main__":
    model = AIModel()
    model.get_offset()