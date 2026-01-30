from cv2_enumerate_cameras import enumerate_cameras
from ultralytics import YOLO
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
        # load yaml config. exit if not found
        try:
            with open("config.yaml", 'r') as file:
                    self.config = yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading config.yaml: {e}")
            sys.exit(1)
            
        # initialize stereo matcher
        self.stereoMatcher = self.init_stereo_matcher()
        
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
        self.sidebar.raise_()
        
        # Create tear off tab manager
        self.tab_manager = TearOffTabManager(self.mainContentArea)
        
        # Create camera and map views
        self.camera_view = CameraView()
        self.map_view = MapView()
    
        # Add views to tab manager
        self.tab_manager.add_view("Camera", self.camera_view)
        self.tab_manager.add_view("Map", self.map_view)
        self.mainContentArea.layout.addWidget(self.tab_manager)
        
        # AI model
        self.model = AIModel(self.config)
        
        # setup stereo camera
        cameraName = self.config['cameraName']
        cameraIDs = getCameraId(cameraName)
        
        if len(cameraIDs) < 2:
            print("Error: Less than two cameras found with the specified name.")
            sys.exit(1)
        
        self.cameraL = StereoCamera(cameraIDs[0], self.config, mapType='left')
        self.cameraR = StereoCamera(cameraIDs[1], self.config, mapType='right')
        
        # timer for capture updates
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.start_capture)
        self.timer.start(self.config['UiRefreshRate'])  # Update every X ms
        
    # start capture function
    def start_capture(self):
        time_start = time.time()
        frameL = self.cameraL.get_frame()
        frameR = self.cameraR.get_frame()
        
        # getDisparityMap(frameL, frameR, self.stereoMatcher, self.config)

        captureL, captureR, boundObjectData = self.model.predict([frameL, frameR])

        self.camera_view.update_camera_feed(captureL, captureR)
        self.map_view.update_map(boundObjectData)
        
        time_end = time.time()

        self.update_metrics(time_start, time_end)

    # shows fps, processing time and disparity in console
    def update_metrics(self, start, end):
        processing_time = end - start
        fps = 1.0 / processing_time if processing_time > 0 else 0.0    
        print(f"FPS: {fps:.2f}, Processing Time: {processing_time:.4f} seconds")
    
    # resize event to reposition logo and sidebar
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.company_logo:
            self.company_logo.move(self.width() - self.company_logo.width() - 10, 0)
            self.company_logo.raise_()
        if self.sidebar:
            self.sidebar.reposition()
            self.sidebar.raise_()
            
    # initialize stereo matcher
    def init_stereo_matcher(self):
        stereoMatcher = cv2.StereoSGBM_create(
            minDisparity=self.config['minDisparity'],
            numDisparities=self.config['numDisparities'],
            blockSize=self.config['blockSize'],
            P1=8 * 3 * self.config['blockSize'] ** 2,
            P2=32 * 3 * self.config['blockSize'] ** 2,
            disp12MaxDiff=self.config['disp12MaxDiff'],
            uniquenessRatio=self.config['uniquenessRatio'],
            speckleWindowSize=self.config['speckleWindowSize'],
            speckleRange=self.config['speckleRange'],
            preFilterCap=self.config['preFilterCap'],
            mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
        )
        
        return stereoMatcher


# stereo camera class
class StereoCamera:
    def __init__(self, index, config=None, mapType=None):
        self.cam = cv2.VideoCapture(index, cv2.CAP_V4L2)
        if not self.cam.isOpened():
            print(f"Camera {index} failed to open")
            return None
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, config['cameraResolution']['width'])
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, config['cameraResolution']['height'])
        self.cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cam.set(cv2.CAP_PROP_FPS, config['cameraFPS'])
        self.cam.set(cv2.CAP_PROP_AUTOFOCUS, config['cameraAutoFocus'])
        self.cameraResolution = (config['cameraResolution']['width'], config['cameraResolution']['height'])
        self.mapType = mapType
        self.config = config
        self.init_rectification()
        print(f"Stereo Camera {index} initialized.")
        
    def get_frame(self):
        ret, frame = self.cam.read()
        if not ret:
            print("Failed to grab frame")
            return None
        if self.mapType == 'left':
            frame = cv2.remap(frame, self.map0x, self.map0y, cv2.INTER_LINEAR)
        else:
            frame = cv2.remap(frame, self.map1x, self.map1y, cv2.INTER_LINEAR)
        return frame
    
    def init_rectification(self):
        # === Intrinsics ===
        self.K0 = np.array(self.config['K0'])

        self.D0 = np.array(self.config['D0'])

        self.K1 = np.array(self.config['K1'])

        self.D1 = np.array(self.config['D1'])

        # === Extrinsics ===
        R = np.array(self.config['R'])

        T = np.array(self.config['T']) / 100.0  # cm → meters

        self.baseline = np.linalg.norm(T)

        # === Stereo rectification ===
        image_size = self.cameraResolution

        R1, R2, P1, P2, Q, _, _ = cv2.stereoRectify(
            self.K0, self.D0,
            self.K1, self.D1,
            image_size,
            R, T,
            flags=cv2.CALIB_ZERO_DISPARITY,
            alpha=0
        )

        self.fxL = P1[0, 0]
        self.fxR = P2[0, 0]
        
        self.Q = Q

        self.map0x, self.map0y = cv2.initUndistortRectifyMap(
            self.K0, self.D0, R1, P1, image_size, cv2.CV_32FC1
        )

        self.map1x, self.map1y = cv2.initUndistortRectifyMap(
            self.K1, self.D1, R2, P2, image_size, cv2.CV_32FC1
        )
        
        # write self.fx to config.yaml file
        self.config['fxL'] = self.fxL
        self.config['fxR'] = self.fxR
        


        print("Stereo rectification initialized.")
        
def getDisparityMap(frameL, frameR, stereoMatcher, config=None):
    time_start = time.time()
    
    grayL = cv2.cvtColor(frameL, cv2.COLOR_BGR2GRAY)
    grayR = cv2.cvtColor(frameR, cv2.COLOR_BGR2GRAY)
    
    disparity = stereoMatcher.compute(grayL, grayR)
    
    # put disparity in config file
    config['calculatedDisparity'] = disparity.mean()
    
    time_end = time.time()
    return None
    
def getCameraId(cameraName):
    cameraIDs = []
    
    for camera_info in enumerate_cameras():
        if cameraName.lower() in camera_info.name.lower():
            if int(str(camera_info.index)[-1]) not in cameraIDs:
                cameraIDs.append(int(str(camera_info.index)[-1]))
        else:
            print(f"Camera '{camera_info.name}' does not match the specified name '{cameraName}'.")
        
    return cameraIDs
   
    
class AIModel:
    def __init__(self, config=None):
        # try catch block toevoegen
        try:
            self.model = YOLO(model="./yolo11n.pt", task="detect")  # load a model
            self.model.to("cuda")
            self.confidence_threshold = 0.8
            self.distance_threshold = config['matchingThreshold']  # in pixels
            self.config = config
        except Exception as e:
            print(f"Error loading AI model: {e}")
            sys.exit(1)

    # predict function
    def predict(self, captures):
        # gets detections from both cameras
        results = [self.model(captures[0], verbose=False, conf=self.confidence_threshold), self.model(captures[1], verbose=False, conf=self.confidence_threshold)]
        objects = [[], []]
        boundObjectData = {
            'objectName': [],
            'objectDistance': [],
            'objectPosition': []
        }
        
        # for each camera result
        for result in results:
            # for each detection in camera result
            for r in result:
                # check which camera the result is from
                capture = captures[0] if result == results[0] else captures[1]
                boxes = r.boxes
                # for each box in detection
                for box in boxes:
                    # get box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    # calculate center point
                    cx = ((x1 + x2) / 2)
                    cy = ((y1 + y2) / 2)
                    
                    # get class name
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = self.model.names[class_id]
                    
                    # store object data
                    objects[0 if result == results[0] else 1].append((cx, cy, class_name))
                    
                    # draw rectangle around object
                    cv2.rectangle(capture, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 1)
                    
                    # draw center point and distance
                    if capture is captures[0]:
                        cv2.circle(capture, (int(cx), int(cy)), 4, (0, 255, 0), -1)
                    else:
                        cv2.circle(capture, (int(cx), int(cy)), 4, (0, 0, 255), -1)        
                
                capture = r.plot()
        
        # bind objects from both cameras together based on proximity
        detectedObjects = self.bind_objects(objects[0], objects[1])
        
        # for each bound object, calculate distance and draw line between cameras
        for ((xL, yL), (xR, yR), class_name) in detectedObjects:
            distance = self.get_distance(xL, xR)
            absoluteCenterX = ((xL + xR) / 2)
            absoluteCenterY = ((yL + yR) / 2)
            cv2.line(captures[0], (int(xL), int(yL)), (int(xR), int(yR)), (255, 255, 0), 1)
            cv2.line(captures[1], (int(xL), int(yL)), (int(xR), int(yR)), (255, 255, 0), 1)
            cv2.putText(captures[1], f"{distance:.2f}m", (int(xL), int(yL) - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.putText(captures[0], f"{distance:.2f}m", (int(xL), int(yL) - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            boundObjectData['objectName'].append(class_name)
            boundObjectData['objectDistance'].append(distance)
            boundObjectData['objectPosition'].append((absoluteCenterX, absoluteCenterY))
          
        return captures[0], captures[1], boundObjectData
    
    def bind_objects(self, objectsL, objectsR):        
        detectedObjects = []
        
        # for each object in left camera
        for (x1, y1, class_nameL) in objectsL:
                closest_obj = None
                closest_dist = float('inf')
                # find closest object in right camera within threshold and bind them
                for (x2, y2, class_nameR) in objectsR:
                    dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                    if dist < closest_dist and dist < self.distance_threshold:
                        closest_dist = dist
                        closest_obj = (x2, y2)
                if closest_obj is not None:
                    detectedObjects.append([(x1, y1), closest_obj, class_nameL])
                    
        return detectedObjects
    
    # calculate distance from disparity
    def get_distance(self, x_left, x_right):
        fx = self.config['fxL']
        baseline = self.config['baseline']

        # calculate disparity and distance
        disparity = x_left - x_right  # pixels
        disparity = disparity / 1.75
        # print(f"Disparity: {abs(disparity)}")
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