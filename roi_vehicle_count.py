from ultralytics import YOLO
import cv2
import numpy as np

# ============================================================
# SETTINGS
# ============================================================

IMAGE_PATH = "traffic1.png"

# Confidence threshold
CONFIDENCE = 0.30

# ============================================================
# LOAD IMAGE
# ============================================================

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("ERROR: Could not find traffic.jpeg")
    print("Make sure it is inside:")
    print("D:\\TrafficAI")
    exit()

print("Image loaded successfully.")

# ============================================================
# LOAD YOLO
# ============================================================

print("Loading YOLO model...")

model = YOLO("yolo11n.pt")

print("YOLO loaded successfully.")

# ============================================================
# VEHICLE CLASSES
# ============================================================

# COCO class IDs
#
# 2 = car
# 3 = motorcycle
# 5 = bus
# 7 = truck

VEHICLE_CLASSES = {
    2: "CAR",
    3: "MOTORCYCLE",
    5: "BUS",
    7: "TRUCK"
}

# ============================================================
# FOUR ROAD REGIONS
# ============================================================
#
# These coordinates are for the traffic image you showed.
#
# IMPORTANT:
# These are road APPROACH regions.
# The center of the junction is intentionally not included.
#
# ============================================================

ROIS = {

    # ---------------- NORTH ----------------
    #
    # Upper road approaching the junction
    #
    "NORTH": np.array([
        (680, 80),
        (1200, 80),
        (1280, 470),
        (680, 470)
    ], dtype=np.int32),


    # ---------------- EAST ----------------
    #
    # Right side road
    #
    "EAST": np.array([
        (1180, 430),
        (1640, 450),
        (1640, 800),
        (1450, 720),
        (1280, 620)
    ], dtype=np.int32),


    # ---------------- SOUTH ----------------
    #
    # Bottom road
    #
    "SOUTH": np.array([
        (250, 680),
        (1250, 680),
        (1550, 930),
        (100, 930)
    ], dtype=np.int32),


    # ---------------- WEST ----------------
    #
    # Left side road
    #
    "WEST": np.array([
        (0, 450),
        (500, 470),
        (850, 650),
        (700, 760),
        (0, 700)
    ], dtype=np.int32)
}

# ============================================================
# COUNTERS
# ============================================================

counts = {
    "NORTH": 0,
    "EAST": 0,
    "SOUTH": 0,
    "WEST": 0
}

# ============================================================
# YOLO DETECTION
# ============================================================

print("Detecting vehicles...")

results = model(
    image,
    classes=list(VEHICLE_CLASSES.keys()),
    conf=CONFIDENCE,
    verbose=False
)

print("Detection completed.")

# ============================================================
# PROCESS DETECTIONS
# ============================================================

for result in results:

    for box in result.boxes:

        # ----------------------------------------------------
        # Vehicle information
        # ----------------------------------------------------

        class_id = int(box.cls[0])
        confidence = float(box.conf[0])

        # Bounding box coordinates
        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0]
        )

        # ----------------------------------------------------
        # Bottom-center point
        # ----------------------------------------------------
        #
        # This point represents where the vehicle touches
        # the road.
        #
        # ----------------------------------------------------

        center_x = int((x1 + x2) / 2)
        bottom_y = int(y2)

        point = (
            center_x,
            bottom_y
        )

        detected_side = None

        # ----------------------------------------------------
        # CHECK FOUR ROIs
        # ----------------------------------------------------

        for side, polygon in ROIS.items():

            inside = cv2.pointPolygonTest(
                polygon,
                point,
                False
            )

            if inside >= 0:

                detected_side = side

                counts[side] += 1

                # Stop checking other regions
                break

        # ----------------------------------------------------
        # DRAW VEHICLE
        # ----------------------------------------------------

        if detected_side is not None:

            # GREEN = COUNTED
            color = (0, 255, 0)

            label = (
                f"{VEHICLE_CLASSES[class_id]} "
                f"{confidence:.2f} "
                f"{detected_side}"
            )

        else:

            # RED = IGNORED
            color = (0, 0, 255)

            label = (
                f"{VEHICLE_CLASSES[class_id]} "
                f"{confidence:.2f} "
                f"IGNORED"
            )

        # Bounding box
        cv2.rectangle(
            image,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        # Bottom center
        cv2.circle(
            image,
            point,
            6,
            color,
            -1
        )

        # Label
        cv2.putText(
            image,
            label,
            (
                x1,
                max(y1 - 10, 20)
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2
        )

# ============================================================
# DRAW FOUR ROI BORDERS
# ============================================================

for side, polygon in ROIS.items():

    cv2.polylines(
        image,
        [polygon],
        True,
        (255, 255, 0),
        3
    )

# ============================================================
# ROI LABELS
# ============================================================

roi_label_positions = {

    "NORTH": (800, 130),

    "EAST": (1430, 520),

    "SOUTH": (700, 850),

    "WEST": (100, 570)
}

for side, position in roi_label_positions.items():

    cv2.putText(
        image,
        side,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 0),
        3
    )

# ============================================================
# COUNT PANEL
# ============================================================

panel_x1 = 15
panel_y1 = 15
panel_x2 = 350
panel_y2 = 210

cv2.rectangle(
    image,
    (panel_x1, panel_y1),
    (panel_x2, panel_y2),
    (30, 30, 30),
    -1
)

# North
cv2.putText(
    image,
    f"NORTH : {counts['NORTH']}",
    (35, 60),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.8,
    (255, 255, 255),
    2
)

# East
cv2.putText(
    image,
    f"EAST  : {counts['EAST']}",
    (35, 100),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.8,
    (255, 255, 255),
    2
)

# South
cv2.putText(
    image,
    f"SOUTH : {counts['SOUTH']}",
    (35, 140),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.8,
    (255, 255, 255),
    2
)

# West
cv2.putText(
    image,
    f"WEST  : {counts['WEST']}",
    (35, 180),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.8,
    (255, 255, 255),
    2
)

# ============================================================
# PRINT RESULT IN CMD
# ============================================================

print()
print("====================================")
print("       VEHICLE COUNT RESULT")
print("====================================")

print(f"NORTH : {counts['NORTH']}")
print(f"EAST  : {counts['EAST']}")
print(f"SOUTH : {counts['SOUTH']}")
print(f"WEST  : {counts['WEST']}")

print("====================================")

# ============================================================
# SHOW IMAGE
# ============================================================

cv2.imshow(
    "4-Side Vehicle Detection",
    image
)

print()
print("GREEN = Vehicle counted")
print("RED   = Vehicle ignored")
print("YELLOW = Road ROI")
print()
print("Press Q to close.")

# ============================================================
# WAIT
# ============================================================

while True:

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cv2.destroyAllWindows()