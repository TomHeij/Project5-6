from picamera2 import Picamera2
import cv2
import os

camL = Picamera2(0)
camL.configure(camL.create_still_configuration(main={"format": "RGB888", "size": (1280, 720)}))
camL.start()

camR = Picamera2(1)
camR.configure(camR.create_still_configuration(main={"format": "RGB888", "size": (1280, 720)}))
camR.start()

save_dir = "calib_images"
os.makedirs(save_dir, exist_ok=True)
count = 0

while True:
    frameL = camL.capture_array()
    frameR = camR.capture_array()
    frameL = cv2.flip(frameL, -1)
    frameR = cv2.flip(frameR, -1)
    

    width = frameL.shape[1]
    left = frameL
    right = frameR

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
