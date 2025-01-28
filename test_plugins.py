import os
import sys
import importlib.util
from PySide2.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QComboBox, QStackedWidget, QFormLayout, QLabel, QHBoxLayout)

from PySide2.QtCore import QCoreApplication, Qt
from PySide2.QtWebEngine import QtWebEngine

# Ensure proper initialization of QtWebEngine
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
QtWebEngine.initialize()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CET.SteelConnDesign Plugins")
        self.setGeometry(100, 100, 800, 600)

        # Main window layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Top section with dropdown
        self.top_widget = QWidget()
        self.top_layout = QHBoxLayout(self.top_widget)
        self.top_layout.setContentsMargins(5, 5, 5, 5)
        
        # Dropdown menu for plugins
        self.plugin_label = QLabel("Please select a tool from the list:")
        self.plugin_dropdown = QComboBox()
        self.plugin_dropdown.currentTextChanged.connect(self.load_and_show_plugin)
        
        self.top_layout.addWidget(self.plugin_label)
        self.top_layout.addWidget(self.plugin_dropdown)
        self.top_layout.addStretch()
        
        self.main_layout.addWidget(self.top_widget)

        # Content section
        self.content_widget = QWidget()
        self.content_layout = QHBoxLayout(self.content_widget)
        
        # Plugin UI container
        self.plugin_container = QStackedWidget()
        self.content_layout.addWidget(self.plugin_container)
        
        self.main_layout.addWidget(self.content_widget)

        # Plugin dictionaries
        self.plugin_widgets = {}  # Stores plugin name to plugin UI mapping
        self.plugin_paths = {}    # Stores plugin name to plugin path mapping
        self.plugin_info = []     # Stores plugin metadata (for sorting)
        
        # Preload plugin paths
        plugin_dir = "./"
        if os.path.exists(plugin_dir):
            self.scan_plugins(plugin_dir)

    def scan_plugins(self, plugin_dir):
        """
        Scan the plugin directory and record plugin paths.
        """
        for plugin_name in os.listdir(plugin_dir):
            plugin_path = os.path.join(plugin_dir, plugin_name, "plugin.py")
            if os.path.isfile(plugin_path):
                # Record plugin path
                self.plugin_paths[plugin_name] = plugin_path
                # Preload plugin metadata
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # Check for required metadata
                if hasattr(module, "description") and hasattr(module, "category") and hasattr(module, "load_order"):
                    self.plugin_info.append({
                        "name": plugin_name,
                        "path": plugin_path,
                        "description": module.description,
                        "category": module.category,
                        "load_order": module.load_order
                    })
                    
        # Sort plugins by load order
        self.plugin_info.sort(key=lambda x: x["load_order"])
        # Add plugin names to the dropdown menu
        for plugin in self.plugin_info:
            self.plugin_dropdown.addItem(plugin["name"])

    def load_and_show_plugin(self, plugin_name):
        """
        Dynamically load the plugin and display its UI.
        """
        if plugin_name in self.plugin_widgets:
            # Plugin already loaded, show it
            self.plugin_container.setCurrentWidget(self.plugin_widgets[plugin_name])
        else:
            # Find plugin metadata
            plugin_data = next((p for p in self.plugin_info if p["name"] == plugin_name), None)
            if plugin_data:
                # Dynamically load the plugin
                plugin_path = plugin_data["path"]
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # Check if PluginUI class is defined
                if hasattr(module, "PluginUI"):
                    plugin_widget = module.PluginUI()
                    self.plugin_widgets[plugin_name] = plugin_widget
                    self.plugin_container.addWidget(plugin_widget)
                    self.plugin_container.setCurrentWidget(plugin_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())