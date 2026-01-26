import sys
import os
import warnings
import math
from PySide6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QPoint, QPointF, QTimer, QFile
from PySide6.QtGui import QPainter, QPolygon, QColor, QPainterPath, QImage, QPixmap, QIcon
from PySide6.QtWidgets import (
    QWidget, QApplication, QLabel, QVBoxLayout, QCheckBox,
    QPushButton, QSlider, QGroupBox, QHBoxLayout, QGraphicsDropShadowEffect, QMainWindow
)
from PySide6.QtUiTools import QUiLoader
import pyqtgraph as pg
import cv2
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from datetime import datetime

# Ignore disconnect warnings for pyqtgraph specifically
warnings.filterwarnings("ignore", message="Failed to disconnect")

# Configure PyQtGraph for map-like appearance
pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")


class ChevronHandle(QWidget):
    """Sine wave-shaped toggle handle embedded in the sidebar edge."""

    def __init__(self, parent):
        super().__init__(parent)
        self.collapsed = False
        self._hovered = False
        self.setFixedSize(20, 100)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
       

    def setCollapsed(self, collapsed: bool):
        if self.collapsed == collapsed: #Prevent unnecessary updates (paint events)
            return
        self.collapsed = collapsed
        self.update()

    def enterEvent(self, event):
        if not self._hovered: #avoid redandont repaint
            self._hovered = True
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._hovered: #avoid redandont repaint
            self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.parent().toggle()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Colors based on hover state
        if self._hovered:
            bg_color = QColor("#555555")
            arrow_color = QColor("#ffffff")
        else:
            bg_color = QColor("#cacaca")
            arrow_color = QColor("#555555")
        
        w, h = self.width(), self.height()
        
        # Draw sine wave shaped background
        path = QPainterPath()
        
        # Start at top-right
        path.moveTo(w, 0)
        
        # Sine wave curve on the left side (curving inward then outward)
        # Top portion curves inward
        path.quadTo(QPointF(w * 0.2, h * 0.25), QPointF(w * 0.15, h * 0.5))
        # Bottom portion curves back out
        path.quadTo(QPointF(w * 0.2, h * 0.75), QPointF(w, h))
        
        # Close the path along the right edge
        path.lineTo(w, 0)
        
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
        
        # Draw chevron arrow in center
        painter.setBrush(arrow_color)
        arrow_w, arrow_h = 8, 16
        cx, cy = w // 2, h // 2
        
        if self.collapsed:
            # ◀ to expand the sidebar leftward
            poly = QPolygon([
                QPoint(cx + arrow_w // 2, cy - arrow_h // 2),
                QPoint(cx - arrow_w // 2, cy),
                QPoint(cx + arrow_w // 2, cy + arrow_h // 2),
            ])
        else:
            # ▶ to collapse the sidebar rightward
            poly = QPolygon([
                QPoint(cx - arrow_w // 2, cy - arrow_h // 2),
                QPoint(cx + arrow_w // 2, cy),
                QPoint(cx - arrow_w // 2, cy + arrow_h // 2),
            ])

        painter.drawPolygon(poly)


class RightOffCanvas(QWidget):
    def __init__(self, parent, width=280):
        super().__init__(parent)
        self.panelWidth = width
        self.handleWidth = 28  # Handle extends beyond panel
        self.collapsed = False

        # Make the main widget transparent (only the content area will have color)
        self.setStyleSheet("background: transparent;")
        self.setFixedWidth(width + self.handleWidth)

        # Add drop shadow for depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(-5, 0)
        self.setGraphicsEffect(shadow)

        # Load control panel from UI file
        ui_file_path = os.path.join(os.path.dirname(__file__), "ControlPanel.ui")
        if not os.path.exists(ui_file_path):
            ui_file_path = os.path.join("elements", "ControlPanel.ui")
        
        loader = QUiLoader()
        ui_file = QFile(ui_file_path)
        if ui_file.open(QFile.ReadOnly):
            self.contentWidget = loader.load(ui_file, self)
            ui_file.close()
            
            # Ensure contentWidget is a child of self
            if self.contentWidget:
                self.contentWidget.setParent(self)
            
            # Get references to checkboxes
            self.cb_drones = self.contentWidget.findChild(QCheckBox, "cb_drones") if self.contentWidget else None
            self.cb_ships = self.contentWidget.findChild(QCheckBox, "cb_ships") if self.contentWidget else None
            self.cb_unknown = self.contentWidget.findChild(QCheckBox, "cb_unknown") if self.contentWidget else None
            self.cb_trails = self.contentWidget.findChild(QCheckBox, "cb_trails") if self.contentWidget else None
            self.cb_labels = self.contentWidget.findChild(QCheckBox, "cb_labels") if self.contentWidget else None
            self.cb_range = self.contentWidget.findChild(QCheckBox, "cb_range") if self.contentWidget else None
            self.cb_zones = self.contentWidget.findChild(QCheckBox, "cb_zones") if self.contentWidget else None
            self.cb_grid = self.contentWidget.findChild(QCheckBox, "cb_grid") if self.contentWidget else None
            self.cb_radar = self.contentWidget.findChild(QCheckBox, "cb_radar") if self.contentWidget else None
            self.cb_direction = self.contentWidget.findChild(QCheckBox, "cb_direction") if self.contentWidget else None
            self.btn_alarm = self.contentWidget.findChild(QPushButton, "btn_alarm") if self.contentWidget else None
        else:
            # Fallback: create simple widget if UI file not found
            self.contentWidget = QWidget(self)
            self.contentWidget.setStyleSheet("""
                background: rgba(240, 240, 240, 178);
                border-left: 1px solid #CCCCCC;
            """)
            layout = QVBoxLayout(self.contentWidget)
            title = QLabel("Map Controls")
            title.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)
            # Create minimal checkbox references to avoid errors
            self.cb_drones = self.cb_ships = self.cb_unknown = None
            self.cb_trails = self.cb_labels = self.cb_range = self.cb_zones = None
            self.cb_grid = self.cb_radar = self.cb_direction = None

        # Chevron handle
        self.handle = ChevronHandle(self)
        self.handle.raise_()

        # Animation
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.InOutCubic)

        self.reposition()

        # Alarm button
        if not self.btn_alarm:
            return
        
        base = os.path.join(os.path.dirname(__file__), "..", "imgs")
        self._alarm_icon_on = QIcon(os.path.join(base, "alarm-on.png"))
        self._alarm_icon_off = QIcon(os.path.join(base, "alarm-off.png"))

        self.btn_alarm.setCheckable(True)
        self.btn_alarm.setChecked(False)
        

        self.btn_alarm.toggled.connect(self.update_alarm_icon)
        self.update_alarm_icon(self.btn_alarm.isChecked())

        # Glow pulse effect using drop shadow
        self._pulse_effect = QGraphicsDropShadowEffect(self.btn_alarm)
        self._pulse_effect.setBlurRadius(0)
        self._pulse_effect.setColor(QColor(255, 60, 60))  # Red glow
        self._pulse_effect.setOffset(0, 0)
        self._pulse_effect.setEnabled(False)
        self.btn_alarm.setGraphicsEffect(self._pulse_effect)

        self._pulse_anim = QPropertyAnimation(self._pulse_effect, b"blurRadius")
        self._pulse_anim.setDuration(800)
        self._pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._pulse_anim.setLoopCount(-1)
        
        
    def update_alarm_icon(self, checked: bool):
        if not self.btn_alarm:
            return

        if checked:
            self.btn_alarm.setIcon(self._alarm_icon_on)
        else:
            self.btn_alarm.setIcon(self._alarm_icon_off)

    def set_alarm_muted(self, is_muted: bool):
        if not self.btn_alarm:
            return

        self.btn_alarm.setChecked(not is_muted)

    def start_alarm_pulse(self):
        if not self.btn_alarm:
            return

        # If already running, don't restart (prevents stuttering on frequent updates)
        if self._pulse_anim.state() == QPropertyAnimation.State.Running:
            return

        self._pulse_effect.setEnabled(True)
        self._pulse_anim.setStartValue(0)
        self._pulse_anim.setEndValue(25)
        self._pulse_anim.start()


    def stop_alarm_pulse(self):
        if not self.btn_alarm:
            return

        self._pulse_anim.stop()
        self._pulse_effect.setBlurRadius(0)
        self._pulse_effect.setEnabled(False)



    def reposition(self):
        p = self.parent().rect()
        h = p.height()
        totalWidth = self.panelWidth + self.handleWidth

        if self.collapsed:
            # Only show handle portion
            self.setGeometry(p.width() - self.handleWidth, 0, totalWidth, h)
        else:
            # Show full panel
            self.setGeometry(p.width() - totalWidth, 0, totalWidth, h)

        # Position content area (after handle)
        self.contentWidget.setGeometry(self.handleWidth, 0, self.panelWidth, h)
        
        # Position handle on left edge
        self.handle.move(2, (h - self.handle.height()) // 2)

    def resizeEvent(self, event):
        self.reposition()

    def toggle(self):
        p = self.parent().rect()
        h = p.height()
        totalWidth = self.panelWidth + self.handleWidth

        if self.collapsed:
            start = QRect(p.width() - self.handleWidth, 0, totalWidth, h)
            end = QRect(p.width() - totalWidth, 0, totalWidth, h)
        else:
            start = QRect(p.width() - totalWidth, 0, totalWidth, h)
            end = QRect(p.width() - self.handleWidth, 0, totalWidth, h)

        self.anim.stop()
        self.anim.setStartValue(start)
        self.anim.setEndValue(end)
        self.anim.start()

        self.collapsed = not self.collapsed
        self.handle.setCollapsed(self.collapsed)


class TearOffTab(QWidget):
    """Individual tab that can be clicked or dragged to tear off."""
    
    def __init__(self, name, index, is_last, parent=None):
        super().__init__(parent)
        self.name = name
        self.index = index
        self.is_last = is_last
        self.is_active = False
        self._hovered = False
        self._drag_start = None
        self._drag_threshold = 15
        
        self.setFixedSize(140, 44)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
    
    def setActive(self, active):
        self.is_active = active
        self.update()
    
    def enterEvent(self, event):
        self._hovered = True
        self.update()
    
    def leaveEvent(self, event):
        self._hovered = False
        self.update()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start = event.position().toPoint()
    
    def mouseMoveEvent(self, event):
        if self._drag_start and (event.position().toPoint() - self._drag_start).manhattanLength() > self._drag_threshold:
            # Start drag - tear off the tab
            self.parent().parent().tearOffTab(self.index)
            self._drag_start = None
    
    def mouseReleaseEvent(self, event):
        if self._drag_start:
            # Click - switch to this tab
            self.parent().parent().activateTab(self.index)
        self._drag_start = None
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Colors
        if self.is_active:
            bg_color = QColor("#c0c0c0") #active tab is gray
            text_color = QColor("#000000")
        elif self._hovered:
            bg_color = QColor("#e8e8e8")
            text_color = QColor("#333333")
        else:
            bg_color = QColor("#ffffff")
            text_color = QColor("#555555")
        
        # Draw tab shape
        path = QPainterPath()
        radius = h // 2 if self.is_last else 0
        
        path.moveTo(0, 0) # Top-left
        path.lineTo(w, 0) # Top-right (Always 90 deg)
        if self.is_last:
            path.lineTo(w, h - radius)
            path.quadTo(w, h, w - radius, h) # Bottom-right (Rounded)
        else:
            path.lineTo(w, h)
        path.lineTo(0, h) # Bottom-left
        path.closeSubpath()
        
        painter.setBrush(bg_color)
        painter.setPen(QColor("#aaaaaa"))
        painter.drawPath(path)
        
        # Draw text
        painter.setPen(text_color)
        painter.drawText(self.rect(), Qt.AlignCenter, self.name)


class TearOffTabBar(QWidget):
    """Tab bar containing tear-off tabs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabs = []
        self.setFixedHeight(44)
        self.setStyleSheet("background: rgba(0, 0, 0, 40); border-bottom: 1px solid rgba(255, 255, 255, 20);")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch()
    
    def addTab(self, name, index, is_last=False):
        tab = TearOffTab(name, index, is_last, self)
        self.tabs.append(tab)
        # Insert before the stretch
        self.layout().insertWidget(self.layout().count() - 1, tab)
        return tab
    
    def setActiveTab(self, index):
        for tab in self.tabs:
            tab.setActive(tab.index == index)
    
    def hideTab(self, index):
        for tab in self.tabs:
            if tab.index == index:
                tab.hide()
    
    def showTab(self, index):
        for tab in self.tabs:
            if tab.index == index:
                tab.show()


class FloatingPane(QWidget):
    """Floating pane that can be moved and resized within the main window."""
    
    def __init__(self, content_widget, tab_index, tab_name, parent=None):
        super().__init__(parent)
        self.content_widget = content_widget
        self.tab_index = tab_index
        self.tab_name = tab_name
        
        self._drag_pos = None
        self._resize_edge = None
        self._resize_margin = 8
        self._min_size = 150
        
        # Start as a perfect square
        self.setGeometry(50, 80, 500, 500)
        self.setMinimumSize(self._min_size, self._min_size)
        
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("""
            FloatingPane {
                background: #f0f0f0;
                border: 3px solid #000000;
                border-radius: 8px;
            }
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(4, 4)
        self.setGraphicsEffect(shadow)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        
        # Title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(28)
        title_bar.setStyleSheet("background: #555555; border-radius: 4px;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(8, 0, 4, 0)
        
        title_label = QLabel(tab_name)
        title_label.setStyleSheet("color: white; font-weight: bold; background: transparent;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 50);
                border-radius: 3px;
            }
        """)
        close_btn.clicked.connect(self.closePane)
        title_layout.addWidget(close_btn)
        
        layout.addWidget(title_bar)
        
        # Content
        content_widget.setParent(self)
        layout.addWidget(content_widget)
        
        self.setMouseTracking(True)
    
    def closePane(self):
        # Return tab to tab bar
        self.parent().returnFloatingPane(self)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            self._resize_edge = self._getResizeEdge(pos)
            if not self._resize_edge:
                self._drag_pos = event.globalPosition().toPoint() - self.pos()
    
    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        
        if event.buttons() == Qt.NoButton:
            # Update cursor based on edge
            edge = self._getResizeEdge(pos)
            if edge in ('left', 'right'):
                self.setCursor(Qt.SizeHorCursor)
            elif edge in ('top', 'bottom'):
                self.setCursor(Qt.SizeVerCursor)
            elif edge in ('top-left', 'bottom-right'):
                self.setCursor(Qt.SizeFDiagCursor)
            elif edge in ('top-right', 'bottom-left'):
                self.setCursor(Qt.SizeBDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        elif event.buttons() == Qt.LeftButton:
            if self._resize_edge:
                self._doResize(event.globalPosition().toPoint())
            elif self._drag_pos:
                new_pos = event.globalPosition().toPoint() - self._drag_pos
                # Bound to parent
                parent_rect = self.parent().rect()
                new_pos.setX(max(0, min(new_pos.x(), parent_rect.width() - self.width())))
                new_pos.setY(max(0, min(new_pos.y(), parent_rect.height() - self.height())))
                self.move(new_pos)
    
    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resize_edge = None


    def _getResizeEdge(self, pos):
        m = self._resize_margin
        w, h = self.width(), self.height()
        
        left = pos.x() < m
        right = pos.x() > w - m
        top = pos.y() < m
        bottom = pos.y() > h - m
        
        if top and left: return 'top-left'
        if top and right: return 'top-right'
        if bottom and left: return 'bottom-left'
        if bottom and right: return 'bottom-right'
        if left: return 'left'
        if right: return 'right'
        if top: return 'top'
        if bottom: return 'bottom'
        return None
    
    def _doResize(self, global_pos):
        geo = self.geometry()
        # Map to parent coordinates
        parent_pos = self.parent().mapFromGlobal(global_pos)
        
        if 'left' in self._resize_edge:
            new_left = max(0, parent_pos.x())
            new_width = geo.right() - new_left
            if new_width >= self._min_size:
                geo.setLeft(new_left)
        elif 'right' in self._resize_edge:
            new_right = min(self.parent().width(), parent_pos.x())
            new_width = new_right - geo.left()
            if new_width >= self._min_size:
                geo.setRight(new_right)
                
        if 'top' in self._resize_edge:
            new_top = max(0, parent_pos.y())
            new_height = geo.bottom() - new_top
            if new_height >= self._min_size:
                geo.setTop(new_top)
        elif 'bottom' in self._resize_edge:
            new_bottom = min(self.parent().height(), parent_pos.y())
            new_height = new_bottom - geo.top()
            if new_height >= self._min_size:
                geo.setBottom(new_bottom)
        
        self.setGeometry(geo)


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
                    self.timer.start(50)  # Update every 50ms
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
            blended = cv2.addWeighted(frameR, 0.5, frameL, 1 - 0.5, 0)
            
            # Convert to QPixmap and display
            pixmap = self.cv2_to_qt(blended)
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
    
    
        
class MapView(QWidget):
    """2D Map Visualization with PyQtGraph for displaying object positions and trails."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the PlotWidget
        self.plot_widget = pg.PlotWidget(title="Object Locatie in 2D")
        self.layout.addWidget(self.plot_widget)
        
        # Lock the aspect ratio so the map doesn't look stretched
        self.plot_widget.setAspectLocked(True)

        
        # Configure the view
        self.plot_widget.showGrid(x=False, y=False)  # Turn off default grid initially
        self.plot_widget.getPlotItem().setMouseEnabled(
            x=False, y=False
        )  #lock pan/zoom
        self.plot_widget.getPlotItem().getViewBox().setAspectLocked(True)
        self.plot_widget.getPlotItem().getViewBox().setLimits(
            xMin=-10, xMax=10, yMin=0, yMax=10
        )
        self.plot_widget.getPlotItem().getViewBox().setRange(
            rect=pg.QtCore.QRectF(-10, 0, 20, 10)
        )
        
        # Add axis labels for coordinates
        self.plot_widget.setLabel("bottom", "Lateral Position (m)")
        self.plot_widget.setLabel("left", "Forward Distance (m)")
        
        # Create grid using native pyqtgraph function (much faster)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Text items for labels (stored to update/remove them)
        self.text_items = {}  # Maps object_id to TextItem
        
        # Color scheme for different object classes
        self.class_colors = {
            'person': (100, 149, 237),      # Cornflower blue
            'drone': (220, 20, 60),           # Crimson
            'ship': (178, 34, 34),         # Firebrick
            'chair': (50, 205, 50),       # Lime green
            'default': (169, 169, 169)      # Dark gray
        }

        # Trail visibility flag
        self.trails_enabled = True

    def set_trails_enabled(self, enabled: bool):
        """Enable or disable trail drawing."""
        self.trails_enabled = enabled

    
    def _get_class_color(self, class_name):
        """Get color for object class."""
        return self.class_colors.get(class_name.lower(), self.class_colors['default'])
    

    def update_object_positions(self, tracks):
        
        self.plot_widget.clear()
        
        # Remove old text items
        for text_item in self.text_items.values():
            self.plot_widget.removeItem(text_item)
        self.text_items.clear()
        

        if not tracks:
            return
    
        # Process extracted tracks
        for track in tracks:
            if not isinstance(track, dict):
                continue
            
            obj_id = track.get('id', 0)
            label = track.get('label', 'unknown')
            history = track.get('history', [])
            current_pos = track.get('current_pos', (0, 0))
            
            lateral, forward = current_pos
            
    
            # Get color for this object class
            color = self._get_class_color(label)
            
            # Plot trail (history) if trails are enabled
            if self.trails_enabled and len(history) > 1:
                trail_x = [pos[0] for pos in history]
                trail_y = [pos[1] for pos in history]
                # Create gradient effect - older points are more transparent
                for i in range(len(trail_x) - 1):
                    alpha = int(100 + (155 * i / len(trail_x)))
                    pen = pg.mkPen(color=color, width=2, style=Qt.SolidLine)
                    self.plot_widget.plot(
                        [trail_x[i], trail_x[i+1]], 
                        [trail_y[i], trail_y[i+1]], 
                        pen=pen
                    )
            
            # Plot current position as circle
            self.plot_widget.plot(
                [lateral], 
                [forward], 
                symbol='o', 
                symbolSize=15, 
                symbolBrush=pg.mkBrush(color=color),
                pen=pg.mkPen(color=(0, 0, 0), width=1)
            )
            
            # Add text label with object info
            # Use the most recent distance from history if available for display
            display_depth = history[-1][3] if history else forward
            
            label_text = f"{label}\nID:{obj_id}\n{display_depth:.2f}m"
            text_item = pg.TextItem(
                text=label_text,
                color=(0, 0, 0),
                anchor=(0.5, 1.5)  # Position below the point
            )
            text_item.setPos(lateral, forward)
            self.plot_widget.addItem(text_item)
            self.text_items[obj_id] = text_item

    
class MainContentArea(QWidget):
    """Main content area with tear-off tabs."""
    
    TAB_CAMERA = 0
    TAB_MAP = 1
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tab_names = {0: "Camera", 1: "Map"}
        self.active_tab = self.TAB_CAMERA
        self.floating_pane = None
        # Logo setup
        logo_path = os.path.join(os.path.dirname(__file__), "..", "imgs", "Logo-Tidalis.jpg")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            self.company_logo = QLabel(self)
            self.company_logo.setPixmap(pixmap)
            self.company_logo.setScaledContents(True)
            self.company_logo.setFixedSize(140, 44) # Match tab height
            self.company_logo.show()
        else:
            print(f"Warning: Logo not found at {logo_path}")
            self.company_logo = None
        
        # Create views
        self.camera_view = CameraView()
        self.map_view = MapView()
        self.views = {0: self.camera_view, 1: self.map_view}
        
        # Main view container - fills entire area
        self.view_container = QWidget(self)
        self.view_layout = QVBoxLayout(self.view_container)
        self.view_layout.setContentsMargins(0, 0, 0, 0)
        self.view_layout.addWidget(self.camera_view)
        self.map_view.setParent(None)  # Not visible initially
        
        # Tab bar - overlaid as top-left title area
        self.tab_bar = TearOffTabBar(self)
        self.tab_bar.addTab("Camera", 0, is_last=False)
        self.tab_bar.addTab("Map", 1, is_last=True)
        self.tab_bar.setActiveTab(self.active_tab)
        
        # Ensure tab bar is on top
        self.tab_bar.raise_()
    
    def resizeEvent(self, event):
        # View container takes full size
        self.view_container.setGeometry(self.rect())
        # Tab bar at top left
        self.tab_bar.setGeometry(0, 0, self.width(), 44)
        
        # Position logo at top right
        if self.company_logo:
            self.company_logo.move(self.width() - self.company_logo.width() - 10, 0)
            self.company_logo.raise_()
            
        super().resizeEvent(event)
    
    def activateTab(self, index):
        if self.floating_pane and self.floating_pane.tab_index == index:
            return  # This tab is floating
        
        self.active_tab = index
        self.tab_bar.setActiveTab(index)
        
        # Show the correct view
        self._showMainView(index)
    
    def _showMainView(self, index):
         # Clear current view
        while self.view_layout.count():
            item = self.view_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Add new view
        view = self.views[index]
        view.setParent(self.view_container)
        self.view_layout.addWidget(view)
    
    def tearOffTab(self, index):
        # Get the view for this tab
        view = self.views[index]
        
        # Create floating pane
        self.floating_pane = FloatingPane(view, index, self.tab_names[index], self)
        self.floating_pane.show()
        self.floating_pane.raise_()
        
        # Hide the tab
        self.tab_bar.hideTab(index)
        
        # Switch to the other tab as main view
        other_tab = self.TAB_MAP if index == self.TAB_CAMERA else self.TAB_CAMERA
        self.activateTab(other_tab)
    
    def returnFloatingPane(self, pane):
        # Get the view back
        view = pane.content_widget
        tab_index = pane.tab_index
        
        # Show the tab again
        self.tab_bar.showTab(tab_index)
        
        # Put view back in views dict
        view.setParent(None)
        self.views[tab_index] = view
        
        # Close the pane
        pane.deleteLater()
        self.floating_pane = None