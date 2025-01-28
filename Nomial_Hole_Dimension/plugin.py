from PySide2.QtWidgets import QHBoxLayout, QVBoxLayout, QFormLayout, QComboBox, QWidget, QGroupBox
from PySide2.QtCore import Qt
from PySide2.QtWebEngineWidgets import QWebEngineView
import json, re
from fractions import Fraction

import sys, os
module_path = os.getenv('APPDATA') + "/CET_SteelConnDesign"

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
description = "Nomial Hole Dimension"
category = "Steel"
load_order = 2

def extract_and_format_dimensions(dim_string):
    # Use regular expression to find all numbers in the string
    numbers = re.findall(r"\d+\.?\d*", dim_string)
    
    # Convert numbers to floats and format to two decimal places
    if len(numbers) == 2:
        formatted_numbers = [f"{float(num):.4f}" for num in numbers]
        return float(formatted_numbers[0]), float(formatted_numbers[1])
    else:
        raise ValueError("The input string does not contain exactly two numbers.")

def fraction_to_decimal(fraction_str):
    # Remove units like "in." or "mm" by splitting and keeping only the numeric part
    numeric_part = fraction_str.split(" in.")[0].split(" mm")[0]
    
    if " " in numeric_part:  # Handle mixed fractions like "1 1/8"
        whole, frac = numeric_part.split()
        decimal_value = int(whole) + float(Fraction(frac))
    elif "/" in numeric_part:  # Handle simple fractions like "1/2"
        decimal_value = float(Fraction(numeric_part))
    else:  # Handle whole numbers like "36"
        decimal_value = float(numeric_part)
    
    return decimal_value


class PluginUI(QWidget):
    def __init__(self):
        super().__init__()
        
        # Create dropdowns
        self.design_code_combo = QComboBox()
        self.design_code_combo.addItems(["AISC 13th", "AISC 14th", "AISC 15th"])
        self.design_code_combo.setCurrentText("AISC 14th")
        
        self.unit_list_combo = QComboBox()
        self.unit_list_combo.addItems(["Imperial Units", "Metric Units"])
        
        self.diameter_list_combo = QComboBox()
        self.imperial_dia_list = ["1/2 in.", "5/8 in.", "3/4 in.", "7/8 in.", "1 in.", "1 1/8 in.", "1 1/4 in.", "1 1/2 in."]
        self.metric_dia_list = ["16 mm", "20 mm", "22 mm", "24 mm", "27 mm", "30 mm", "33 mm", "36 mm"]
        self.diameter_list_combo.addItems(self.imperial_dia_list)
        
        self.hole_type_combo = QComboBox()
        self.hole_type_combo.addItems(["Standard", "Oversize", "Short Slot", "Long Slot"])
        
        # Add event listeners
        self.design_code_combo.currentTextChanged.connect(self.on_design_code_changed)
        self.unit_list_combo.currentTextChanged.connect(self.on_unit_list_changed)
        self.diameter_list_combo.currentTextChanged.connect(self.on_diameter_list_changed)
        self.hole_type_combo.currentTextChanged.connect(self.on_hole_type_changed)
        
        self.web_view = QWebEngineView()

        # Set initial values
        self.update()

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
        form_layout.addRow("Design Code", self.design_code_combo)
        form_layout.addRow("Measurement Unit", self.unit_list_combo)
        form_layout.addRow("Bolt Diameter", self.diameter_list_combo)
        form_layout.addRow("Hole Type", self.hole_type_combo)
        
        vbox = QVBoxLayout()
        group_box = QGroupBox()
        group_box.setTitle("Inputs")
        group_box.setLayout(form_layout)
        vbox.addWidget(group_box)

        return vbox
    def create_right_panel(self):
        group_box = QGroupBox("Results")
        group_layout = QVBoxLayout()
        
        # Web engine view for displaying HTML content
        group_layout.addWidget(self.web_view)
        group_box.setLayout(group_layout)

        vbox = QVBoxLayout()
        vbox.addWidget(group_box)
        
        return vbox
    
    def generate_slot_hole_svg(self, slot_width, slot_length, x, y, width, height):
        """
        Generate an SVG string with a slot hole, dimension lines, and arrows for the selected unit system.
        """
        arrow_size = 5  # Size of the arrowhead

        # Convert dimensions to imperial if needed
        if self.unit_list_combo.currentText() == "Imperial Units":
            width_label = slot_width / 25.4
            length_label = slot_length / 25.4
            unit_label = "in"
        else:
            width_label = slot_width
            length_label = slot_length
            unit_label = "mm"

        return f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
            <!-- Slot Hole -->
            <rect x="{x}" y="{y}" width="{slot_length}" height="{slot_width}" rx="{slot_width / 2}" 
                  ry="{slot_width / 2}" fill="lightgray" stroke="black" stroke-width="1" />

            <!-- Dimension Line for Length -->
            <line x1="{x}" y1="{y - 20}" x2="{x + slot_length}" y2="{y - 20}" stroke="black" stroke-width="1" />
            <!-- Left Arrow for Length -->
            <polygon points="{x},{y - 20} {x + arrow_size},{y - 25} {x + arrow_size},{y - 15}" fill="black" />
            <!-- Right Arrow for Length -->
            <polygon points="{x + slot_length},{y - 20} {x + slot_length - arrow_size},{y - 25} {x + slot_length - arrow_size},{y - 15}" fill="black" />
            <!-- Text for Length -->
            <text x="{x + slot_length / 2}" y="{y - 30}" font-size="14" text-anchor="middle" fill="black">{length_label} {unit_label}</text>

            <!-- Dimension Line for Width -->
            <line x1="{x - 20}" y1="{y}" x2="{x - 20}" y2="{y + slot_width}" stroke="black" stroke-width="1" />
            <!-- Top Arrow for Width -->
            <polygon points="{x - 20},{y} {x - 25},{y + arrow_size} {x - 15},{y + arrow_size}" fill="black" />
            <!-- Bottom Arrow for Width -->
            <polygon points="{x - 20},{y + slot_width} {x - 25},{y + slot_width - arrow_size} {x - 15},{y + slot_width - arrow_size}" fill="black" />
            <!-- Text for Width -->
            <text x="{x - 30}" y="{y + slot_width / 2}" font-size="14" text-anchor="end" fill="black"
                  dominant-baseline="middle">{width_label} {unit_label}</text>
        </svg>
        """
    
    def on_design_code_changed(self, value):
        self.update()

    def on_unit_list_changed(self, value):
        self.diameter_list_combo.clear()
        self.diameter_list_combo.addItems(self.imperial_dia_list if value == "Imperial Units" else self.metric_dia_list)
        self.update()

    def on_diameter_list_changed(self):
        self.update()

    def on_hole_type_changed(self):
        self.update()

    def update(self):
        design_code = self.design_code_combo.currentText()
        unit = self.unit_list_combo.currentText()
        hole_type = self.hole_type_combo.currentText()
        dia_str = self.diameter_list_combo.currentText()

        if not dia_str == "":
            diameter = fraction_to_decimal(dia_str)
            results = json.loads(CET_MODULE.get_hole_info(design_code, unit, diameter, hole_type))

            if hole_type == "Short Slot" or hole_type == "Long Slot":
                dimension = extract_and_format_dimensions(results["Hole diameter"]["content"])
                slot_width = dimension[0]
                slot_length = dimension[1]

                if unit == "Imperial Units":
                    slot_width *= 25.4
                    slot_length *= 25.4
        
                w = self.web_view.width()
                width = max(self.web_view.width() - 50, 300)
                height = max(self.web_view.height() - 100, 400)

                svg_content = self.generate_slot_hole_svg(slot_width, slot_length, x=100, y=50, width=width, height=height)
            else:
                svg_content = ""
            html_content = f"""
            <html>
            <body>
                Hole Dimension: {results["Hole diameter"]["content"]}<br>
                {results["Hole diameter reference"]["content"]}
                {svg_content}
            </body>
            </html>
            """
            self.web_view.setHtml(html_content)

