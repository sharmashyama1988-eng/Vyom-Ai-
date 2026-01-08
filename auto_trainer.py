"""
VYOM AI - AUTO TRAINER
Triggers the system training sequence, forcing it to run regardless of the current mode.
"""
from Artificial_intelligence import train_system

def train_all():
    """
    Initiates the training sequence by calling train_system with force=True.
    """
    print("🚀 Auto-Trainer Initiated...")
    
    try:
        # We are forcing the training to run. This is the "auto_trainer" script.
        train_system(force=True)
        print("✅ Auto-Trainer finished successfully.")
        
    except Exception as e:
        print(f"❌ Auto-Trainer Error: {e}")

if __name__ == "__main__":
    train_all()
