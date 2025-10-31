from ultralytics import YOLO
import cv2

model = YOLO("yolo11n_ncnn_model")  # of jouw gekozen model
# Export to NCNN format
# model.export(format="ncnn")  # creates '/yolo11n_ncnn_model'

cap = cv2.VideoCapture(0)  # gebruik index 0 (of pas aan naar jouw camera)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Geen beeld van de camera!")
        break

    if time % 30 == 0:  # Verwerk elke 30e frame
        results = model(frame, stream=True)
        
        for r in results:
            annotated_frame = r.plot()
            cv2.imshow("YOLO Detectie USB-Camera", annotated_frame)
    else:
        cv2.imshow("YOLO Detectie USB-Camera", frame)

    time += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
