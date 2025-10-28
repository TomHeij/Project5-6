# High-performance camera processing with multi-threading and optimizations
# Run with: eval "$($HOME/miniconda3/bin/conda shell.zsh hook)" && conda activate opencv-cuda && python shit_optimized.py

import cv2
from cv2_enumerate_cameras import enumerate_cameras

import time
import sys
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

class CameraThread(QThread):
    """Dedicated thread for camera capture"""
    frameReady = pyqtSignal(int, np.ndarray)
    
    def __init__(self, camera_id, camera_index):
        super().__init__()
        self.camera_id = camera_id
        self.camera_index = camera_index
        self.cap = None
        self.running = False
        
    def run(self):
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            print(f"Failed to open camera {self.camera_id}")
            return
            
        # Optimize camera settings
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce latency
        
        self.running = True
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frameReady.emit(self.camera_index, frame)
            self.msleep(16)  # ~60 FPS
            
    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()

class ProcessingThread(QThread):
    """Dedicated thread for frame processing"""
    processedFrameReady = pyqtSignal(int, np.ndarray, np.ndarray)
    
    def __init__(self):
        super().__init__()
        self.frame_queue = Queue(maxsize=10)
        self.running = False
        
        # Create optimized background subtractors for each camera
        self.fgbg_list = [
            cv2.createBackgroundSubtractorMOG2(
                history=100, 
                varThreshold=25, 
                detectShadows=False  # Disable for speed
            ) for _ in range(2)
        ]
        
        # Pre-create morphological kernels
        self.kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        self.kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        
    def add_frame(self, camera_index, frame):
        """Add frame to processing queue"""
        if not self.frame_queue.full():
            self.frame_queue.put((camera_index, frame, time.time()))
    
    def run(self):
        self.running = True
        while self.running:
            try:
                camera_index, frame, timestamp = self.frame_queue.get(timeout=0.1)
                
                # Skip old frames to reduce latency
                if time.time() - timestamp > 0.1:
                    continue
                    
                processed_frame, mask = self.process_frame_optimized(frame, camera_index)
                self.processedFrameReady.emit(camera_index, processed_frame, mask)
                
            except:
                continue
                
    def process_frame_optimized(self, frame, camera_index):
        """Optimized frame processing with multi-scale approach"""
        start_time = time.time()
        
        # Resize for faster processing if needed
        height, width = frame.shape[:2]
        if width > 1280:
            scale = 1280 / width
            small_frame = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        else:
            small_frame = frame
            scale = 1.0
        
        # Apply background subtraction
        fgbg = self.fgbg_list[camera_index]
        mask = fgbg.apply(small_frame)
        
        # Optimized noise reduction
        mask = cv2.medianBlur(mask, 3)
        
        # Threshold to binary
        _, mask_binary = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
        
        # Morphological operations for noise reduction
        mask_clean = cv2.morphologyEx(mask_binary, cv2.MORPH_OPEN, self.kernel_small)
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, self.kernel_large)
        
        # Find contours with hierarchy for better filtering
        contours, hierarchy = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Use original frame for drawing
        result_frame = frame.copy()
        
        # Filter and draw contours
        min_area = 500  # Minimum area for detection
        max_area = width * height * 0.3  # Maximum area (30% of frame)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area < area < max_area:
                # Scale contour back if we resized
                if scale != 1.0:
                    contour = (contour / scale).astype(np.int32)
                    
                # Calculate bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by aspect ratio (avoid very thin detections)
                aspect_ratio = w / h if h > 0 else 0
                if 0.2 < aspect_ratio < 5.0:
                    # Draw bounding box
                    cv2.rectangle(result_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # Draw area text
                    cv2.putText(result_frame, f'Area: {int(area)}', 
                              (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Scale mask back if needed
        if scale != 1.0:
            mask_clean = cv2.resize(mask_clean, (width, height))
        
        processing_time = (time.time() - start_time) * 1000
        
        # Add performance info to frame
        cv2.putText(result_frame, f'Processing: {processing_time:.1f}ms', 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        return result_frame, mask_clean
    
    def stop(self):
        self.running = False

def detect_cameras():
    """Detect available cameras"""
    camList = []
    for camera_info in enumerate_cameras():
        index = int(str(camera_info.index)[-1])
        if index not in camList:
            camList.append(index)
    return camList

class OptimizedCameraWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("High-Performance Camera Feeds - Multi-threaded")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize threads
        self.camera_threads = []
        self.processing_thread = ProcessingThread()
        
        # Frame storage
        self.latest_frames = {}
        self.latest_masks = {}
        
        # Performance monitoring
        self.frame_counts = [0, 0]
        self.fps_values = [0.0, 0.0]
        self.last_fps_times = [time.time(), time.time()]
        
        # Setup UI
        self.setup_ui()
        
        # Setup cameras and threads
        self.setup_cameras()
        
        # Setup display timer
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(16)  # ~60 FPS display
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Performance info
        perf_layout = QHBoxLayout()
        self.perf_label = QLabel("Performance: Initializing...")
        self.perf_label.setStyleSheet("font-weight: bold; color: blue;")
        perf_layout.addWidget(self.perf_label)
        main_layout.addLayout(perf_layout)
        
        # Camera feeds layout
        camera_layout = QHBoxLayout()
        
        # Camera 1 section
        cam1_layout = QVBoxLayout()
        cam1_layout.addWidget(QLabel("Camera 1 - Processed"))
        self.cam1_label = QLabel("Camera 1")
        self.cam1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cam1_label.setMinimumSize(600, 400)
        self.cam1_label.setStyleSheet("border: 2px solid blue")
        cam1_layout.addWidget(self.cam1_label)
        
        cam1_layout.addWidget(QLabel("Camera 1 - Motion Mask"))
        self.mask1_label = QLabel("Mask 1")
        self.mask1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mask1_label.setMinimumSize(600, 400)
        self.mask1_label.setStyleSheet("border: 2px solid red")
        cam1_layout.addWidget(self.mask1_label)
        
        # Camera 2 section
        cam2_layout = QVBoxLayout()
        cam2_layout.addWidget(QLabel("Camera 2 - Processed"))
        self.cam2_label = QLabel("Camera 2")
        self.cam2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cam2_label.setMinimumSize(600, 400)
        self.cam2_label.setStyleSheet("border: 2px solid blue")
        cam2_layout.addWidget(self.cam2_label)
        
        cam2_layout.addWidget(QLabel("Camera 2 - Motion Mask"))
        self.mask2_label = QLabel("Mask 2")
        self.mask2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mask2_label.setMinimumSize(600, 400)
        self.mask2_label.setStyleSheet("border: 2px solid red")
        cam2_layout.addWidget(self.mask2_label)
        
        camera_layout.addLayout(cam1_layout)
        camera_layout.addLayout(cam2_layout)
        main_layout.addLayout(camera_layout)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.stats_button = QPushButton("Show Detailed Stats")
        self.stats_button.clicked.connect(self.show_stats)
        control_layout.addWidget(self.stats_button)
        
        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(self.close)
        control_layout.addWidget(self.quit_button)
        
        main_layout.addLayout(control_layout)
        
    def setup_cameras(self):
        """Setup camera threads"""
        cam_ids = detect_cameras()
        print(f"Detected cameras: {cam_ids}")
        
        # Start camera threads
        for i, cam_id in enumerate(cam_ids[:2]):  # Only use first 2 cameras
            camera_thread = CameraThread(cam_id, i)
            camera_thread.frameReady.connect(self.on_frame_ready)
            camera_thread.start()
            self.camera_threads.append(camera_thread)
            
        # Start processing thread
        self.processing_thread.processedFrameReady.connect(self.on_processed_frame_ready)
        self.processing_thread.start()
        
    def on_frame_ready(self, camera_index, frame):
        """Handle new frame from camera thread"""
        self.processing_thread.add_frame(camera_index, frame)
        
        # Update FPS counter
        self.frame_counts[camera_index] += 1
        
    def on_processed_frame_ready(self, camera_index, processed_frame, mask):
        """Handle processed frame from processing thread"""
        self.latest_frames[camera_index] = processed_frame
        self.latest_masks[camera_index] = mask
        
    def update_display(self):
        """Update the display with latest frames"""
        current_time = time.time()
        
        # Update FPS calculations
        for i in range(2):
            if current_time - self.last_fps_times[i] >= 1.0:
                self.fps_values[i] = self.frame_counts[i] / (current_time - self.last_fps_times[i])
                self.frame_counts[i] = 0
                self.last_fps_times[i] = current_time
        
        # Update performance label
        avg_fps = sum(self.fps_values) / len(self.fps_values) if self.fps_values else 0
        queue_size = self.processing_thread.frame_queue.qsize()
        self.perf_label.setText(
            f"FPS: Cam1={self.fps_values[0]:.1f}, Cam2={self.fps_values[1]:.1f}, "
            f"Avg={avg_fps:.1f} | Queue: {queue_size} | Mode: Multi-threaded CPU Optimized"
        )
        
        # Display frames
        if 0 in self.latest_frames:
            self.display_frame(self.latest_frames[0], self.cam1_label)
        if 0 in self.latest_masks:
            self.display_mask(self.latest_masks[0], self.mask1_label)
            
        if 1 in self.latest_frames:
            self.display_frame(self.latest_frames[1], self.cam2_label)
        if 1 in self.latest_masks:
            self.display_mask(self.latest_masks[1], self.mask2_label)
    
    def display_frame(self, frame, label):
        """Convert and display frame in label"""
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatio, 
                                    Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(scaled_pixmap)
    
    def display_mask(self, mask, label):
        """Convert and display mask in label"""
        h, w = mask.shape
        bytes_per_line = w
        q_image = QImage(mask.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatio, 
                                    Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(scaled_pixmap)
    
    def show_stats(self):
        """Show detailed performance statistics"""
        stats = f"""
Performance Statistics:
======================
Camera 1 FPS: {self.fps_values[0]:.2f}
Camera 2 FPS: {self.fps_values[1]:.2f}
Average FPS: {sum(self.fps_values)/len(self.fps_values):.2f}
Processing Queue Size: {self.processing_thread.frame_queue.qsize()}
Active Threads: {threading.active_count()}

Optimizations Applied:
- Multi-threaded camera capture
- Dedicated processing thread
- Frame scaling for faster processing
- Optimized morphological operations
- Queue-based frame management
- Reduced buffer sizes for low latency
"""
        print(stats)
        
    def closeEvent(self, event):
        """Clean up when closing"""
        print("Shutting down threads...")
        
        # Stop processing thread
        self.processing_thread.stop()
        self.processing_thread.wait()
        
        # Stop camera threads
        for thread in self.camera_threads:
            thread.stop()
            thread.wait()
            
        cv2.destroyAllWindows()
        event.accept()

def main():
    print("Starting High-Performance Camera Application...")
    print("Features:")
    print("- Multi-threaded camera capture")
    print("- Dedicated processing thread")
    print("- Optimized algorithms")
    print("- Low-latency frame processing")
    print("")
    
    app = QApplication(sys.argv)
    window = OptimizedCameraWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()