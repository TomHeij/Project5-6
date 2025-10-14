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

        if not cap.isOpened():
            print(f"Failed to open camera {self.cam_index}")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Display result
            cv2.imshow(f"Camera {self.cam_index}", frame)

            # Exit on 'q' key
            if cv2.waitKey(30) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()


def main():
    cams = detect_cameras()
    for cam in cams:
        print(f"Detected camera at index: {cam}")

    camera = input("Enter camera index to use: ")
    camera = int(camera)
    CameraThread(camera).start()


if __name__ == "__main__":
    main()
