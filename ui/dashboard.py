import sys
import time
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QIcon

import config
from detection import YOLOVehicleDetector
from traffic_controller import TrafficController
from ui.styles import DARK_THEME_STYLE
from ui.roi_editor import ROIEditorDialog

# ============================================================
# VIDEO PROCESSING & DETECTION THREAD
# ============================================================

class VideoThread(QThread):
    """
    Background worker thread for video frame capture, YOLO detection,
    and adaptive traffic controller logic. Keeps UI responsive at 30+ FPS.
    """
    frame_processed = Signal(QImage, dict, int, dict)
    fps_updated = Signal(float)

    def __init__(self, camera_id=config.CAMERA_ID):
        super().__init__()
        self.camera_id = camera_id
        self.running = True
        self.rois = config.load_rois()
        self.detector = None
        self.controller = TrafficController()

    def update_rois(self, new_rois):
        self.rois = new_rois

    def run(self):
        # Initialize YOLO detector inside worker thread
        self.detector = YOLOVehicleDetector()
        cap = cv2.VideoCapture(self.camera_id)

        if not cap.isOpened():
            print(f"Warning: Could not open camera {self.camera_id}. Initializing synthetic video stream...")
            cap = None

        if cap:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

        prev_time = time.time()
        frame_count = 0
        fps = 0.0

        # Create dummy background if camera unavailable
        blank_frame = np.zeros((config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), dtype=np.uint8)
        cv2.putText(blank_frame, "WEBCAM STREAM LIVE", (450, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (100, 100, 100), 2)

        while self.running:
            if cap:
                ret, frame = cap.read()
                if not ret:
                    # Reset capture loop if end of video stream
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    if not ret:
                        frame = blank_frame.copy()
            else:
                frame = blank_frame.copy()

            # Process YOLO detection
            active_dir = self.controller.current_direction
            curr_state = self.controller.current_state
            
            processed_frame, counts, total_vehicles, _ = self.detector.process_frame(
                frame, self.rois, active_direction=active_dir, current_state=curr_state
            )

            # Update Traffic Controller State Machine
            state_data = self.controller.update(counts)

            # Calculate FPS
            frame_count += 1
            now = time.time()
            if now - prev_time >= 1.0:
                fps = frame_count / (now - prev_time)
                frame_count = 0
                prev_time = now
                self.fps_updated.emit(fps)

            # Convert OpenCV BGR frame to QImage for PySide6
            h, w, ch = processed_frame.shape
            bytes_per_line = ch * w
            rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

            # Emit signal to UI thread
            self.frame_processed.emit(q_img, counts, total_vehicles, state_data)

            # Small sleep to keep CPU efficient
            self.msleep(10)

        if cap:
            cap.release()

    def stop(self):
        self.running = False
        self.wait()


# ============================================================
# MAIN DASHBOARD WINDOW
# ============================================================

class TrafficDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI-Based Adaptive Traffic Signal System")
        self.resize(1600, 950)
        self.setMinimumSize(1280, 800)
        self.setStyleSheet(DARK_THEME_STYLE)

        # Start Video Processing Thread
        self.video_thread = VideoThread()
        self.video_thread.frame_processed.connect(self.on_frame_processed)
        self.video_thread.fps_updated.connect(self.on_fps_updated)

        self.init_ui()
        self.video_thread.start()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 1. TOP HEADER BAR
        header_bar = self.create_header_bar()
        main_layout.addWidget(header_bar)

        # 2. MAIN CONTENT AREA (3 Columns / Split View)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # LEFT SIDE: LIVE CAMERA FEED
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, stretch=6)

        # RIGHT SIDE: SIGNAL CONTROLLER & ANALYTICS
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, stretch=5)

        main_layout.addLayout(content_layout, stretch=1)

    # --------------------------------------------------------
    # HEADER BAR
    # --------------------------------------------------------
    def create_header_bar(self):
        header_frame = QFrame()
        header_frame.setObjectName("HeaderBar")
        layout = QHBoxLayout(header_frame)
        layout.setContentsMargins(10, 5, 10, 5)

        # Titles
        title_box = QVBoxLayout()
        t1 = QLabel("AI-BASED ADAPTIVE TRAFFIC SIGNAL")
        t1.setObjectName("HeaderTitle")
        t2 = QLabel("Real-Time Computer Vision Traffic Management System")
        t2.setObjectName("HeaderSubtitle")
        title_box.addWidget(t1)
        title_box.addWidget(t2)
        layout.addLayout(title_box)

        layout.addStretch()

        # System Badges
        p1 = QLabel("YOLO v11n")
        p1.setObjectName("PillBadge")
        p2 = QLabel("LIVE CAMERA")
        p2.setObjectName("PillBadge")
        p3 = QLabel("ADAPTIVE CONTROL")
        p3.setObjectName("PillBadge")
        
        status_lbl = QLabel("● SYSTEM ONLINE")
        status_lbl.setObjectName("StatusBadge")

        layout.addWidget(p1)
        layout.addWidget(p2)
        layout.addWidget(p3)
        layout.addSpacing(10)
        layout.addWidget(status_lbl)
        layout.addSpacing(15)

        # ROI Calibration Button
        calib_btn = QPushButton("⚙ ROI Calibration")
        calib_btn.setToolTip("Adjust approach bounding regions for camera setup")
        calib_btn.clicked.connect(self.open_roi_editor)
        layout.addWidget(calib_btn)

        return header_frame

    # --------------------------------------------------------
    # LEFT PANEL: LIVE CAMERA FEED
    # --------------------------------------------------------
    def create_left_panel(self):
        panel = QFrame()
        panel.setObjectName("CardContainer")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)

        title_box = QHBoxLayout()
        title = QLabel("LIVE CAMERA FEED & YOLO DETECTION")
        title.setObjectName("SectionTitle")
        title_box.addWidget(title)
        title_box.addStretch()
        
        self.camera_status_lbl = QLabel("CAMERA 0 | 1280x720")
        self.camera_status_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        title_box.addWidget(self.camera_status_lbl)
        layout.addLayout(title_box)

        # Video Frame Label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #030712; border: 1px solid #1e293b; border-radius: 8px;")
        self.video_label.setMinimumSize(640, 480)
        layout.addWidget(self.video_label, stretch=1)

        return panel

    # --------------------------------------------------------
    # RIGHT PANEL: CONTROLLER & SIGNALS
    # --------------------------------------------------------
    def create_right_panel(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # TOP ROW: MAIN SIGNAL COUNTDOWN DISPLAY
        countdown_card = self.create_main_signal_card()
        layout.addWidget(countdown_card)

        # MIDDLE ROW: 3 TRAFFIC APPROACH SIGNAL CARDS
        signals_card = self.create_signals_panel()
        layout.addWidget(signals_card)

        # ADAPTIVE CONTROL & PRIORITY BANNER
        adaptive_card = self.create_adaptive_control_card()
        layout.addWidget(adaptive_card)

        # TRAFFIC DENSITY & GREEN TIME ALLOCATION
        density_card = self.create_density_card()
        layout.addWidget(density_card)

        # SYSTEM METRICS SUMMARY
        metrics_card = self.create_metrics_panel()
        layout.addWidget(metrics_card)

        scroll.setWidget(container)
        return scroll

    # --------------------------------------------------------
    # SECTION 1: MAIN SIGNAL DISPLAY CARD
    # --------------------------------------------------------
    def create_main_signal_card(self):
        card = QFrame()
        card.setObjectName("CardContainer")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)

        # Direction & State Box
        dir_box = QVBoxLayout()
        lbl = QLabel("CURRENT ACTIVE SIGNAL")
        lbl.setObjectName("SectionTitle")
        
        self.current_dir_lbl = QLabel("NORTH")
        self.current_dir_lbl.setObjectName("CurrentDirectionLabel")

        self.current_state_lbl = QLabel("GREEN")
        self.current_state_lbl.setObjectName("CurrentStateBadgeGREEN")
        self.current_state_lbl.setAlignment(Qt.AlignCenter)

        dir_box.addWidget(lbl)
        dir_box.addWidget(self.current_dir_lbl)
        dir_box.addWidget(self.current_state_lbl)
        layout.addLayout(dir_box)

        layout.addStretch()

        # Large Timer Display
        timer_box = QVBoxLayout()
        timer_lbl = QLabel("COUNTDOWN TIMER")
        timer_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold; text-align: right;")
        timer_lbl.setAlignment(Qt.AlignRight)

        self.timer_display = QLabel("00:05")
        self.timer_display.setObjectName("TimerDisplay")
        self.timer_display.setAlignment(Qt.AlignRight)

        timer_box.addWidget(timer_lbl)
        timer_box.addWidget(self.timer_display)
        layout.addLayout(timer_box)

        return card

    # --------------------------------------------------------
    # SECTION 2: 3 APPROACH SIGNAL CARDS
    # --------------------------------------------------------
    def create_signals_panel(self):
        card = QFrame()
        card.setObjectName("CardContainer")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("TRAFFIC APPROACH SIGNALS")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(10)

        self.approach_cards = {}
        for d in config.DIRECTIONS:
            c = QFrame()
            c.setObjectName("SignalCardInactive")
            c_layout = QVBoxLayout(c)
            c_layout.setContentsMargins(10, 10, 10, 10)

            # Header Direction Title
            d_name = QLabel(d)
            d_name.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
            
            # State Indicator Light Text
            state_lbl = QLabel("● RED")
            state_lbl.setStyleSheet("color: #ef4444; font-weight: 800; font-size: 13px;")

            # Vehicle Count
            count_lbl = QLabel("00 VEHICLES")
            count_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")

            # Green Time
            gt_lbl = QLabel("GREEN: 0 SEC")
            gt_lbl.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: bold;")

            c_layout.addWidget(d_name)
            c_layout.addWidget(state_lbl)
            c_layout.addWidget(count_lbl)
            c_layout.addWidget(gt_lbl)

            cards_layout.addWidget(c)
            self.approach_cards[d] = {
                "frame": c,
                "state": state_lbl,
                "count": count_lbl,
                "green": gt_lbl
            }

        layout.addLayout(cards_layout)
        return card

    # --------------------------------------------------------
    # SECTION 3: ADAPTIVE CONTROL & PRIORITY ALERT
    # --------------------------------------------------------
    def create_adaptive_control_card(self):
        card = QFrame()
        card.setObjectName("CardContainer")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("ADAPTIVE TRAFFIC CONTROL")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        info_layout = QHBoxLayout()
        info_layout.setSpacing(15)

        # Mode Box
        m_box = QVBoxLayout()
        m_title = QLabel("CURRENT MODE")
        m_title.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold;")
        self.mode_val_lbl = QLabel("NORMAL")
        self.mode_val_lbl.setStyleSheet("color: #10b981; font-size: 14px; font-weight: 800;")
        m_box.addWidget(m_title)
        m_box.addWidget(self.mode_val_lbl)
        info_layout.addLayout(m_box)

        # Cycle Flow Box
        c_box = QVBoxLayout()
        c_title = QLabel("NORMAL CYCLE FLOW")
        c_title.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold;")
        self.cycle_flow_lbl = QLabel("NORTH ➔ EAST ➔ SOUTH")
        self.cycle_flow_lbl.setStyleSheet("color: #38bdf8; font-size: 13px; font-weight: 700;")
        c_box.addWidget(c_title)
        c_box.addWidget(self.cycle_flow_lbl)
        info_layout.addLayout(c_box)

        # Threshold Box
        t_box = QVBoxLayout()
        t_title = QLabel("PRIORITY THRESHOLD")
        t_title.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold;")
        t_val = QLabel("+10 VEHICLES")
        t_val.setStyleSheet("color: #f59e0b; font-size: 13px; font-weight: 800;")
        t_box.addWidget(t_title)
        t_box.addWidget(t_val)
        info_layout.addLayout(t_box)

        layout.addLayout(info_layout)

        # Priority Alert Banner Box (Hidden by default, shown during priority)
        self.priority_alert_box = QFrame()
        self.priority_alert_box.setObjectName("PriorityAlertBox")
        pa_layout = QVBoxLayout(self.priority_alert_box)
        pa_layout.setContentsMargins(8, 8, 8, 8)

        self.priority_alert_lbl = QLabel("⚠ PRIORITY TRAFFIC DETECTED")
        self.priority_alert_lbl.setObjectName("PriorityAlertText")
        self.priority_detail_lbl = QLabel("EAST has 15 vehicles (NORTH has 4). Difference: +11")
        self.priority_detail_lbl.setStyleSheet("color: #ffffff; font-size: 11px;")

        pa_layout.addWidget(self.priority_alert_lbl)
        pa_layout.addWidget(self.priority_detail_lbl)

        layout.addWidget(self.priority_alert_box)
        self.priority_alert_box.setVisible(False)

        return card

    # --------------------------------------------------------
    # SECTION 4: DENSITY BARS & GREEN TIME ALLOCATION
    # --------------------------------------------------------
    def create_density_card(self):
        card = QFrame()
        card.setObjectName("CardContainer")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("APPROACH TRAFFIC DENSITY & GREEN TIME")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(10)

        self.density_bars = {}
        self.density_count_lbls = {}

        for idx, d in enumerate(config.DIRECTIONS):
            # Direction Label
            lbl = QLabel(d)
            lbl.setStyleSheet("font-weight: 800; color: #ffffff; font-size: 12px;")
            grid.addWidget(lbl, idx, 0)

            # Density Progress Bar
            bar = QProgressBar()
            bar.setRange(0, 20) # 0 to 20 vehicles scale
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(18)
            grid.addWidget(bar, idx, 1)

            # Count & Green Time Label
            cnt_lbl = QLabel("0 vehicles | 0s Green")
            cnt_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
            grid.addWidget(cnt_lbl, idx, 2)

            self.density_bars[d] = bar
            self.density_count_lbls[d] = cnt_lbl

        layout.addLayout(grid)

        # Rule Legend Footer
        legend = QLabel("Rule: 1 Vehicle = 5 Sec | Minimum = 5 Sec | Maximum = 60 Sec")
        legend.setStyleSheet("color: #64748b; font-size: 10px; font-style: italic; font-weight: bold;")
        layout.addWidget(legend)

        return card

    # --------------------------------------------------------
    # SECTION 5: SYSTEM METRICS PANEL
    # --------------------------------------------------------
    def create_metrics_panel(self):
        card = QFrame()
        card.setObjectName("CardContainer")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)

        metrics = [
            ("TOTAL VEHICLES", "0", "tot_veh_val"),
            ("CYCLE COUNT", "1", "cycle_val"),
            ("ACTIVE APPROACH", "NORTH", "act_app_val"),
            ("LIVE FPS", "0.0", "fps_val")
        ]

        self.metric_lbls = {}
        for title, default_val, key in metrics:
            box = QVBoxLayout()
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("color: #94a3b8; font-size: 9px; font-weight: bold;")
            v_lbl = QLabel(default_val)
            v_lbl.setStyleSheet("color: #38bdf8; font-size: 15px; font-weight: 800;")
            box.addWidget(t_lbl)
            box.addWidget(v_lbl)
            layout.addLayout(box)
            self.metric_lbls[key] = v_lbl

        return card

    # --------------------------------------------------------
    # SLOTS & UPDATES
    # --------------------------------------------------------
    @Slot(QImage, dict, int, dict)
    def on_frame_processed(self, q_img, counts, total_vehicles, state_data):
        # 1. Update Video Frame Display
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)

        # 2. Update Main Countdown Signal Card
        curr_dir = state_data["current_direction"]
        curr_state = state_data["current_state"]
        rem_sec = state_data["remaining_seconds"]

        self.current_dir_lbl.setText(curr_dir)
        self.timer_display.setText(f"00:{rem_sec:02d}")

        if curr_state == "GREEN":
            self.current_state_lbl.setText("GREEN")
            self.current_state_lbl.setObjectName("CurrentStateBadgeGREEN")
            self.timer_display.setStyleSheet("color: #10b981;")
        elif curr_state == "YELLOW":
            self.current_state_lbl.setText("YELLOW")
            self.current_state_lbl.setObjectName("CurrentStateBadgeYELLOW")
            self.timer_display.setStyleSheet("color: #f59e0b;")
        else:
            self.current_state_lbl.setText("RED")
            self.current_state_lbl.setObjectName("CurrentStateBadgeRED")
            self.timer_display.setStyleSheet("color: #ef4444;")

        # Re-apply stylesheet to update badge background
        self.current_state_lbl.setStyle(self.current_state_lbl.style())

        # 3. Update 3 Approach Signal Cards
        green_times = state_data["green_times"]
        for d in config.DIRECTIONS:
            c_widgets = self.approach_cards[d]
            cnt = counts.get(d, 0)
            gt = green_times.get(d, 0)

            c_widgets["count"].setText(f"{cnt:02d} VEHICLES")
            c_widgets["green"].setText(f"GREEN: {gt} SEC")

            if d == curr_dir:
                if curr_state == "GREEN":
                    c_widgets["frame"].setObjectName("SignalCardActiveGREEN")
                    c_widgets["state"].setText("● GREEN")
                    c_widgets["state"].setStyleSheet("color: #34d399; font-weight: 800; font-size: 13px;")
                else:
                    c_widgets["frame"].setObjectName("SignalCardActiveYELLOW")
                    c_widgets["state"].setText("● YELLOW")
                    c_widgets["state"].setStyleSheet("color: #fbbf24; font-weight: 800; font-size: 13px;")
            else:
                c_widgets["frame"].setObjectName("SignalCardInactive")
                c_widgets["state"].setText("● RED")
                c_widgets["state"].setStyleSheet("color: #ef4444; font-weight: 800; font-size: 13px;")

            c_widgets["frame"].setStyle(c_widgets["frame"].style())

        # 4. Update Adaptive Control & Priority Alert
        is_priority = state_data["priority_active"]
        p_info = state_data["priority_info"]

        if is_priority or state_data.get("last_priority_direction"):
            self.mode_val_lbl.setText("PRIORITY MODE")
            self.mode_val_lbl.setStyleSheet("color: #ef4444; font-size: 14px; font-weight: 800;")
        else:
            self.mode_val_lbl.setText("NORMAL CYCLE")
            self.mode_val_lbl.setStyleSheet("color: #10b981; font-size: 14px; font-weight: 800;")

        if is_priority and p_info:
            self.priority_alert_box.setVisible(True)
            self.priority_alert_lbl.setText(f"⚠ PRIORITY TRAFFIC DETECTED ➔ {p_info['priority_dir']}")
            self.priority_detail_lbl.setText(
                f"{p_info['priority_dir']} has {p_info['priority_count']} vehicles ({p_info['current_dir']} has {p_info['current_count']}). "
                f"Difference: +{p_info['diff']}"
            )
        else:
            self.priority_alert_box.setVisible(False)

        # Highlight current active approach in cycle sequence text
        cycle_str = ""
        for idx, d in enumerate(config.DIRECTIONS):
            if d == curr_dir:
                cycle_str += f"[{d}]"
            else:
                cycle_str += f"{d}"
            if idx < len(config.DIRECTIONS) - 1:
                cycle_str += " ➔ "
        self.cycle_flow_lbl.setText(cycle_str)

        # 5. Update Traffic Density Bars & Allocation
        for d in config.DIRECTIONS:
            cnt = counts.get(d, 0)
            gt = green_times.get(d, 0)
            self.density_bars[d].setValue(min(cnt, 20))
            self.density_count_lbls[d].setText(f"{cnt} vehicles | {gt}s Green")

        # 6. Update System Metrics Summary
        self.metric_lbls["tot_veh_val"].setText(str(total_vehicles))
        self.metric_lbls["cycle_val"].setText(str(state_data["cycle_count"]))
        self.metric_lbls["act_app_val"].setText(curr_dir)

    @Slot(float)
    def on_fps_updated(self, fps):
        self.metric_lbls["fps_val"].setText(f"{fps:.1f}")

    def open_roi_editor(self):
        dialog = ROIEditorDialog(self.video_thread.rois, self)
        if dialog.exec():
            # Update video thread with new ROI bounds
            self.video_thread.update_rois(dialog.rois)

    def closeEvent(self, event):
        self.video_thread.stop()
        event.accept()
