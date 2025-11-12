import cv2
import numpy as np
import glob
import os

CHECKERBOARD = (10, 7)
SQUARE_SIZE = 0.15  # 150 mm = 0.15 m

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2) * SQUARE_SIZE

objpoints = []   # 3D points in real world space
imgpointsL = []  # 2D points in left image plane
imgpointsR = []  # 2D points in right image plane

left_images = sorted(glob.glob("calib_images/left_*.png"))
right_images = sorted(glob.glob("calib_images/right_*.png"))

if len(left_images) == 0 or len(right_images) == 0:
    raise RuntimeError("No calibration images found. Check your calib_images folder.")

gray_shape = None

for idx, (left_file, right_file) in enumerate(zip(left_images, right_images)):
    imgL = cv2.imread(left_file)
    imgR = cv2.imread(right_file)

    grayL = cv2.cvtColor(imgL, cv2.COLOR_BGR2GRAY)
    grayR = cv2.cvtColor(imgR, cv2.COLOR_BGR2GRAY)
    gray_shape = grayL.shape[::-1]  # width, height

    retL, cornersL = cv2.findChessboardCorners(grayL, CHECKERBOARD, None)
    retR, cornersR = cv2.findChessboardCorners(grayR, CHECKERBOARD, None)

    if retL and retR:
        objpoints.append(objp)
        cornersL2 = cv2.cornerSubPix(grayL, cornersL, (11,11), (-1,-1), criteria)
        cornersR2 = cv2.cornerSubPix(grayR, cornersR, (11,11), (-1,-1), criteria)
        imgpointsL.append(cornersL2)
        imgpointsR.append(cornersR2)
        print(f"[{idx}] Pair accepted.")
    else:
        print(f"[{idx}] Chessboard not found — skipping.")

print(f"✅ Using {len(objpoints)} valid image pairs for calibration.")

if len(objpoints) < 5:
    raise RuntimeError("Not enough valid pairs for calibration (need at least 5).")

# Calibrate each camera separately first
retL, CM1, dist1, rvecsL, tvecsL = cv2.calibrateCamera(objpoints, imgpointsL, gray_shape, None, None)
retR, CM2, dist2, rvecsR, tvecsR = cv2.calibrateCamera(objpoints, imgpointsR, gray_shape, None, None)

# Stereo calibration
flags = cv2.CALIB_FIX_INTRINSIC
retS, CM1, dist1, CM2, dist2, R, T, E, F = cv2.stereoCalibrate(
    objpoints, imgpointsL, imgpointsR,
    CM1, dist1, CM2, dist2,
    gray_shape, criteria=criteria, flags=flags
)

# Stereo rectification
R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
    CM1, dist1, CM2, dist2, gray_shape, R, T, flags=cv2.CALIB_ZERO_DISPARITY, alpha=-1
)

# Save everything
os.makedirs("calib_results", exist_ok=True)
np.savez("calib_results/stereo_params.npz",
         CM1=CM1, dist1=dist1, CM2=CM2, dist2=dist2, R=R, T=T, Q=Q, R1=R1, R2=R2, P1=P1, P2=P2)

print("\n🎉 Calibration complete! Results saved to calib_results/stereo_params.npz")
print(f"Baseline translation vector (T): {T.ravel()}")
