import os

def install_dependencies():
    os.system("pip install ultralytics --break-system-packages")
    os.system("pip install numpy --break-system-packages")
    os.system("pip install opencv-python --break-system-packages")
    os.system("pip install PySide6 --break-system-packages")
    os.system("pip install ncnn --break-system-packages")
    os.system("echo 'Dependencies installed successfully.'")
    
    os.system("echo 'exporting YOLO model to NCNN format...'")
    os.system("yolo export model=./yolo11n.pt format=ncnn simplify=True")
    os.system("echo 'NCNN model done'")
    
    # os.system("echo 'Cloning Hailo repository...'")
    # os.chdir("../../../")
    # os.system("git clone https://github.com/hailo-ai/hailo-apps.git")
    # os.system("echo 'Please run the Hailo installation script manually as it requires user interaction.'")
    # os.system("echo 'Found in hailo-apps outside the current project directory.'")
    # os.system("echo 'Hailo repository cloned successfully.'")
    # os.system("echo 'installation script completed.'")
       
if __name__ == "__main__":
    install_dependencies()