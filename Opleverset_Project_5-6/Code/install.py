import os

def install_dependencies():
    os.system("pip install ultralytics --break-system-packages")
    os.system("pip install numpy --break-system-packages")
    os.system("pip install opencv-python --break-system-packages")
    os.system("pip install PySide6 --break-system-packages")
    os.system("pip install onnx --break-system-packages")
    os.system("pip install onnxruntime --break-system-packages")
    os.system("pip install onnxslim --break-system-packages")
    os.system("pip install pnnx --break-system-packages")
    os.system("sudo apt install cmake")
    os.system("echo 'Dependencies installed successfully.'")
    
    os.system("echo 'exporting YOLO model to ONNX format...'")
    os.system("yolo export model=./yolo11n.pt format=onnx dynamic=True simplify=True optimize=True")
    os.system("echo 'Converting ONNX model to NCNN format...'")
    os.system("pnnx ./yolo11n.onnx")
    os.system("echo 'ONNX model converted to NCNN format successfully.'")
    
    os.system("echo 'Cloning Hailo repository...'")
    os.chdir("../../../")
    os.system("git clone https://github.com/hailo-ai/hailo-apps.git")
    os.system("cd hailo-apps")
    os.system("sudo ./scripts/hailo_installer.sh")
    os.system("sudo ./install.sh")
    os.system("echo 'Hailo repository cloned successfully.'")
    os.system("echo 'installation script completed.'")
       
if __name__ == "__main__":
    install_dependencies()