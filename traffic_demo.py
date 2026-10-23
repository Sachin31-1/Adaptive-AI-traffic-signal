from ultralytics import YOLO
import cv2
import time

# ============================================================
# 3-DIRECTION DYNAMIC TRAFFIC SIGNAL
# ============================================================

CAMERA_ID = 0

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

MODEL_NAME = "yolo11n.pt"
CONFIDENCE = 0.25

# Vehicle classes
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
# ROI
#
# Larger regions for easier demo detection.
#
# NORTH:
# x = 300 to 850
# y = 20 to 350
#
# EAST:
# x = 650 to 1280
# y = 180 to 570
#
# SOUTH:
# x = 300 to 850
# y = 350 to 720
# ============================================================

ROIS = {
    "NORTH": (300, 20, 850, 350),

    "EAST": (650, 180, 1280, 570),

    "SOUTH": (300, 350, 850, 720)
}

# ============================================================
# SIGNAL SETTINGS
# ============================================================

SECONDS_PER_VEHICLE = 5

MAX_GREEN = 60

MIN_GREEN = 5

YELLOW_TIME = 3

# Fixed cycle
DIRECTIONS = [
    "NORTH",
    "EAST",
    "SOUTH"
]

# ============================================================
# LOAD YOLO
# ============================================================

print("Loading YOLO model...")

model = YOLO(MODEL_NAME)

print("YOLO loaded successfully.")

# ============================================================
# CAMERA
# ============================================================

cap = cv2.VideoCapture(CAMERA_ID)

if not cap.isOpened():

    print("ERROR: Webcam could not be opened.")

    exit()

cap.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    FRAME_WIDTH
)

cap.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    FRAME_HEIGHT
)

# ============================================================
# FUNCTIONS
# ============================================================

def inside_roi(point, roi):

    x, y = point

    x1, y1, x2, y2 = roi

    return (
        x1 <= x <= x2
        and
        y1 <= y <= y2
    )


def calculate_green_time(vehicle_count):

    # 1 vehicle = 5 seconds
    green = vehicle_count * SECONDS_PER_VEHICLE

    # Minimum green
    if green < MIN_GREEN:

        green = MIN_GREEN

    # Maximum green = 60 seconds
    if green > MAX_GREEN:

        green = MAX_GREEN

    return green


def draw_roi(frame, name, roi, count):

    x1, y1, x2, y2 = roi

    # ROI rectangle
    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (255, 255, 0),
        2
    )

    # Direction
    cv2.putText(
        frame,
        name,
        (x1 + 10, y1 + 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 0),
        2
    )

    # Count
    cv2.putText(
        frame,
        f"Vehicles: {count}",
        (x1 + 10, y1 + 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )


def draw_signal(frame, direction, state, remaining):

    # Signal panel
    x = 20
    y = 20

    cv2.rectangle(
        frame,
        (x, y),
        (320, y + 130),
        (30, 30, 30),
        -1
    )

    # State colour
    if state == "GREEN":

        color = (0, 255, 0)

    elif state == "YELLOW":

        color = (0, 255, 255)

    else:

        color = (0, 0, 255)

    # Signal circle
    cv2.circle(
        frame,
        (65, 75),
        30,
        color,
        -1
    )

    # Direction
    cv2.putText(
        frame,
        direction,
        (110, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2
    )

    # State
    cv2.putText(
        frame,
        state,
        (110, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2
    )

    # Timer
    cv2.putText(
        frame,
        f"{remaining}s",
        (230, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


# ============================================================
# INITIAL VALUES
# ============================================================

counts = {
    "NORTH": 0,
    "EAST": 0,
    "SOUTH": 0
}

green_times = {
    "NORTH": 5,
    "EAST": 5,
    "SOUTH": 5
}

# Start with NORTH
current_index = 0

current_direction = DIRECTIONS[current_index]

current_state = "GREEN"

phase_duration = MIN_GREEN

phase_start = time.time()

cycle_number = 1

# ============================================================
# MAIN LOOP
# ============================================================

while True:

    ret, frame = cap.read()

    if not ret:

        print("Camera frame error.")

        break

    frame = cv2.resize(
        frame,
        (FRAME_WIDTH, FRAME_HEIGHT)
    )

    # ========================================================
    # YOLO
    # ========================================================

    results = model(
        frame,
        classes=list(VEHICLE_CLASSES.keys()),
        conf=CONFIDENCE,
        verbose=False
    )

    new_counts = {
        "NORTH": 0,
        "EAST": 0,
        "SOUTH": 0
    }

    # ========================================================
    # VEHICLE DETECTION
    # ========================================================

    for result in results:

        for box in result.boxes:

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            x1 = int(x1)
            y1 = int(y1)
            x2 = int(x2)
            y2 = int(y2)

            confidence = float(box.conf[0])

            class_id = int(box.cls[0])

            vehicle_name = VEHICLE_CLASSES.get(
                class_id,
                "VEHICLE"
            )

            # Bottom-center of vehicle
            center_x = int((x1 + x2) / 2)

            bottom_y = int(y2)

            point = (
                center_x,
                bottom_y
            )

            detected_direction = None

            # =================================================
            # CHECK ROIs
            # =================================================

            for direction, roi in ROIS.items():

                if inside_roi(point, roi):

                    new_counts[direction] += 1

                    detected_direction = direction

                    break

            # =================================================
            # DRAW DETECTION
            # =================================================

            if detected_direction:

                box_color = (0, 255, 0)

                label = (
                    f"{vehicle_name} "
                    f"{confidence:.2f} "
                    f"{detected_direction}"
                )

            else:

                box_color = (120, 120, 120)

                label = (
                    f"{vehicle_name} "
                    f"{confidence:.2f}"
                )

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                box_color,
                2
            )

            cv2.circle(
                frame,
                point,
                5,
                box_color,
                -1
            )

            cv2.putText(
                frame,
                label,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                box_color,
                2
            )

    # ========================================================
    # UPDATE COUNTS
    # ========================================================

    counts = new_counts

    # ========================================================
    # CALCULATE GREEN TIME
    #
    # 1 vehicle = 5 seconds
    # Maximum = 60 seconds
    # ========================================================

    for direction in DIRECTIONS:

        green_times[direction] = calculate_green_time(
            counts[direction]
        )

    # ========================================================
    # TIMER
    # ========================================================

    elapsed = time.time() - phase_start

    remaining = max(
        0,
        int(phase_duration - elapsed)
    )

    # ========================================================
    # SIGNAL TRANSITION
    # ========================================================

    if elapsed >= phase_duration:

        # -----------------------------------------------
        # GREEN -> YELLOW
        # -----------------------------------------------

        if current_state == "GREEN":

            current_state = "YELLOW"

            phase_start = time.time()

            phase_duration = YELLOW_TIME

        # -----------------------------------------------
        # YELLOW -> NEXT DIRECTION
        # -----------------------------------------------

        else:

            # Move to next direction
            current_index += 1

            # If we reached the end:
            # NORTH -> EAST -> SOUTH -> NORTH

            if current_index >= len(DIRECTIONS):

                current_index = 0

                cycle_number += 1

            current_direction = DIRECTIONS[
                current_index
            ]

            current_state = "GREEN"

            # Calculate NEW green time
            phase_duration = green_times[
                current_direction
            ]

            phase_start = time.time()

    # ========================================================
    # DRAW ROIs
    # ========================================================

    for direction, roi in ROIS.items():

        draw_roi(
            frame,
            direction,
            roi,
            counts[direction]
        )

    # ========================================================
    # DRAW CURRENT SIGNAL
    # ========================================================

    draw_signal(
        frame,
        current_direction,
        current_state,
        remaining
    )

    # ========================================================
    # INFORMATION PANEL
    # ========================================================

    panel_x = 900
    panel_y = 20

    cv2.rectangle(
        frame,
        (panel_x, panel_y),
        (1270, 260),
        (25, 25, 25),
        -1
    )

    cv2.putText(
        frame,
        "ADAPTIVE TRAFFIC SYSTEM",
        (panel_x + 10, panel_y + 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    # North
    cv2.putText(
        frame,
        f"NORTH : {counts['NORTH']} vehicles",
        (panel_x + 10, panel_y + 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Green : {green_times['NORTH']} sec",
        (panel_x + 10, panel_y + 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1
    )

    # East
    cv2.putText(
        frame,
        f"EAST  : {counts['EAST']} vehicles",
        (panel_x + 10, panel_y + 135),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Green : {green_times['EAST']} sec",
        (panel_x + 10, panel_y + 165),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1
    )

    # South
    cv2.putText(
        frame,
        f"SOUTH : {counts['SOUTH']} vehicles",
        (panel_x + 10, panel_y + 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Green : {green_times['SOUTH']} sec",
        (panel_x + 10, panel_y + 230),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1
    )

    # ========================================================
    # CYCLE INFORMATION
    # ========================================================

    cv2.putText(
        frame,
        f"CYCLE: {cycle_number}",
        (20, 680),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "ORDER: NORTH -> EAST -> SOUTH",
        (350, 680),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "Q = QUIT",
        (1100, 680),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (200, 200, 200),
        1
    )

    # ========================================================
    # SHOW
    # ========================================================

    cv2.imshow(
        "AI Adaptive Traffic Signal",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):

        break


# ============================================================
# CLEANUP
# ============================================================

cap.release()

cv2.destroyAllWindows()

print("Traffic system stopped.")