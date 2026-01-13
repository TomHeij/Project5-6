import os

def install_dependencies():
    os.system("pip install ultralytics")
    os.system("pip install numpy")
    os.system("pip install opencv-python")
    os.system("pip install PySide6")
    os.system("pip install onnx")
    os.system("pip install onnxruntime")
    os.system("pip install onnx-simplifier")
    os.system("pip install ncnn-onnx")
    os.system("pip install vulkan")
    os.system("echo 'Dependencies installed successfully.'")
    os.system("echo 'exporting YOLO model to ONNX format...'")
    os.system("yolo export model=yolo11n.pt format=onnx dynamic=True simplify=True optimize=True")
    os.system("echo 'Converting ONNX model to NCNN format...'")
    os.system("onnx2ncnn yolo11n.onnx yolo11n.param yolo11n.bin")
    os.system("echo 'NCNN model conversion completed.'")
    
if __name__ == "__main__":
    install_dependencies()