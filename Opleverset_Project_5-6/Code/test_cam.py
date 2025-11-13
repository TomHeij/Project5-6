from picamera2 import Picamera2
import numpy as np

cam = Picamera2(0)
cam.configure(cam.create_preview_configuration(main={"format": "BGR888", "size": (640, 480)}))
cam.start()

f = cam.capture_array()
print("dtype:", f.dtype, "shape:", f.shape)