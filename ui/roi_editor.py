from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QPushButton, QGroupBox, QTabWidget, QWidget, QMessageBox
)
from PySide6.QtCore import Qt
import config

class ROIEditorDialog(QDialog):
    """
    ROI Calibration Dialog for adjusting camera approach bounding boxes.
    Allows easy customization of NORTH, EAST, and SOUTH ROI coordinates.
    Saves results to roi_config.json.
    """
    def __init__(self, current_rois, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ROI Region Calibration")
        self.setMinimumSize(480, 420)
        self.rois = {d: list(current_rois[d]) for d in config.DIRECTIONS}
        
        self.spinboxes = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        header = QLabel("Adjust Traffic Approach Regions (ROIs)")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")
        layout.addWidget(header)

        desc = QLabel("Coordinates map to 1280x720 video resolution (x1, y1, x2, y2).")
        desc.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(desc)

        tabs = QTabWidget()
        tabs.setStyleSheet("QTabBar::tab { background: #1e293b; color: #f8fafc; padding: 8px 16px; } "
                           "QTabBar::tab:selected { background: #0284c7; font-weight: bold; }")

        for direction in config.DIRECTIONS:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            
            box_group = QGroupBox(f"{direction} Approach Box")
            box_layout = QVBoxLayout(box_group)

            roi = self.rois[direction]
            self.spinboxes[direction] = {}

            # Create controls for x1, y1, x2, y2
            params = [
                ("Min X (Left x1)", 0, 0, 1280, roi[0]),
                ("Min Y (Top y1)", 1, 0, 720, roi[1]),
                ("Max X (Right x2)", 2, 0, 1280, roi[2]),
                ("Max Y (Bottom y2)", 3, 0, 720, roi[3]),
            ]

            for label_text, idx, min_v, max_v, val in params:
                row = QHBoxLayout()
                lbl = QLabel(label_text)
                lbl.setMinimumWidth(140)
                lbl.setStyleSheet("font-weight: 600;")
                
                sb = QSpinBox()
                sb.setRange(min_v, max_v)
                sb.setValue(val)
                sb.setStyleSheet("background: #0f172a; color: #ffffff; padding: 4px; border: 1px solid #334155;")
                
                self.spinboxes[direction][idx] = sb
                row.addWidget(lbl)
                row.addWidget(sb)
                box_layout.addLayout(row)

            tab_layout.addWidget(box_group)
            tabs.addTab(tab, direction)

        layout.addWidget(tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset Defaults")
        reset_btn.setStyleSheet("background-color: #475569;")
        reset_btn.clicked.connect(self.reset_defaults)
        btn_layout.addWidget(reset_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #334155;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save & Apply ROIs")
        save_btn.setStyleSheet("background-color: #10b981;")
        save_btn.clicked.connect(self.save_and_apply)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def reset_defaults(self):
        for direction in config.DIRECTIONS:
            default_val = config.DEFAULT_ROIS[direction]
            for idx in range(4):
                self.spinboxes[direction][idx].setValue(default_val[idx])

    def save_and_apply(self):
        new_rois = {}
        for direction in config.DIRECTIONS:
            x1 = self.spinboxes[direction][0].value()
            y1 = self.spinboxes[direction][1].value()
            x2 = self.spinboxes[direction][2].value()
            y2 = self.spinboxes[direction][3].value()

            if x1 >= x2 or y1 >= y2:
                QMessageBox.warning(
                    self,
                    "Invalid Coordinates",
                    f"For {direction}: Min X/Y must be strictly smaller than Max X/Y."
                )
                return
            new_rois[direction] = [x1, y1, x2, y2]

        if config.save_rois(new_rois):
            self.rois = new_rois
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save ROI configuration to file.")
