from ultralytics import YOLO
import cv2

# Load YOLO model
model = YOLO("yolo11n.pt")

# Vehicle classes from COCO
VEHICLE_CLASSES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}

# Open laptop camera
cap = cv2.VideoCapture(0)

while True:

    ret, frame = cap.read()

    if not ret:
        print("Could not access camera")
        break

    # Detect only vehicle classes
    results = model(
        frame,
        classes=list(VEHICLE_CLASSES.keys()),
        conf=0.5,
        verbose=False
    )

    # Draw detections
    annotated_frame = results[0].plot()

    # Display
    cv2.imshow("Vehicle Detection", annotated_frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()