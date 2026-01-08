import platform
import os
import json
from flask import request

def get_device_info():
    """
    Analyzes request headers to identify device type and OS.
    """
    ua = request.headers.get('User-Agent', '').lower()
    
    # Simple Device Detection
    if any(m in ua for m in ['android', 'iphone', 'ipad', 'windows phone', 'mobile']):
        device_type = 'mobile'
    else:
        device_type = 'desktop'
        
    # OS Detection
    os_name = 'unknown'
    if 'windows' in ua: os_name = 'windows'
    elif 'android' in ua: os_name = 'android'
    elif 'iphone' in ua or 'ipad' in ua: os_name = 'ios'
    elif 'linux' in ua: os_name = 'linux'
    elif 'mac' in ua: os_name = 'macos'
    
    return {
        "type": device_type,
        "os": os_name,
        "platform": platform.system(),
        "user_agent": ua
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
