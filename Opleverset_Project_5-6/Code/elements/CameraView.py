from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QImage, QPixmap, QPainter
from PySide6.QtWidgets import QWidget, QLabel
import cv2
from datetime import datetime

class CameraView(QWidget):
    """Camera view with live feed from stereo cameras."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #000000;")
        
        # Camera setup
        self.cameraL = None
        self.cameraR = None
        self.aimodel = None
        self.cameras_connected = False
        
        # Camera feed label
        self.camera_label = QLabel(self)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setScaledContents(True)
        self.camera_label.setStyleSheet("background: transparent;")
        
        # Status label for "not connected" message
        self.status_label = QLabel("Stereo camera is not connected", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            color: #ffffff;
            font-size: 24px;
            font-weight: bold;
            background: transparent;
        """)
        self.status_label.show()
        self.status_label.raise_()
        
        # Timer for camera updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_camera_feed)
    
    def setup_cameras(self, cameraL, cameraR, aimodel):
        self.cameraL = cameraL
        self.cameraR = cameraR
        self.aimodel = aimodel
        
        # Check if cameras are connected
        if self.cameraL and self.cameraR:
            # Check if cameras have valid capture objects
            if hasattr(self.cameraL, 'cam') and hasattr(self.cameraR, 'cam'):
                if self.cameraL.cam and self.cameraL.cam.isOpened() and \
                   self.cameraR.cam and self.cameraR.cam.isOpened():
                    self.cameras_connected = True
                    self.status_label.hide()
                    self.timer.start(50)  # Update every 50ms = 20 frames per second
                    return
        
        self.cameras_connected = False
        self.status_label.show()

    def draw_overlay_on_pixmap(self, pixmap):
        """Draw UI overlay on the pixmap."""
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = pixmap.width(), pixmap.height()
        
        # Scale-independent positioning
        margin = int(w * 0.02)  # 2% of width
        top_y = int(h * 0.05)   # 3% from top ()
        bar_height = int(h * 0.08)  # 8% of height

        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        fm = painter.fontMetrics()
        
        status_text = "SYSTEM: ACTIVE"
        time_text = datetime.now().strftime("%H:%M:%S")  # Real time: HH:MM:SS
        
        w_status = fm.horizontalAdvance(status_text) + 10
        w_time = fm.horizontalAdvance(time_text) + 10
        box_height = int(h * 0.03)
        
        # Left side status
        painter.fillRect(QRect(margin, top_y, w_status, box_height), Qt.white)
        painter.setPen(Qt.black)
        painter.drawText(QRect(margin, top_y, w_status, box_height), Qt.AlignCenter, status_text)
        
        # Right side time
        painter.fillRect(QRect(w - margin - w_time, top_y, w_time, box_height), Qt.white)
        painter.drawText(QRect(w - margin - w_time, top_y, w_time, box_height), Qt.AlignCenter, time_text)
        
        painter.end()
        return pixmap
    
    def update_camera_feed(self):
        """Update the camera feed display."""
        if not self.cameras_connected:
            return
        
        try:
            frameL = self.cameraL.get_frame() if self.cameraL else None
            frameR = self.cameraR.get_frame() if self.cameraR else None
            
            if frameL is None or frameR is None:
                self.cameras_connected = False
                self.status_label.show()
                self.timer.stop()
                return
            
            # Process frames with AI model if available
            if self.aimodel:
                frameL, frameR = self.aimodel.predict([frameL, frameR])
            
            # Blend the two camera feeds
            blended = cv2.addWeighted(frameR, 0.5, frameL, 0.5, 0) #blend the two camera feeds
            
            display_frame = blended 
            
            # Convert to QPixmap and display
            pixmap = self.cv2_to_qt(display_frame)
            pixmap = self.draw_overlay_on_pixmap(pixmap)  
            self.camera_label.setPixmap(pixmap)
            
        except Exception as e:
            print(f"Error updating camera feed: {e}")
            self.cameras_connected = False
            self.status_label.show()
            self.timer.stop()
    
    def cv2_to_qt(self, cv_img):
        """Convert OpenCV image to QPixmap."""
        if cv_img is None:
            return QPixmap()
        height, width, channel = cv_img.shape
        bytes_per_line = 3 * width
        q_img = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(q_img)
        # Scale to fit the widget while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.width(), self.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        return scaled_pixmap
    
    def resizeEvent(self, event):
        """Handle widget resize to update camera label and status label positions."""
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        
        # Update camera label size
        self.camera_label.setGeometry(0, 0, w, h)
        
        # Update status label position (centered)
        status_w, status_h = 400, 50
        self.status_label.setGeometry(
            (w - status_w) // 2,
            (h - status_h) // 2,
            status_w,
            status_h
        )
        
        # Update camera feed if connected
        if self.cameras_connected:
            self.update_camera_feed()