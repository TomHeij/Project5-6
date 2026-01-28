import os
from PySide6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QPoint, QPointF
from PySide6.QtGui import QPainter, QPolygon, QColor, QPainterPath
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect



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
            bg_color = QColor("#c0c0c0")
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
        
        path.moveTo(0, 0)
        path.lineTo(w, 0)
        if self.is_last:
            path.lineTo(w, h - radius)
            path.quadTo(w, h, w - radius, h)
        else:
            path.lineTo(w, h)
        path.lineTo(0, h)
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


class TearOffTabManager(QWidget):    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_names = {}
        self.views = {}
        self.active_tab = 0
        self.floating_pane = None
        self.next_index = 0
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Tab bar
        self.tab_bar = TearOffTabBar(self)
        main_layout.addWidget(self.tab_bar)
        
        # View container
        self.view_container = QWidget(self)
        self.view_layout = QVBoxLayout(self.view_container)
        self.view_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.view_container)
    
    def add_view(self, name, widget):
        index = self.next_index
        self.next_index += 1
        
        self.tab_names[index] = name
        self.views[index] = widget
        # Add to tab bar (mark last tab with rounded corner)
        is_last = (True if index > 0 else False)
        self.tab_bar.addTab(name, index, is_last=is_last)
        
        # Show first view
        if index == 0:
            self.activateTab(0)
        
        return index
    
    def activateTab(self, index):
        if self.floating_pane and self.floating_pane.tab_index == index:
            return  # This tab is floating
        
        self.active_tab = index
        self.tab_bar.setActiveTab(index)
        self._showMainView(index)
    
    def _showMainView(self, index):
        # Don't show a view that's floating
        if self.floating_pane and self.floating_pane.tab_index == index:
            return
        
        # Clear current view
        while self.view_layout.count():
            item = self.view_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Add new view
        view = self.views[index]
        if view.parent() != self.view_container:
            view.setParent(self.view_container)
        self.view_layout.addWidget(view)
    
    def tearOffTab(self, index):
        view = self.views[index]
        
        # Remove view from current layout before tearing off
        for i in range(self.view_layout.count() - 1, -1, -1):
            item = self.view_layout.itemAt(i)
            if item and item.widget() == view:
                self.view_layout.removeItem(item)
        
        # Create floating pane
        self.floating_pane = FloatingPane(view, index, self.tab_names[index], self)
        self.floating_pane.show()
        self.floating_pane.raise_()
        
        # Hide the tab
        self.tab_bar.hideTab(index)
        
        # Switch to another tab as main view
        other_tab = next((i for i in self.views.keys() if i != index), None)
        if other_tab is not None:
            self.activateTab(other_tab)
    
    def returnFloatingPane(self, pane):
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
        
        # Activate this tab
        self.activateTab(tab_index)