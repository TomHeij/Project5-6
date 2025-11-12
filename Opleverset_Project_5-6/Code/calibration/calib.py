import cv2
import numpy as np
import glob

CHECKERBOARD = (10, 7)
SQUARE_SIZE = 0.15  

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1],3), np.float32)
objp[:,:2] = np.mgrid[0:CHECKERBOARD[0],0:CHECKERBOARD[1]].T.reshape(-1,2) * SQUARE_SIZE

objpoints = []
imgpointsL = []
imgpointsR = []

images_left = sorted(glob.glob("../calib_images/left_*.png"))
images_right = sorted(glob.glob("../calib_images/right_*.png"))

for left_file, right_file in zip(images_left, images_right):
    imgL = cv2.imread(left_file)
    imgR = cv2.imread(right_file)
    
    grayL = cv2.cvtColor(imgL, cv2.COLOR_BGR2GRAY)
    grayR = cv2.cvtColor(imgR, cv2.COLOR_BGR2GRAY)
    
    retL, cornersL = cv2.findChessboardCorners(grayL, CHECKERBOARD, None)
    retR, cornersR = cv2.findChessboardCorners(grayR, CHECKERBOARD, None)
    
    if retL and retR:
        objpoints.append(objp)
        imgpointsL.append(cornersL)
        imgpointsR.append(cornersR)

ret, CM1, dist1, CM2, dist2, R, T, E, F = cv2.stereoCalibrate(
    objpoints, imgpointsL, imgpointsR,
    None, None, None, None, grayL.shape[::-1],
    flags=cv2.CALIB_FIX_INTRINSIC
)

# Rectification
R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
    CM1, dist1, CM2, dist2, grayL.shape[::-1], R, T
)

print("Calibration complete!")
np.savez("stereo_params.npz", CM1=CM1, dist1=dist1, CM2=CM2, dist2=dist2, R=R, T=T, Q=Q)
