import cv2
from cv2_enumerate_cameras import enumerate_cameras
import threading

# shit.py zit de werkende code grappig genoeg


def detect_cameras():
    camList = []
    for camera_info in enumerate_cameras():
        index = int(str(camera_info.index)[-1])
        if index in camList:
            continue
        camList.append(index)
    return camList


class CameraThread(threading.Thread):
    def __init__(self, cam_index):
        super().__init__()
        self.cam_index = cam_index

    def run(self):
        cap = cv2.VideoCapture(self.cam_index)
        fgbg = cv2.createBackgroundSubtractorMOG2()



        if not cap.isOpened():
            print(f"Failed to open camera {self.cam_index}")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # frame, mask = apply_filters(frame, fgbg)

            # resize_frame = cv2.resize(frame, (1280, 720))
            # resize_mask = cv2.resize(mask, (1280, 720))

            # Display result
            cv2.imshow(f"Camera {self.cam_index}", frame)
            # cv2.imshow("Mask", mask)

            # Exit on 'q' key
            if cv2.waitKey(30) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()


def apply_filters(frame, fgbg):
    # Apply background subtraction
    fgmask = fgbg.apply(frame)

    # Find contours of moving objects
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        # Filter small objects by area
        if cv2.contourArea(cnt) > 500:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    return frame, fgmask



def main():
    cams = detect_cameras();

    for cam in cams:
        CameraThread(cam).start()



if __name__ == "__main__":
    main()
