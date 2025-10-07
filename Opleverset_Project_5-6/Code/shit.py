# het is aangeraden om met een venv te werken.
# dit is wel ergens op internet te vinden hoe je dat moet opzetten.


# TODO:
# Multi-Threading



import cv2
from cv2_enumerate_cameras import enumerate_cameras

import time
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap
import numpy as np

# function to open a camera by ID
def open_camera(cam_id):
    cap = cv2.VideoCapture(cam_id)
    if not cap.isOpened():
        print(f"Failed to open camera {cam_id}")
        return None
    # cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    return cap

# function to detect available camera(s)
def detect_cameras():
    camList = []
    for camera_info in enumerate_cameras():
        index = int(str(camera_info.index)[-1])
        if index in camList:
            continue
        camList.append(index)
    return camList

# function to apply filters to the video frames with GPU acceleration
def apply_filters(frame, fgbg, use_gpu=True):
    if use_gpu:
        try:
            return apply_filters_gpu(frame, fgbg)
        except Exception as e:
            print(f"GPU processing failed, falling back to CPU: {e}")
            return apply_filters_cpu(frame, fgbg)
    else:
        return apply_filters_cpu(frame, fgbg)

def apply_filters_gpu(frame, fgbg):
    gpu_frame = cv2.UMat(frame)
    gpu_mask = fgbg.apply(gpu_frame)
    _, gpu_mask = cv2.threshold(gpu_mask, 254, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    gpu_mask = cv2.dilate(gpu_mask, kernel, iterations=3)
    mask = gpu_mask.get()
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 300:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    return frame, mask

def apply_filters_cpu(frame, fgbg):
    mask = fgbg.apply(frame)
    _, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY)
    mask = cv2.dilate(mask, np.ones((2,2), np.uint8), iterations=3)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 300:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    return frame, mask


class CameraWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Feeds - Qt6 (GPU Accelerated)")
        self.setGeometry(100, 100, 1200, 800)
        
        # Check GPU availability
        self.gpu_available = self.check_gpu_support()
        
        # Initialize camera variables
        self.caps = []
        self.fgbg = cv2.createBackgroundSubtractorMOG2(history=80, varThreshold=100)
        
        # Performance monitoring
        self.frame_count = 0
        self.fps_timer = 0
        self.last_fps_time = time.time()
        
        # Setup UI
        self.setup_ui()
        
        # Setup cameras
        self.setup_cameras()
        
        # Setup timer for frame updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(1)  # Update every 1 ms
    
    def check_gpu_support(self):
        """Check if GPU acceleration is available"""
        try:
            # Test if OpenCL is available
            test_mat = cv2.UMat(np.zeros((100, 100, 3), dtype=np.uint8))
            cv2.GaussianBlur(test_mat, (5, 5), 0)
            
            print("✓ GPU acceleration (OpenCL) is available and working!")
            return True
        except Exception as e:
            print(f"✗ GPU acceleration not available: {e}")
            print("Falling back to CPU processing")
            return False
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Camera feeds layout
        camera_layout = QHBoxLayout()
        
        # Camera 1 section
        cam1_layout = QVBoxLayout()
        self.cam1_label = QLabel("Camera 1")
        self.cam1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cam1_label.setMinimumSize(400, 300)
        self.cam1_label.setStyleSheet("border: 1px solid black")
        
        self.mask1_label = QLabel("Mask 1")
        self.mask1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mask1_label.setMinimumSize(400, 300)
        self.mask1_label.setStyleSheet("border: 1px solid black")
        
        cam1_layout.addWidget(self.cam1_label)
        cam1_layout.addWidget(self.mask1_label)
        
        # Camera 2 section
        cam2_layout = QVBoxLayout()
        self.cam2_label = QLabel("Camera 2")
        self.cam2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cam2_label.setMinimumSize(400, 300)
        self.cam2_label.setStyleSheet("border: 1px solid black")
        
        self.mask2_label = QLabel("Mask 2")
        self.mask2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mask2_label.setMinimumSize(400, 300)
        self.mask2_label.setStyleSheet("border: 1px solid black")
        
        cam2_layout.addWidget(self.cam2_label)
        cam2_layout.addWidget(self.mask2_label)
        
        camera_layout.addLayout(cam1_layout)
        camera_layout.addLayout(cam2_layout)
        
        # Add camera layout to main layout
        main_layout.addLayout(camera_layout)
        
        # Performance info and controls
        control_layout = QHBoxLayout()
        
        self.gpu_toggle_button = QPushButton("Toggle CPU/GPU")
        self.gpu_toggle_button.clicked.connect(self.toggle_gpu_processing)
        control_layout.addWidget(self.gpu_toggle_button)
        
        self.performance_label = QLabel("Performance: Initializing...")
        control_layout.addWidget(self.performance_label)
        
        # Quit button
        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(self.close)
        control_layout.addWidget(self.quit_button)
        
        main_layout.addLayout(control_layout)
    
    def setup_cameras(self):
        # Get camera IDs
        cam_ids = detect_cameras()
        
        # Open cameras and store their capture objects
        for cam_id in cam_ids:
            print(f"Detected camera ID: {cam_id}")
            cap = open_camera(cam_id)
            if cap:
                self.caps.append(cap)
    
    def cv2_to_qimage(self, cv_img):
        """Convert OpenCV image to QImage"""
        h, w, ch = cv_img.shape
        bytes_per_line = ch * w
        
        if ch == 3:  # BGR to RGB
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            q_image = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        else:  # Grayscale
            q_image = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        
        return q_image
    
    def toggle_gpu_processing(self):
        """Toggle between GPU and CPU processing"""
        self.gpu_available = not self.gpu_available
        mode = "GPU (OpenCL)" if self.gpu_available else "CPU"
        self.gpu_toggle_button.setText(f"Using: {mode}")
        print(f"Switched to {mode} processing")
    
    def update_frames(self):
        """Update camera frames in the GUI"""
        import time
        frame_start_time = time.time()
        
        if len(self.caps) >= 2:
            # Read frames from both cameras
            ret1, frame1 = self.caps[0].read()
            ret2, frame2 = self.caps[1].read()
            
            if ret1:
                # Apply filters to frame 1 with GPU acceleration
                processed_frame1, mask1 = apply_filters(frame1, self.fgbg, use_gpu=self.gpu_available)
                
                # Convert to QImage and display
                q_img1 = self.cv2_to_qimage(processed_frame1)
                pixmap1 = QPixmap.fromImage(q_img1)
                scaled_pixmap1 = pixmap1.scaled(self.cam1_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.cam1_label.setPixmap(scaled_pixmap1)
                
                # Convert mask to QImage and display
                q_mask1 = self.cv2_to_qimage(cv2.cvtColor(mask1, cv2.COLOR_GRAY2BGR))
                mask_pixmap1 = QPixmap.fromImage(q_mask1)
                scaled_mask1 = mask_pixmap1.scaled(self.mask1_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.mask1_label.setPixmap(scaled_mask1)
            
            if ret2:
                # Apply filters to frame 2 with GPU acceleration
                processed_frame2, mask2 = apply_filters(frame2, self.fgbg, use_gpu=self.gpu_available)
                
                # Convert to QImage and display
                q_img2 = self.cv2_to_qimage(processed_frame2)
                pixmap2 = QPixmap.fromImage(q_img2)
                scaled_pixmap2 = pixmap2.scaled(self.cam2_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.cam2_label.setPixmap(scaled_pixmap2)
                
                # Convert mask to QImage and display
                q_mask2 = self.cv2_to_qimage(cv2.cvtColor(mask2, cv2.COLOR_GRAY2BGR))
                mask_pixmap2 = QPixmap.fromImage(q_mask2)
                scaled_mask2 = mask_pixmap2.scaled(self.mask2_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.mask2_label.setPixmap(scaled_mask2)
        
        # Update performance monitoring
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:  # Update every second
            fps = self.frame_count / (current_time - self.last_fps_time)
            processing_time = (current_time - frame_start_time) * 1000  # ms
            mode = "GPU (OpenCL)" if self.gpu_available else "CPU"
            self.performance_label.setText(f"FPS: {fps:.1f} | Processing: {processing_time:.1f}ms | Mode: {mode}")
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def closeEvent(self, event):
        """Clean up when closing the window"""
        self.timer.stop()
        for cap in self.caps:
            if cap:
                cap.release()
        cv2.destroyAllWindows()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = CameraWindow()
    window.show()
    sys.exit(app.exec())
    
    
if __name__ == "__main__":
    main()