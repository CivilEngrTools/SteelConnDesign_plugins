from PySide2.QtWidgets import QHBoxLayout, QVBoxLayout, QFormLayout, QComboBox, QWidget, QTabWidget, QGroupBox
from PySide2.QtCore import Qt
from PySide2.QtWebEngineWidgets import QWebEngineView
import json
import sys, os
module_path = os.getenv('APPDATA') + "/CET_SteelConnDesign"

if not os.path.exists(module_path):
    module_path = "../"

# Add to sys.path
if module_path not in sys.path:
    sys.path.insert(0, module_path)

# Import your module
try:
    import CET_MODULE  # Replace CET_MODULE with your .pyd module name
except ImportError as e:
    print(f"Error importing module: {e}")

# Plugin metadata
author = "CivilEngrTools.com"
description = "Member Property"
category = "Steel"
load_order = 1

class PluginUI(QWidget):
    def __init__(self):
        super().__init__()
       
        self.shape_names = json.loads(CET_MODULE.get_shape_names())
        
        # Create dropdowns
        self.design_code_combo = QComboBox()
        self.design_code_combo.addItems(["AISC 13th", "AISC 14th", "AISC 15th"])
        self.design_code_combo.setCurrentText("AISC 14th")
        
        self.shape_list_combo = QComboBox()
        self.shape_list_combo.addItems(["W-Shapes", "Angles", "Rectangular HSS"])
        
        self.section_list_combo = QComboBox()
        self.section_list_combo.addItems(self.shape_names["AISC 14th"]["W-Shapes"])
        
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["A992", "A58", "A36"])
        
        # Add event listeners
        self.design_code_combo.currentTextChanged.connect(self.on_design_code_changed)
        self.shape_list_combo.currentTextChanged.connect(self.on_shape_list_changed)
        self.section_list_combo.currentTextChanged.connect(self.on_section_list_changed)
        
        self.web_view = QWebEngineView()

        # Variables to record activities
        self.design_code = None
        self.shape_list = None

        # Set initial values
        design_code = self.design_code_combo.currentText()
        shape = self.shape_list_combo.currentText()
        size = self.section_list_combo.currentText()
        sizes = CET_MODULE.get_member_section_size(design_code, shape, size)
        html_content = self.create_property_table(sizes)
        self.web_view.setHtml(html_content)

        # layout
        main_layout = QHBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)  # Align the VBox to the top

        main_layout.addLayout(self.create_left_panel())
        main_layout.addLayout(self.create_right_panel())
        self.setLayout(main_layout)

    def create_left_panel(self):
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignTop | Qt.AlignLeft)
        form_layout.setHorizontalSpacing(50)  # Add more space between label and dropdown
        form_layout.setVerticalSpacing(8)   # Add vertical spacing between rows
        
        # Add widgets to the form layout
        form_layout.addRow("Design code", self.design_code_combo)
        form_layout.addRow("Shape List", self.shape_list_combo)
        form_layout.addRow("Section list", self.section_list_combo)
        form_layout.addRow("Grade", self.grade_combo)
        
        vbox = QVBoxLayout()
        group_box = QGroupBox()
        group_box.setTitle("Inputs")
        group_box.setLayout(form_layout)
        vbox.addWidget(group_box)

        return vbox
    def create_property_table(self, values):
        shape = self.shape_list_combo.currentText()
        
        symbols_dict = {
            "W-Shapes": ["A", "d", "d_{det}", "t_w", "t_{w,det}", "b_f", "b_{f,det}", "t_f", "t_{f,det}", "k_{des}", "k_{det}", "k_1", "T", "g", "W_t", "I_x", "S_x", "r_x", "Z_x", "I_y", "S_y", "r_y", "Z_y", "J", "C_w"],
            "Angles": ["k", "W_t", "A", "I_x", "S_x", "r_x", "\overline{y}", "Z_x", "y_p", "J", "Cw", "r_o", "I_y", "S_y", "r_y", "\overline{x}", "Z_y", "x_p", "I_z", "S_z", "r_z", "T_{\\alpha}", "Qs", "d", "B", "t"],
            "Default": ["t_{des}", "t_{nom}", "W", "A", "I_x", "S_x", "r_x", "Z_x", "I_y", "S_y", "r_y", "Z_y", "J", "C", "H_t", "B"]
        }
        
        symbols = symbols_dict.get(shape, symbols_dict["Default"])
        
        rows = ""
        num_pairs = len(symbols) // 2 + len(symbols) % 2
        for i in range(num_pairs):
            left_symbol = symbols[i]
            right_symbol = symbols[i + num_pairs] if i + num_pairs < len(symbols) else ""
            left_value = values[i] if i < len(values) else ""
            right_value = values[i + num_pairs] if i + num_pairs < len(values) else ""
            rows += f"<tr><td>\\({left_symbol}\\)</td><td>{left_value}</td><td>\\({right_symbol}\\)</td><td>{right_value}</td></tr>"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Member Property</title>
            <style>
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    table-layout: fixed;
                }}
                th, td {{
                    border: 1px solid black;
                    text-align: center;
                    padding: 3px;
                    width: 25%;
                    word-wrap: break-word;
                }}
            </style>
            <script type="text/javascript" id="MathJax-script" async
                src="https://cdn.jsdelivr.net/npm/mathjax@3.1.2/es5/tex-svg.js">
            </script>
        </head>
        <body>
        <table>
        <tr><th>Item</th><th>Value</th><th>Item</th><th>Value</th></tr>
        {rows}
        </table>
        </body>
        </html>
        """
        
        return html_content

    def create_right_panel(self):
        group_box = QGroupBox("Results")
        group_layout = QVBoxLayout()
        
        # Web engine view for displaying HTML content
        group_layout.addWidget(self.web_view)
        group_box.setLayout(group_layout)

        vbox = QVBoxLayout()
        vbox.addWidget(group_box)
        
        return vbox
    
    def on_design_code_changed(self, value):
        self.design_code = value  
        self.section_list_combo.clear()
        shape = self.shape_list_combo.currentText()
        use_code = "AISC 14th" if value == "AISC 13th" else value
        self.section_list_combo.addItems(self.shape_names[use_code][shape])  
        self.update()

    def on_shape_list_changed(self, value):
        self.shape_list = value 
        self.section_list_combo.clear()
        design_code = self.design_code_combo.currentText()
        use_code = "AISC 14th" if design_code == "AISC 13th" else design_code
        self.section_list_combo.addItems(self.shape_names[use_code][value])  
        self.update()
    
    def on_section_list_changed(self):
        self.update()

    def update(self):
        design_code = self.design_code_combo.currentText()
        shape = self.shape_list_combo.currentText()
        size = self.section_list_combo.currentText()
        if not size == "":
            sizes = CET_MODULE.get_member_section_size(design_code, shape, size)
            html_content = self.create_property_table(sizes)
            self.web_view.setHtml(html_content)
