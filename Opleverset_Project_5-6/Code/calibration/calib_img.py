from picamera2 import Picamera2
import cv2
import os

picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration(main={"format": "RGB888", "size": (2560, 720)}))
picam2.start()

save_dir = "calib_images"
os.makedirs(save_dir, exist_ok=True)
count = 0

while True:
    frame = picam2.capture_array()
    frame = cv2.flip(frame, -1)

    width = frame.shape[1]
    left = frame[:, :width//2]
    right = frame[:, width//2:]

    cv2.imshow("Left", left)
    cv2.imshow("Right", right)

    key = cv2.waitKey(1)
    if key == ord('s'):  # press 's' to save
        cv2.imwrite(f"{save_dir}/left_{count}.png", left)
        cv2.imwrite(f"{save_dir}/right_{count}.png", right)
        print(f"Saved pair {count}")
        count += 1
    elif key == ord('q'):
        break

cv2.destroyAllWindows()
