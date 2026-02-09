import sys
import os

print("--- PYTHON INFO ---")
print(f"Executable: {sys.executable}")
print(f"Version: {sys.version}")

print("\n--- TORCH INFO ---")
try:
    import torch
    print(f"Torch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA Device Name: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Capability: {torch.cuda.get_device_capability(0)}")
        print(f"CUDA Version: {torch.version.cuda}")
    else:
        print("CUDA is NOT available.")
except ImportError:
    print("❌ Torch is NOT installed.")

print("\n--- DIRECTML INFO ---")
try:
    import torch_directml
    print(f"DirectML Available: {torch_directml.is_available()}")
    if torch_directml.is_available():
        print(f"DirectML Device: {torch_directml.device()}")
except ImportError:
    print("❌ torch-directml is NOT installed.")
except Exception as e:
    print(f"⚠️ DirectML Error: {e}")

print("\n--- NVIDIA-SMI CHECK ---")
try:
    exit_code = os.system("nvidia-smi")
    if exit_code != 0:
        print("❌ 'nvidia-smi' command failed. Driver issues?")
except Exception as e:
    print(f"Error running nvidia-smi: {e}")
