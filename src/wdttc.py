"""
All tasks entry point, mainly for pyinstaller to create exe file.
"""
import sys
import ctypes
import importlib
import json
from devdata_path import *
from time import sleep
from os.path import exists

# Import for pyinstaller to include all necessary files
import common_keywords
import runtrayicon
import tasks
import taskslocales
import trayicon


def pause_execution(msg):
    mb_topmost_flag = 0x40000
    ctypes.windll.user32.MessageBoxExW(None, msg, "Info", 0 | 64 | mb_topmost_flag)

def main():
    # Run icon task by default
    if len(sys.argv) < 2:
        arg = 'runtrayicon'
    else:
        arg = sys.argv[1]
    with open(devdata_path('env.json')) as f:
        envdata = json.load(f)
    sleep_time = envdata['TASK_WAIT_TIMEOUT']

    if len(sys.argv) > 2:
        msg = '[%s %s]' % (arg, sys.argv[2])
    else:
        msg = '[%s]' % arg
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