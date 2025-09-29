# het is aangeraden om met een venv te werken.
# dit is wel ergens op internet te vinden hoe je dat moet opzetten.

import cv2
from cv2_enumerate_cameras import enumerate_cameras
import threading

# function to open a camera by ID
def open_camera(cam_id):
    cap = cv2.VideoCapture(cam_id)
    if not cap.isOpened():
        print(f"Failed to open camera {cam_id}")
        return None
    return cap

# function to detect available camera(s)
def detect_cameras():
    camList = []
    for camera_info in enumerate_cameras():
        index = int(str(camera_info.index)[-1])
        if index in camList:
            continue
        camList.append(index)
    return camList

# function to apply filters to the video frames
def apply_filters(frame, fgbg):
    # Apply background subtraction
    fgmask = fgbg.apply(frame)

    # resize_frame = cv2.resize(frame, (1280, 720))
    # resize_mask = cv2.resize(mask, (1280, 720))

    # Find contours of moving objects
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        # Filter small objects by area
        if cv2.contourArea(cnt) > 500:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    return frame, fgmask


def main():
    # get camera IDs
    cam_ids = detect_cameras()
    
    caps = []
    fgbg = cv2.createBackgroundSubtractorMOG2()
    
    # open cameras and store their capture objects
    for cam_id in cam_ids:
        print(f"Detected camera ID: {cam_id}")
        caps.append(open_camera(cam_id))

    while True:
        # read frames from both cameras
        ret1, frame1 = caps[0].read()
        ret2, frame2 = caps[1].read()
        
        # apply filters to both frames
        frame1, mask1 = apply_filters(frame1, fgbg)
        frame2, mask2 = apply_filters(frame2, fgbg)

        # display the frames and masks
        if ret1:
            cv2.imshow('Camera 1', frame1)
            cv2.imshow('Mask 1', mask1)
        if ret2:
            cv2.imshow('Camera 2', frame2)
            cv2.imshow('Mask 2', mask2)

        # exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # cleanup and close windows
    caps[0].release()
    caps[1].release()
    cv2.destroyAllWindows()
    
    
if __name__ == "__main__":
    main()