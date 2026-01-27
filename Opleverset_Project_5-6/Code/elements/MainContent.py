from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
import os
from .TearOffTabs import TearOffTabBar, FloatingPane
from .CameraView import CameraView
from .MapView import MapView

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