import sys
import os
import warnings
import math
from PySide6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QPoint, QPointF, QTimer, QFile
from PySide6.QtGui import QPainter, QPolygon, QColor, QPainterPath, QImage, QPixmap
from PySide6.QtWidgets import (
    QWidget, QApplication, QLabel, QVBoxLayout, QCheckBox,
    QPushButton, QSlider, QGroupBox, QHBoxLayout, QGraphicsDropShadowEffect, QMainWindow
)
from PySide6.QtUiTools import QUiLoader
import pyqtgraph as pg
import cv2

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
        self.collapsed = collapsed
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        self.parent().toggle()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Colors based on hover state
        if self._hovered:
            bg_color = QColor("#3a3a3a")
            arrow_color = QColor("#ffffff")
        else:
            bg_color = QColor("#555555")
            arrow_color = QColor("#dddddd")
        
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
            bg_color = QColor("#ffffff")
            text_color = QColor("#000000")
        elif self._hovered:
            bg_color = QColor("#e8e8e8")
            text_color = QColor("#333333")
        else:
            bg_color = QColor("#d0d0d0")
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
        # TODO:
        # - Bewaar content widget, tab index en naam
        # - Initialiseer drag en resize status variabelen
        # - Stel initiële geometrie in (500x500 vierkant)
        # - Stel minimum grootte in
        # - Pas stylesheet toe met rand en achtergrond
        # - Voeg slagschaduw effect toe
        # - Maak layout met titelbalk en content
        # - Voeg sluitknop toe aan titelbalk
        # - Activeer muis tracking
        pass
    
    def closePane(self):
        # TODO: Breng tab terug naar tab bar via parent
        pass
    
    def mousePressEvent(self, event):
        # TODO: Detecteer resize rand of start drag
        pass
    
    def mouseMoveEvent(self, event):
        # TODO:
        # - Update cursor op basis van positie boven randen
        # - Behandel resize of drag op basis van status
        pass
    
    def mouseReleaseEvent(self, event):
        # TODO:
        # - Wis drag en resize status
        pass

    def _getResizeEdge(self, pos):
        # TODO:
        # - Bepaal bij welke rand(en) de positie in de buurt is
        # - Retourneer rand identificatie of None
        pass
    
    def _doResize(self, global_pos):
        # TODO:
        # - Bereken nieuwe geometrie op basis van resize rand
        # - Pas minimum grootte beperkingen toe
        # - Update widget geometrie
        pass


class CameraView(QWidget):
    """Camera view with live feed from stereo cameras."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # TODO:
        # - Stel zwarte achtergrond in
        # - Maak camera feed label
        # - Maak status label voor niet-verbonden status
        # - Initialiseer camera referenties (None initieel)
        # - Maak timer voor camera updates
        pass
    
    def setup_cameras(self, cameraL, cameraR, aimodel):
        # TODO:
        # - Bewaar camera en AI model referenties
        # - Controleer of camera's verbonden en geopend zijn
        # - Update status en start timer indien verbonden
        pass
    
    def update_camera_feed(self):
        # TODO:
        # - Haal frames op van beide camera's
        # - Verwerk met AI model indien beschikbaar
        # - Blend frames en converteer naar QPixmap
        # - Toon in camera label
        # - Behandel fouten en update verbindingsstatus
        pass
    
    def cv2_to_qt(self, cv_img):
        # TODO:
        # - Converteer OpenCV BGR afbeelding naar QImage
        # - Converteer naar QPixmap
        # - Schaal om in widget te passen met behoud van aspect ratio
        pass
    
    def resizeEvent(self, event):
        # TODO:
        # - Update camera label en status label posities
        # - Update camera feed indien verbonden
        pass
    
    def paintEvent(self, event):
        # TODO:
        # - Teken UI overlay (header balk met status/tijd)
        # - Indien verbonden, teken crosshair en REC indicator
        # - Indien niet verbonden, teken scan lijnen en inactieve status
        pass


class MapView(QWidget):
    """2D Map Visualization with PyQtGraph for displaying object positions and trails."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # TODO:
        # - Maak layout
        # - Initialiseer object tracking dictionaries
        # - Maak PyQtGraph PlotWidget
        # - Configureer aspect ratio en view limieten
        # - Voeg as labels toe
        # - Activeer raster
        # - Stel kleurenschema in voor object klassen
        # - Maak timer voor dummy data (optioneel)
        pass
    
    def _get_class_color(self, class_name):
        # TODO: Retourneer kleur tuple voor gegeven klasse naam
        pass
    
    def start_dummy_data(self):
        # TODO: Start timer voor dummy data generatie
        pass
    
    def stop_dummy_data(self):
        # TODO: Stop dummy data timer
        pass
    
    def _update_dummy_data(self):
        # TODO:
        # - Genereer willekeurige bewegende objecten ter demonstratie
        # - Roep update_object_positions aan met dummy data
        pass
    
    def update_object_positions(self, detected_objects):
        """
        Update kaart met real-time object posities vanuit stereo vision systeem.
        
        Args:
            detected_objects: Lijst van dicts met:
                - 'id': object identificatie (int)
                - 'x': laterale positie in meters of pixels
                - 'y': voorwaartse afstand in meters of pixels  
                - 'depth': stereo diepte in meters
                - 'label': object klasse naam
        """
        # TODO:
        # - Stop dummy data als echte data gebruikt wordt
        # - Wis plot en tekst items
        # - Verwerk elk gedetecteerd object:
        #   - Converteer pixel coördinaten naar meters indien nodig
        #   - Update object geschiedenis voor trails
        #   - Verkrijg kleur voor object klasse
        #   - Plot trail met verloop effect
        #   - Plot huidige positie als cirkel
        #   - Voeg tekst label toe met object info
        # - Ruim geschiedenis op voor objecten die niet meer gedetecteerd worden
        pass


class MainContentArea(QWidget):
    """Main content area with tear-off tabs."""
    
    TAB_CAMERA = 0
    TAB_MAP = 1
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # TODO:
        # - Initialiseer tab namen dictionary
        # - Stel initiële actieve tab in
        # - Laad bedrijfslogo indien beschikbaar
        # - Maak CameraView en MapView instanties
        # - Maak view container widget en layout
        # - Maak TearOffTabBar en voeg tabs toe
        # - Zorg dat tab bar bovenop ligt (raise_())
        pass
    
    def resizeEvent(self, event):
        # TODO:
        # - Positioneer view container om widget te vullen
        # - Positioneer tab bar linksboven
        # - Positioneer logo rechtsboven indien beschikbaar
        pass
    
    def activateTab(self, index):
        # TODO:
        # - Controleer of tab momenteel zweeft
        # - Update actieve tab index
        # - Update tab bar actieve status
        # - Toon de juiste view in hoofdgebied
        pass
    
    def _showMainView(self, index):
        # TODO:
        # - Wis huidige view uit layout
        # - Voeg nieuwe view toe aan layout
        pass
    
    def tearOffTab(self, index):
        # TODO:
        # - Controleer of floating pane al bestaat
        # - Verkrijg view voor deze tab
        # - Maak FloatingPane met view
        # - Verberg tab uit tab bar
        # - Schakel hoofdweergave over naar andere tab
        pass
    
    def returnFloatingPane(self, pane):
        # TODO:
        # - Verkrijg view en tab index van pane
        # - Toon tab weer in tab bar
        # - Herstel view naar views dictionary
        # - Verwijder pane en wis referentie
        pass