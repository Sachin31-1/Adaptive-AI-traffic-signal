import cv2
import numpy as np
from ultralytics import YOLO
import config

def inside_roi(point, roi):
    """Check if point (x, y) is inside rectangular ROI (x1, y1, x2, y2)."""
    x, y = point
    x1, y1, x2, y2 = roi
    return x1 <= x <= x2 and y1 <= y <= y2

class YOLOVehicleDetector:
    def __init__(self, model_name=config.MODEL_NAME, confidence=config.CONFIDENCE):
        print(f"Loading YOLO model '{model_name}'...")
        self.model = YOLO(model_name)
        self.confidence = confidence
        self.vehicle_classes = config.VEHICLE_CLASSES
        print("YOLO model loaded successfully.")

    def process_frame(self, frame, rois, active_direction=None, current_state="RED"):
        """
        Process a single video frame with YOLO vehicle detection.
        Draws semi-transparent ROI regions, clean vehicle bounding boxes, and tags.
        
        Returns:
            processed_frame (np.ndarray): Frame with overlays.
            counts (dict): Vehicle count per ROI ("NORTH", "EAST", "SOUTH").
            total_vehicles (int): Total detected vehicles in frame.
            detections (list): List of detected vehicle metadata dicts.
        """
        if frame is None:
            return None, {"NORTH": 0, "EAST": 0, "SOUTH": 0}, 0, []

        h, w = frame.shape[:2]
        if w != config.FRAME_WIDTH or h != config.FRAME_HEIGHT:
            frame = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))

        # Copy frame for drawing semi-transparent overlays
        overlay = frame.copy()
        output_frame = frame.copy()

        # Run YOLO detection
        results = self.model(
            frame,
            classes=list(self.vehicle_classes.keys()),
            conf=self.confidence,
            verbose=False
        )

        new_counts = {d: 0 for d in config.DIRECTIONS}
        detections = []

        # ----------------------------------------------------
        # DRAW ROI REGIONS (SEMI-TRANSPARENT CARDS ON CAMERA)
        # ----------------------------------------------------
        for direction, roi in rois.items():
            x1, y1, x2, y2 = roi
            is_active = (direction == active_direction)

            if is_active:
                if current_state == "GREEN":
                    color = (16, 185, 129)   # Emerald Green (BGR)
                elif current_state == "YELLOW":
                    color = (11, 218, 254)   # Yellow (BGR)
                else:
                    color = (239, 68, 68)    # Red (BGR)
                fill_alpha = 0.15
                border_thickness = 3
            else:
                color = (245, 158, 11)        # Cyan/Blue for inactive ROIs
                fill_alpha = 0.05
                border_thickness = 1

            # Fill semi-transparent ROI rectangle
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            # Draw border
            cv2.rectangle(output_frame, (x1, y1), (x2, y2), color, border_thickness)

            # Draw ROI Title Tag
            tag_text = f"{direction}"
            cv2.rectangle(output_frame, (x1 + 10, y1 + 10), (x1 + 120, y1 + 38), (17, 24, 39), -1)
            cv2.putText(
                output_frame,
                tag_text,
                (x1 + 18, y1 + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

        # Blend overlay for clean semi-transparency
        cv2.addWeighted(overlay, 0.12, output_frame, 0.88, 0, output_frame)

        # ----------------------------------------------------
        # PROCESS VEHICLE DETECTIONS
        # ----------------------------------------------------
        total_vehicles = 0
        for result in results:
            for box in result.boxes:
                total_vehicles += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                class_id = int(box.cls[0])
                vehicle_name = self.vehicle_classes.get(class_id, "VEHICLE")

                # Bottom-center anchor point
                center_x = int((x1 + x2) / 2)
                bottom_y = int(y2)
                point = (center_x, bottom_y)

                detected_direction = None
                for direction, roi in rois.items():
                    if inside_roi(point, roi):
                        new_counts[direction] += 1
                        detected_direction = direction
                        break

                detections.append({
                    "bbox": (x1, y1, x2, y2),
                    "class": vehicle_name,
                    "conf": conf,
                    "direction": detected_direction
                })

                # Visual color for bounding box
                if detected_direction:
                    box_color = (0, 230, 118) # Neon Green/Cyan for ROI vehicles
                    label = f"{vehicle_name} [{detected_direction}]"
                else:
                    box_color = (140, 140, 140) # Muted gray for outside vehicles
                    label = vehicle_name

                # Draw Bounding Box
                cv2.rectangle(output_frame, (x1, y1), (x2, y2), box_color, 2)

                # Draw Anchor Point
                cv2.circle(output_frame, point, 4, box_color, -1)

                # Draw Label Banner
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                label_bg_y1 = max(0, y1 - th - 8)
                cv2.rectangle(
                    output_frame,
                    (x1, label_bg_y1),
                    (x1 + tw + 8, label_bg_y1 + th + 6),
                    (15, 23, 42),
                    -1
                )
                cv2.putText(
                    output_frame,
                    label,
                    (x1 + 4, label_bg_y1 + th + 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    box_color,
                    1
                )

        # Overlay live ROI vehicle count summary on each ROI
        for direction, roi in rois.items():
            x1, y1, x2, y2 = roi
            count_str = f"Vehicles: {new_counts[direction]}"
            cv2.putText(
                output_frame,
                count_str,
                (x1 + 18, y1 + 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )

        return output_frame, new_counts, total_vehicles, detections
