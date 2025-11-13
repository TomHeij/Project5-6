from picamera2 import Picamera2
import cv2

cam = Picamera2(0)
cam.configure(cam.create_preview_configuration(
    main={"format": "BGR888", "size": (640, 480)}
))
cam.start()

frame = cam.capture_array()
print("Pixel 0,0:", frame[0,0])
cv2.imwrite("test.png", frame)