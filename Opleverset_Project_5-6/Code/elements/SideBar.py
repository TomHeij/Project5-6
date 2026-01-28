import os
from PySide6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QPoint, QPointF, QFile
from PySide6.QtGui import QPainter, QPolygon, QColor, QPainterPath, QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QPushButton, QLabel, QGraphicsDropShadowEffect
from PySide6.QtUiTools import QUiLoader

class RightOffCanvas(QWidget):
    def __init__(self, parent, width=280):
        super().__init__(parent)
        self.panelWidth = width
        self.handleWidth = 28  # Handle extends beyond panel
        self.collapsed = True

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
    
    def is_trails_enabled(self):
        """Check if trails checkbox is enabled."""
        return self.cb_trails.isChecked() if self.cb_trails else True
    
    def is_labels_enabled(self):
        """Check if labels checkbox is enabled."""
        return self.cb_labels.isChecked() if self.cb_labels else True
    
    def is_grid_enabled(self):
        """Check if grid checkbox is enabled."""
        return self.cb_grid.isChecked() if self.cb_grid else True
        

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