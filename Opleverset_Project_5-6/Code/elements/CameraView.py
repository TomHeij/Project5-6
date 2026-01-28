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
    
    def update_camera_feed(self, frameR=None, frameL=None):
        # Blend the two camera feeds
        blended = cv2.addWeighted(frameR, 0.5, frameL, 0.5, 0) #blend the two camera feeds
        
        # Convert to QPixmap and display
        pixmap = self.cv2_to_qt(blended)
        self.camera_label.setPixmap(pixmap)
        self.status_label.hide()
    
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