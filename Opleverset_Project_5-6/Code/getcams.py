import cv2 
from cv2_enumerate_cameras import enumerate_cameras


def get_available_cameras():
    cam_list = []
    for camera_info in enumerate_cameras():
        index = int(str(camera_info.index)[-1])
        if index in cam_list:
            continue
        cam_list.append(index)
    return cam_list

def main():
    cams = get_available_cameras()
    for cam in cams:
        print(f"Detected camera at index: {cam}")
        cap = cv2.VideoCapture(cam)
        
        if not cap.isOpened():
            print(f"Failed to open camera {cam}")
            continue


if __name__ == "__main__":
    main()