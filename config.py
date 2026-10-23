import os
import json

# ============================================================
# ADAPTIVE TRAFFIC SIGNAL CONFIGURATION
# ============================================================

# Camera settings
CAMERA_ID = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# YOLO Model Settings
MODEL_NAME = "yolo11n.pt"
CONFIDENCE = 0.25

# COCO Vehicle Classes
# 2: CAR, 3: MOTORCYCLE, 5: BUS, 7: TRUCK
VEHICLE_CLASSES = {
    2: "CAR",
    3: "MOTORCYCLE",
    5: "BUS",
    7: "TRUCK"
}

# Default ROIs (x1, y1, x2, y2)
DEFAULT_ROIS = {
    "NORTH": [250, 20, 850, 360],
    "EAST": [650, 150, 1280, 570],
    "SOUTH": [250, 350, 850, 720]
}

# Traffic Signal Rules
SECONDS_PER_VEHICLE = 5
MAX_GREEN = 60
MIN_GREEN = 5
YELLOW_TIME = 3
PRIORITY_DIFFERENCE = 10

# Normal Traffic Cycle Sequence
DIRECTIONS = ["NORTH", "EAST", "SOUTH"]

ROI_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "roi_config.json")

def load_rois():
    """Load ROI coordinates from JSON file or return default ROIs."""
    if os.path.exists(ROI_CONFIG_FILE):
        try:
            with open(ROI_CONFIG_FILE, "r") as f:
                data = json.load(f)
                # Ensure all directions exist and formatted as list/tuple of 4 ints
                rois = {}
                for d in DIRECTIONS:
                    if d in data and len(data[d]) == 4:
                        rois[d] = [int(v) for v in data[d]]
                    else:
                        rois[d] = list(DEFAULT_ROIS[d])
                return rois
        except Exception as e:
            print(f"Warning: Failed to load {ROI_CONFIG_FILE}: {e}")
    return {k: list(v) for k, v in DEFAULT_ROIS.items()}

def save_rois(rois):
    """Save ROI coordinates to JSON file."""
    try:
        data = {d: [int(v) for v in rois[d]] for d in DIRECTIONS if d in rois}
        with open(ROI_CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving ROIs to {ROI_CONFIG_FILE}: {e}")
        return False
