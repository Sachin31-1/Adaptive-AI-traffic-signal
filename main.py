import sys
import os
from PySide6.QtWidgets import QApplication
from ui.dashboard import TrafficDashboard

def main():
    print("==================================================")
    print("  AI-BASED ADAPTIVE TRAFFIC SIGNAL MANAGEMENT     ")
    print("==================================================")
    print("Launching PySide6 Real-Time Dashboard...")
    
    app = QApplication(sys.argv)
    app.setApplicationName("AI Adaptive Traffic Signal")

    dashboard = TrafficDashboard()
    dashboard.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
