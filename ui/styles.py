# Dark Dashboard QSS Stylesheet

DARK_THEME_STYLE = """
/* Global Window Style */
QMainWindow, QDialog {
    background-color: #0b132b;
    color: #f9fafb;
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
}

QWidget {
    color: #f9fafb;
    font-family: 'Segoe UI', 'Inter', sans-serif;
}

/* Card Containers */
.QFrame, QFrame#CardContainer {
    background-color: #111827;
    border: 1px solid #1f2937;
    border-radius: 10px;
}

.QFrame:hover {
    border: 1px solid #374151;
}

/* Header Bar */
#HeaderBar {
    background-color: #0f172a;
    border-bottom: 2px solid #1e293b;
    padding: 12px 20px;
}

#HeaderTitle {
    color: #ffffff;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 1.5px;
}

#HeaderSubtitle {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 500;
}

#StatusBadge {
    background-color: #064e3b;
    color: #34d399;
    border: 1px solid #059669;
    border-radius: 14px;
    padding: 5px 14px;
    font-size: 12px;
    font-weight: 700;
}

#PillBadge {
    background-color: #1e293b;
    color: #38bdf8;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
}

/* Section Titles */
.QLabel#SectionTitle {
    color: #38bdf8;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* Signal Cards */
#SignalCard {
    background-color: #1e293b;
    border: 2px solid #334155;
    border-radius: 10px;
    padding: 12px;
}

#SignalCardActiveGREEN {
    background-color: #064e3b;
    border: 2px solid #10b981;
    border-radius: 10px;
    padding: 12px;
}

#SignalCardActiveYELLOW {
    background-color: #78350f;
    border: 2px solid #f59e0b;
    border-radius: 10px;
    padding: 12px;
}

#SignalCardInactive {
    background-color: #1e1b4b;
    border: 1px solid #312e81;
    border-radius: 10px;
    padding: 12px;
}

/* Main Display Countdown Timer */
#TimerDisplay {
    font-size: 48px;
    font-weight: 900;
    font-family: 'Consolas', 'Courier New', monospace;
    color: #10b981;
    letter-spacing: 2px;
}

#CurrentDirectionLabel {
    font-size: 26px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 1px;
}

#CurrentStateBadgeGREEN {
    background-color: #10b981;
    color: #022c22;
    border-radius: 6px;
    padding: 6px 18px;
    font-size: 16px;
    font-weight: 800;
}

#CurrentStateBadgeYELLOW {
    background-color: #f59e0b;
    color: #451a03;
    border-radius: 6px;
    padding: 6px 18px;
    font-size: 16px;
    font-weight: 800;
}

#CurrentStateBadgeRED {
    background-color: #ef4444;
    color: #450a0a;
    border-radius: 6px;
    padding: 6px 18px;
    font-size: 16px;
    font-weight: 800;
}

/* Priority Alert Box */
#PriorityAlertBox {
    background-color: #7f1d1d;
    border: 2px solid #ef4444;
    border-radius: 8px;
    padding: 10px;
}

#PriorityAlertText {
    color: #fef2f2;
    font-size: 13px;
    font-weight: 800;
}

/* Table Style */
QTableWidget {
    background-color: #0f172a;
    gridline-color: #1e293b;
    border: 1px solid #1e293b;
    border-radius: 6px;
    color: #f8fafc;
}

QHeaderView::section {
    background-color: #1e293b;
    color: #38bdf8;
    padding: 6px;
    font-weight: 700;
    font-size: 11px;
    border: none;
}

/* Progress Density Bars */
QProgressBar {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: 700;
    font-size: 11px;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
    border-radius: 5px;
}

/* Action Buttons */
QPushButton {
    background-color: #0284c7;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 700;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #0369a1;
}

QPushButton:pressed {
    background-color: #075985;
}

/* Tooltips */
QToolTip {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #38bdf8;
    border-radius: 4px;
    padding: 4px 8px;
}
"""
