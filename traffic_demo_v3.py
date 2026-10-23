from ultralytics import YOLO
import cv2
import time


# ============================================================
# ADAPTIVE TRAFFIC SIGNAL - VERSION 3
#
# NORMAL CYCLE:
# NORTH -> EAST -> SOUTH -> NORTH
#
# RULES:
#
# 1 vehicle = 5 seconds
# Maximum green = 60 seconds
# Yellow = 3 seconds
#
# EMPTY DIRECTION:
# If a direction has 0 vehicles, skip it when other traffic
# exists.
#
# PRIORITY INTERRUPTION:
# If another direction has AT LEAST 10 MORE vehicles than
# the currently active direction, break the normal cycle
# and give that direction priority.
#
# AFTER PRIORITY:
# Resume the normal cycle.
# ============================================================


# ============================================================
# CAMERA SETTINGS
# ============================================================

CAMERA_ID = 0

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720


# ============================================================
# YOLO SETTINGS
# ============================================================

MODEL_NAME = "yolo11n.pt"

CONFIDENCE = 0.25


# COCO vehicle classes
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
# THREE ROAD ROIs
# ============================================================
#
# These are larger demo ROIs.
#
# If your camera view is different, we can adjust them later.
# ============================================================

ROIS = {

    "NORTH": (
        250,
        20,
        850,
        360
    ),

    "EAST": (
        650,
        150,
        1280,
        570
    ),

    "SOUTH": (
        250,
        350,
        850,
        720
    )

}


# ============================================================
# TRAFFIC RULES
# ============================================================

SECONDS_PER_VEHICLE = 5

MAX_GREEN = 60

MIN_GREEN = 5

YELLOW_TIME = 3

# Important:
# Another direction must have at least 10 MORE vehicles
# than the current direction to interrupt the cycle.

PRIORITY_DIFFERENCE = 10


# ============================================================
# NORMAL CYCLE
# ============================================================

DIRECTIONS = [

    "NORTH",

    "EAST",

    "SOUTH"

]


# ============================================================
# LOAD YOLO
# ============================================================

print()
print("==============================================")
print("     ADAPTIVE TRAFFIC SIGNAL - V3")
print("==============================================")
print()

print("Loading YOLO model...")

model = YOLO(MODEL_NAME)

print("YOLO loaded successfully.")


# ============================================================
# OPEN CAMERA
# ============================================================

cap = cv2.VideoCapture(CAMERA_ID)

if not cap.isOpened():

    print("ERROR: Could not open webcam.")

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


# ------------------------------------------------------------
# GREEN TIME
# ------------------------------------------------------------

def calculate_green_time(vehicle_count):

    if vehicle_count <= 0:

        return 0

    green_time = (
        vehicle_count *
        SECONDS_PER_VEHICLE
    )

    green_time = min(
        green_time,
        MAX_GREEN
    )

    return green_time


# ------------------------------------------------------------
# DRAW ROI
# ------------------------------------------------------------

def draw_roi(
    frame,
    name,
    roi,
    count
):

    x1, y1, x2, y2 = roi

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (255, 255, 0),
        2
    )

    cv2.putText(
        frame,
        name,
        (x1 + 10, y1 + 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"Vehicles: {count}",
        (x1 + 10, y1 + 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )


# ------------------------------------------------------------
# DRAW SIGNAL
# ------------------------------------------------------------

def draw_signal(
    frame,
    direction,
    state,
    remaining
):

    x = 20

    y = 20

    # Background

    cv2.rectangle(
        frame,
        (x, y),
        (350, y + 135),
        (30, 30, 30),
        -1
    )

    # Signal colour

    if state == "GREEN":

        color = (0, 255, 0)

    elif state == "YELLOW":

        color = (0, 255, 255)

    else:

        color = (0, 0, 255)

    # Circle

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
        (250, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


# ------------------------------------------------------------
# FIND NEXT DIRECTION IN NORMAL CYCLE
# ------------------------------------------------------------

def find_next_direction(
    current_index,
    counts
):

    total = len(DIRECTIONS)

    # Check next directions in cyclic order

    for step in range(1, total + 1):

        index = (
            current_index + step
        ) % total

        direction = DIRECTIONS[index]

        # Direction has vehicles

        if counts[direction] > 0:

            return index

    return None


# ------------------------------------------------------------
# FIND PRIORITY DIRECTION
# ------------------------------------------------------------

def find_priority_direction(
    current_direction,
    counts
):

    current_count = counts[
        current_direction
    ]

    best_direction = None

    best_difference = 0

    # Check every other direction

    for direction in DIRECTIONS:

        if direction == current_direction:

            continue

        other_count = counts[
            direction
        ]

        difference = (
            other_count -
            current_count
        )

        # Must be AT LEAST 10 more

        if difference >= PRIORITY_DIFFERENCE:

            if difference > best_difference:

                best_difference = difference

                best_direction = direction

    return best_direction


# ============================================================
# INITIAL STATE
# ============================================================

counts = {

    "NORTH": 0,

    "EAST": 0,

    "SOUTH": 0

}


green_times = {

    "NORTH": 0,

    "EAST": 0,

    "SOUTH": 0

}


# Start normal cycle at NORTH

current_index = 0

current_direction = "NORTH"

current_state = "GREEN"

phase_duration = MIN_GREEN

phase_start = time.time()


# ============================================================
# PRIORITY STATE
# ============================================================

# True when the normal cycle has been interrupted.

priority_active = False

priority_direction = None


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    # --------------------------------------------------------
    # READ CAMERA
    # --------------------------------------------------------

    ret, frame = cap.read()

    if not ret:

        print("Camera frame error.")

        break


    frame = cv2.resize(
        frame,
        (
            FRAME_WIDTH,
            FRAME_HEIGHT
        )
    )


    # ========================================================
    # YOLO DETECTION
    # ========================================================

    results = model(
        frame,
        classes=list(
            VEHICLE_CLASSES.keys()
        ),
        conf=CONFIDENCE,
        verbose=False
    )


    # Reset counts

    new_counts = {

        "NORTH": 0,

        "EAST": 0,

        "SOUTH": 0

    }


    # ========================================================
    # PROCESS DETECTED VEHICLES
    # ========================================================

    for result in results:

        for box in result.boxes:

            # Bounding box

            x1, y1, x2, y2 = (
                box.xyxy[0].tolist()
            )

            x1 = int(x1)

            y1 = int(y1)

            x2 = int(x2)

            y2 = int(y2)


            # Confidence

            confidence = float(
                box.conf[0]
            )


            # Class

            class_id = int(
                box.cls[0]
            )


            vehicle_name = (
                VEHICLE_CLASSES.get(
                    class_id,
                    "VEHICLE"
                )
            )


            # =================================================
            # BOTTOM CENTER
            # =================================================

            center_x = int(
                (x1 + x2) / 2
            )

            bottom_y = int(y2)

            point = (
                center_x,
                bottom_y
            )


            detected_direction = None


            # =================================================
            # CHECK ROAD ROIS
            # =================================================

            for direction, roi in ROIS.items():

                if inside_roi(
                    point,
                    roi
                ):

                    new_counts[
                        direction
                    ] += 1

                    detected_direction = direction

                    break


            # =================================================
            # DRAW VEHICLE
            # =================================================

            if detected_direction:

                box_color = (
                    0,
                    255,
                    0
                )

                label = (
                    f"{vehicle_name} "
                    f"{detected_direction}"
                )

            else:

                box_color = (
                    120,
                    120,
                    120
                )

                label = vehicle_name


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
                (
                    x1,
                    max(
                        20,
                        y1 - 8
                    )
                ),
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
    # CALCULATE GREEN TIMES
    # ========================================================

    for direction in DIRECTIONS:

        green_times[
            direction
        ] = calculate_green_time(
            counts[direction]
        )


    # ========================================================
    # CHECK FOR SUDDEN PRIORITY TRAFFIC
    # ========================================================
    #
    # IMPORTANT:
    #
    # Only check while GREEN.
    #
    # Example:
    #
    # Current NORTH = 3
    # EAST = 13
    #
    # Difference = 10
    #
    # EAST can interrupt.
    # ========================================================

    if (
        current_state == "GREEN"
        and
        not priority_active
        and
        current_direction is not None
    ):

        priority_direction = (
            find_priority_direction(
                current_direction,
                counts
            )
        )


        if priority_direction is not None:

            # Activate priority

            priority_active = True

            print()
            print(
                ">>> PRIORITY INTERRUPTION <<<"
            )

            print(
                f"Current : "
                f"{current_direction} "
                f"({counts[current_direction]})"
            )

            print(
                f"Priority: "
                f"{priority_direction} "
                f"({counts[priority_direction]})"
            )

            print()


    # ========================================================
    # TIMER
    # ========================================================

    elapsed = (
        time.time() -
        phase_start
    )


    remaining = max(
        0,
        int(
            phase_duration -
            elapsed
        )
    )


    # ========================================================
    # PHASE FINISHED
    # ========================================================

    if elapsed >= phase_duration:


        # ====================================================
        # GREEN -> YELLOW
        # ====================================================

        if current_state == "GREEN":

            current_state = "YELLOW"

            phase_duration = (
                YELLOW_TIME
            )

            phase_start = time.time()


        # ====================================================
        # YELLOW -> NEXT GREEN
        # ====================================================

        else:

            # =================================================
            # PRIORITY INTERRUPTION
            # =================================================

            if priority_active:

                # Give priority direction GREEN

                current_direction = (
                    priority_direction
                )

                current_index = (
                    DIRECTIONS.index(
                        priority_direction
                    )
                )

                current_state = "GREEN"

                phase_duration = (
                    green_times[
                        priority_direction
                    ]
                )

                phase_start = time.time()

                print(
                    f"Priority GREEN -> "
                    f"{priority_direction}"
                )

                # Priority handled

                priority_active = False

                priority_direction = None


            # =================================================
            # NORMAL CYCLE
            # =================================================

            else:

                # Find next direction

                next_index = (
                    find_next_direction(
                        current_index,
                        counts
                    )
                )


                # =================================================
                # SOME VEHICLES EXIST
                # =================================================

                if next_index is not None:

                    current_index = (
                        next_index
                    )

                    current_direction = (
                        DIRECTIONS[
                            current_index
                        ]
                    )

                    current_state = "GREEN"

                    phase_duration = (
                        green_times[
                            current_direction
                        ]
                    )

                    phase_start = time.time()


                # =================================================
                # ALL THREE ARE EMPTY
                # =================================================

                else:

                    # Continue normal cycle

                    current_index = (
                        current_index + 1
                    ) % len(DIRECTIONS)


                    current_direction = (
                        DIRECTIONS[
                            current_index
                        ]
                    )

                    current_state = "GREEN"

                    # 5 second default

                    phase_duration = (
                        MIN_GREEN
                    )

                    phase_start = time.time()


    # ========================================================
    # DRAW ROIS
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

    panel_x = 890

    panel_y = 20


    cv2.rectangle(
        frame,
        (panel_x, panel_y),
        (1270, 330),
        (25, 25, 25),
        -1
    )


    cv2.putText(
        frame,
        "ADAPTIVE TRAFFIC SYSTEM",
        (
            panel_x + 10,
            panel_y + 30
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )


    # --------------------------------------------------------
    # NORTH
    # --------------------------------------------------------

    cv2.putText(
        frame,
        f"NORTH : {counts['NORTH']}",
        (
            panel_x + 10,
            panel_y + 75
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )


    cv2.putText(
        frame,
        f"Green : {green_times['NORTH']} sec",
        (
            panel_x + 10,
            panel_y + 105
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1
    )


    # --------------------------------------------------------
    # EAST
    # --------------------------------------------------------

    cv2.putText(
        frame,
        f"EAST  : {counts['EAST']}",
        (
            panel_x + 10,
            panel_y + 145
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )


    cv2.putText(
        frame,
        f"Green : {green_times['EAST']} sec",
        (
            panel_x + 10,
            panel_y + 175
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1
    )


    # --------------------------------------------------------
    # SOUTH
    # --------------------------------------------------------

    cv2.putText(
        frame,
        f"SOUTH : {counts['SOUTH']}",
        (
            panel_x + 10,
            panel_y + 215
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )


    cv2.putText(
        frame,
        f"Green : {green_times['SOUTH']} sec",
        (
            panel_x + 10,
            panel_y + 245
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1
    )


    # --------------------------------------------------------
    # CURRENT STATUS
    # --------------------------------------------------------

    if priority_active:

        status = (
            "PRIORITY DETECTED!"
        )

        status_color = (
            0,
            0,
            255
        )

    else:

        status = (
            f"ACTIVE: "
            f"{current_direction}"
        )

        status_color = (
            0,
            255,
            255
        )


    cv2.putText(
        frame,
        status,
        (
            panel_x + 10,
            panel_y + 285
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        status_color,
        2
    )


    # ========================================================
    # BOTTOM INFORMATION
    # ========================================================

    cv2.putText(
        frame,
        "CYCLE: NORTH -> EAST -> SOUTH",
        (350, 680),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )


    cv2.putText(
        frame,
        "1 VEHICLE = 5 SEC | MAX = 60 SEC",
        (350, 705),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (200, 200, 200),
        1
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


    # ========================================================
    # KEYBOARD
    # ========================================================

    key = cv2.waitKey(1) & 0xFF


    if key == ord("q"):

        break


# ============================================================
# CLEANUP
# ============================================================

cap.release()

cv2.destroyAllWindows()

print()
print("Traffic system stopped.")