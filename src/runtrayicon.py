"""
Execute trayicon as detached process
"""
import subprocess
import json
from os.path import exists
import os, sys
from devdata_path import *


def main():
    with open(devdata_path('env.json')) as f:
        data = json.load(f)
    vault = data['VAULT_FILE']
    assert exists(devdata_path(vault)), f"Vault file {vault} not found"

    if getattr(sys, 'frozen', False):
        cmd = [sys.executable, 'trayicon', vault]
    else:
        # Use pythonw.exe (windowless) from the same directory as the current interpreter
        python_dir = os.path.dirname(sys.executable)
        pythonw_exe = os.path.join(python_dir, 'pythonw.exe')
        
        # Fallback to python.exe if pythonw.exe doesn't exist
        if not exists(pythonw_exe):
            pythonw_exe = sys.executable
            
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', f'trayicon.py')
        cmd = [pythonw_exe, path, vault]

    if sys.platform.startswith('darwin'):
        subprocess.Popen(cmd, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    else:
        subprocess.Popen(cmd, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_BREAKAWAY_FROM_JOB)
        
if __name__ == '__main__':
    main()