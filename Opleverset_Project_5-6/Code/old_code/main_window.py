"""
MainWindow - Generated from MainWindow.ui as pure Python code.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt


class MainWindow(QWidget):
    """Main window widget with container for tearoff tabs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi()
    
    def setupUi(self):
        """Set up the user interface."""
        # Main window properties
        self.setGeometry(0, 0, 1200, 800)
        self.setWindowTitle("Tear-Off Tabs Demo")
        self.setStyleSheet("background: #2c3e50;")
        
        # Main horizontal layout
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        
        # Main content area widget
        self.mainContentArea = QWidget()
        self.mainContentArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Expanding, Expanding
        
        # Vertical layout for main content area
        self.verticalLayout = QVBoxLayout(self.mainContentArea)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        
        # Add main content area to main layout
        self.horizontalLayout.addWidget(self.mainContentArea)
        
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
