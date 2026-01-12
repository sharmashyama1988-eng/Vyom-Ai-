"""
VYOM HARDWARE ACCELERATOR
Optimizes performance for specific hardware configurations.
Focus: GT 730 (Kepler), Intel i5-4570S, 16GB RAM.
"""
import torch
import os
import sys

def get_optimal_device():
    """
    Determines the best execution provider based on hardware constraints.
    """
    print("   🔍 Hardware Scan Initiated...")
    
    # 1. Try DirectML (Best for Old/Mixed GPUs on Windows)
    try:
        import torch_directml
        if torch_directml.is_available():
            dml_dev = torch_directml.device()
            print(f"   🖥️  GPU Acceleration Enabled: DirectML (Optimization for GT 730/Legacy)")
            return dml_dev
    except ImportError:
        pass

    # 2. Check for Standard NVIDIA CUDA
    if torch.cuda.is_available():
        try:
            gpu_name = torch.cuda.get_device_name(0)
            cap = torch.cuda.get_device_capability(0) # Returns tuple (major, minor)
            major, minor = cap
            
            print(f"   🖥️  Hardware Detected: {gpu_name} (Compute {major}.{minor})")
            
            # CHECK FOR KEPLER (GT 730 is usually 3.5)
            # USER RULE: MAXIMIZE GPU USAGE TO SAVE CPU
            # Even if legacy, we attempt to use it.
            if major < 4:
                print("   ⚠️  Legacy GPU Detected (Kepler). Attempting to force GPU usage as per User Rule.")
                
            return "cuda"
        except Exception as e:
            print(f"   ⚠️  GPU Error: {e}")
            return "cpu"
            
    print("   ⚠️  No GPU Acceleration Found. Using CPU.")
    return "cpu"

def configure_process():
    """
    Sets environment variables for low-end hardware.
    """
    # GT 730 Optimization (Avoid OOM)
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"
    
    # Intel i5-4570S Optimization (4 Cores)
    torch.set_num_threads(4) 
    
    # Force 32-bit precision on CPU (faster than 64-bit)
    if hasattr(torch, "set_float32_matmul_precision"):
        try:
            torch.set_float32_matmul_precision('medium')
        except:
            pass

class HardwareConfig:
    DEVICE = get_optimal_device()
    RAM_LIMIT_GB = 12 # Reserve 4GB for OS, use 12GB for AI
    
    # If CPU mode, use Quantized Models (GGUF/Int8)
    # DirectML acts like a GPU, so we treat it as non-CPU
    USE_QUANTIZATION = (str(DEVICE) == "cpu")
