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
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', f'trayicon.py')
        cmd = ["python", path, vault]

    if sys.platform.startswith('darwin'):
        subprocess.Popen(cmd, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    else:
        subprocess.Popen(cmd, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_BREAKAWAY_FROM_JOB)

if __name__ == '__main__':
    main()