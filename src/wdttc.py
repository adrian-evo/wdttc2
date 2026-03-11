"""
All tasks entry point, mainly for pyinstaller to create exe file.
"""
import sys
import os
import ctypes
import importlib
import json
import subprocess
from devdata_path import *
from time import sleep
from os.path import exists

# Import for pyinstaller to include all necessary files
import common_keywords
import runtrayicon
import tasks
import taskslocales
import trayicon


def main():
    # Run icon task by default
    if len(sys.argv) < 2:
        arg = 'runtrayicon'
    else:
        arg = sys.argv[1]

    # When running tray icon, check for wdttc.ini; launch setup if missing
    if arg == 'runtrayicon':
        if getattr(sys, 'frozen', False):
            app_path = os.path.dirname(sys.executable)
        else:
            app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ini_file = os.path.join(app_path, 'wdttc.ini')
        if not exists(ini_file):
            setup_bat = os.path.join(app_path, 'setup-wdttc.bat')
            subprocess.Popen(
                ['cmd', '/c', setup_bat],
                cwd=app_path,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            sys.exit(0)

    with open(devdata_path('env.json')) as f:
        envdata = json.load(f)
    with open(devdata_path(envdata['VAULT_FILE'])) as f:
        appdata = json.load(f)
    sleep_time = envdata['TASK_WAIT_TIMEOUT']
    run_headless = appdata['LEVEL_2_ACTIONS'].get('RUN_HEADLESS', False)

    if len(sys.argv) > 2:
        msg = '[%s %s]' % (arg, sys.argv[2])
    else:
        msg = '[%s]' % arg

    # no timeout for runtrayicon
    if arg == 'runtrayicon' or run_headless:
        sleep_time = 0

    if sleep_time > 0:
        print("The %s task will be executed in %s seconds... Close the window to cancel." % (msg, sleep_time))
        for i in range(sleep_time,0,-1):
            print(f"{i}", end="\r", flush=True)
            sleep(1)

    # The argument is the same as module (filename), so we need to import the module
    # If module is not found under src, it will be searched under plugins
    module = importlib.import_module(arg)

    if len(sys.argv) > 2:
        module.main(sys.argv[2])
    else:
        module.main()


if __name__ == "__main__":
    main()