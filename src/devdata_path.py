import os
import sys

def devdata_path(file_name):
    """Get the path for configuration files"""
    if getattr(sys, 'frozen', False):
        # Running standalone executable
        app_path = os.path.dirname(sys.executable)
    else:
        # Running in miniforge3 environment
        app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(app_path, 'devdata' + os.sep + file_name)
    #print(config_dir)
    
    return config_dir