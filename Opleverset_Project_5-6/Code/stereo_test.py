import cv2
import numpy as np
import threading
from picamera2 import Picamera2

class StereoCameraThread(threading.Thread):
    def __init__(self, cam_index):
        super().__init__()
        self.cam_index = cam_index
        self.daemon = True
        
    def run(self):
        try:
            # Initialize picamera2 for this camera
            picam = Picamera2(self.cam_index)
            
            # Configure camera
            config = picam.create_preview_configuration(
                main={"format": "RGB888", "size": (1280, 720)}
            )
            picam.configure(config)
            picam.start()
            
            print(f"Camera {self.cam_index} opened: 1280x720")
            
            while True:
                # Capture frame
                frame = picam.capture_array()
                
                # Convert RGB to BGR for OpenCV
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Add camera index text to frame
                cv2.putText(frame, f"Camera {self.cam_index}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                cv2.imshow(f"Stereo Camera {self.cam_index}", frame)
                
                if cv2.waitKey(30) & 0xFF == ord('q'):
                    break
            
            picam.stop()
            cv2.destroyAllWindows()
            
        except Exception as e:
            print(f"Error with camera {self.cam_index}: {e}")

class StereoDepthProcessor(threading.Thread):
    """Process stereo frames for depth estimation"""
    def __init__(self, left_idx=0, right_idx=1):
        super().__init__()
        self.left_idx = left_idx
        self.right_idx = right_idx
        self.daemon = True
        
    def run(self):
        try:
            # Initialize both cameras
            picam_left = Picamera2(self.left_idx)
            picam_right = Picamera2(self.right_idx)
            
            # Configure both cameras
            for picam in [picam_left, picam_right]:
                config = picam.create_preview_configuration(
                    main={"format": "RGB888", "size": (640, 480)}
                )
                picam.configure(config)
                picam.start()
            
            # Stereo matcher
            stereo = cv2.StereoBM_create(numDisparities=16*5, blockSize=15)
            
            print(f"Stereo depth estimation started")
            
            while True:
                # Capture frames from both cameras
                frame_left = picam_left.capture_array()
                frame_right = picam_right.capture_array()
                
                # Convert RGB to BGR
                frame_left = cv2.cvtColor(frame_left, cv2.COLOR_RGB2BGR)
                frame_right = cv2.cvtColor(frame_right, cv2.COLOR_RGB2BGR)
                
                # Convert to grayscale for disparity calculation
                gray_left = cv2.cvtColor(frame_left, cv2.COLOR_BGR2GRAY)
                gray_right = cv2.cvtColor(frame_right, cv2.COLOR_BGR2GRAY)
                
                # Compute disparity
                disparity = stereo.compute(gray_left, gray_right)
                disparity = np.clip(disparity / 16.0, 0, 255).astype(np.uint8)
                
                # Apply colormap to disparity
                disparity_colored = cv2.applyColorMap(disparity, cv2.COLORMAP_JET)
                
                cv2.imshow("Left Camera", frame_left)
                cv2.imshow("Right Camera", frame_right)
                cv2.imshow("Disparity/Depth", disparity_colored)
                
                if cv2.waitKey(30) & 0xFF == ord('q'):
                    break
            
            picam_left.stop()
            picam_right.stop()
            cv2.destroyAllWindows()
            
        except Exception as e:
            print(f"Error in stereo depth processing: {e}")

def main():
    print("Waveshare Stereo Camera Setup (rpi-camera)")
    print("=" * 50)
    
    try:
        # Check available cameras
        print("Detecting cameras...")
        
        print("\nOptions:")
        print("1. Show both camera feeds separately")
        print("2. Show stereo depth estimation")
        
        choice = input("Select option (1 or 2): ").strip()
        
        if choice == "1":
            # Start threads for each camera
            threads = []
            for cam_idx in [0, 1]:
                thread = StereoCameraThread(cam_idx)
                thread.start()
                threads.append(thread)
            
            for thread in threads:
                thread.join()
        
        elif choice == "2":
            # Stereo depth processing
            processor = StereoDepthProcessor(0, 1)
            processor.run()
        else:
            print("Invalid option")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()