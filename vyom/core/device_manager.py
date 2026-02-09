import platform
import os
import json

def get_device_info():
    """
    Analyzes local system to identify device type and OS.
    """
    # Since this is a CLI, we assume desktop/local execution
    device_type = 'desktop'
    
    # OS Detection
    os_name = platform.system().lower()
    
    return {
        "type": device_type,
        "os": os_name,
        "platform": platform.platform(),
        "user_agent": "VyomCLI/1.0"
    }

def sync_device_data(device_id, user_manager):
    """
    Updates user record with last used device type.
    """
    info = get_device_info()
    user_manager.update_user(device_id, {
        "last_device": info['type'],
        "last_os": info['os'],
        "last_seen_platform": info['platform']
    })
    return info
