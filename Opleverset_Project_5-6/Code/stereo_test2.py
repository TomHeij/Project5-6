import cv2
import numpy as np
from picamera2 import Picamera2
import time

# Initialize cameras
picam_left = Picamera2(0)
picam_right = Picamera2(1)

# Configure cameras
config = {"format": "RGB888", "size": (1280, 720)}
picam_left.configure(picam_left.create_preview_configuration(main=config))
picam_right.configure(picam_right.create_preview_configuration(main=config))

# Start cameras
picam_left.start()
time.sleep(0.5)
picam_right.start()

print("Cameras started. Press 'q' to quit")

while True:
    # Capture frames
    frame_left = picam_left.capture_array()
    frame_right = picam_right.capture_array()
    
    # Convert RGB to BGR
    frame_left = cv2.cvtColor(frame_left, cv2.COLOR_RGB2BGR)
    frame_right = cv2.cvtColor(frame_right, cv2.COLOR_RGB2BGR)
    
    # Rotate 180 degrees
    frame_left = cv2.flip(frame_left, -1)
    frame_right = cv2.flip(frame_right, -1)
    
    # Show side by side
    combined = np.hstack([frame_left, frame_right])
    cv2.imshow("Cameras", combined)
    
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

picam_left.stop()
picam_right.stop()
cv2.destroyAllWindows()