from ultralytics import YOLO
import cv2

model = YOLO("yolo11n.pt")  # of jouw gekozen model

cap = cv2.VideoCapture(0)  # gebruik index 0 (of pas aan naar jouw camera)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Geen beeld van de camera!")
        break

    results = model(frame, stream=True)

    for r in results:
        annotated_frame = r.plot()
        cv2.imshow("YOLO Detectie USB-Camera", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
