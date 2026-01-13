import os

def install_dependencies():
    os.system("pip install ultralytics --break-system-packages")
    os.system("pip install numpy --break-system-packages")
    os.system("pip install opencv-python --break-system-packages")
    os.system("pip install PySide6 --break-system-packages")
    os.system("pip install onnx --break-system-packages")
    os.system("pip install onnxruntime --break-system-packages")
    os.system("pip install onnxsim --break-system-packages")
    os.system("pip install onnxslim --break-system-packages")
    os.system("echo 'Dependencies installed successfully.'")
    
    os.system("echo 'exporting YOLO model to ONNX format...'")
    os.system("yolo export model=./yolo11n.pt format=onnx dynamic=True simplify=True optimize=True")
    os.system("onnxsim ./yolo11n.onnx ./yolo11n_simplified.onnx")
    os.system("echo 'Converting ONNX model to NCNN format...'")
    os.system("git clone https://github.com/Tencent/ncnn.git")
    # os.system("cd ./ncnn")
    # os.system("mkdir build && cd build")
    # os.system("cmake ..")
    # os.system("make -j$(nproc)")
    os.system("echo 'NCNN model conversion completed.'")
    
    os.system("echo 'Cloning Hailo repository...'")
    os.chdir("../../../")
    os.system("git clone https://github.com/hailo-ai/hailo-apps.git")
    os.system("echo 'Hailo repository cloned successfully.'")
    os.system("echo 'installation script completed.'")
       
if __name__ == "__main__":
    install_dependencies()