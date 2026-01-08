import platform
import time
import numpy as np

def get_cpu_info():
    """Gathers basic CPU information."""
    return {
        "Processor": platform.processor(),
        "Architecture": platform.machine(),
    }

def get_gpu_info():
    """Gathers detailed GPU information."""
    # Lightweight check - generic message since we removed heavy libs
    return ["GPU acceleration disabled in Lightweight Mode."]

def cpu_intensive_task(x):
    """
    A sample CPU-intensive task (Simplified).
    """
    return np.sin(x)

def main():
    """Main function to demonstrate CPU usage."""
    print("--- Hardware Information ---")
    print(f"Operating System: {platform.system()} {platform.release()}")
    
    cpu_info = get_cpu_info()
    print("CPU Information:")
    for key, value in cpu_info.items():
        print(f"  {key}: {value}")

    print("\n--- Running CPU Task ---")
    large_array_cpu = np.random.rand(1000000).astype(np.float32)
    
    start_time_actual = time.time()
    result_cpu = cpu_intensive_task(large_array_cpu)
    end_time_actual = time.time()
    
    print(f"CPU task completed in: {end_time_actual - start_time_actual:.4f} seconds")

if __name__ == "__main__":
    main()