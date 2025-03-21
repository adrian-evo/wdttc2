"""
Implement About custom action and check release
"""
import requests
import json
import os
from taskslocales import _
from devdata_path import *

project_url = 'https://github.com/adrian-evo/wdttc2'
api_url = f'https://api.github.com/repos/adrian-evo/wdttc2/releases'

def about_action(self):
    import ctypes
    mb_topmost_flag = 0x40000
    actual_version, new_version, description, released_at = self.check_release()
    if new_version <= actual_version:
        msg = project_url + '\n\n' + _('Your current version is {}\nThere are no new updates available').format(actual_version)
        ctypes.windll.user32.MessageBoxExW(None, msg, _("About"), 0 | 64 | mb_topmost_flag)
    else:
        msg = project_url + '\n\n' + _('Your current version is {}\nThe latest version is {}\nDescription: {}\nReleased at: {}').format(actual_version, new_version, description, released_at)
        ctypes.windll.user32.MessageBoxExW(None, msg, _("About"), 0 | 64 | mb_topmost_flag)

def check_release(self):
    # actual version from json
    with open(devdata_path('env.json')) as f:
        envdata = json.load(f)
    version = envdata['RELEASE']
    actual_version = int(''.join([i for i in version if i.isdigit()]))
    #actual_version = 22

    try:
        # Fetch the latest release information from GitLab
        response = requests.get(url=api_url)
        response.raise_for_status()
    
        latest_release = response.json()[0]

        # Extract the latest release info
        name = latest_release['name']
        new_version = int(''.join([i for i in name if i.isdigit()]))
        description = latest_release['body']
        released_at = latest_release['published_at']
        #print(f'Actual version: {actual_version}, New version: {new_version}, Description: {description}, Released at: {released_at}')
        return actual_version, new_version, description, released_at

    except:
        print(f"Cannot check the latest release from {api_url}")
        return actual_version, 0, '', ''

if __name__ == '__main__':
    #about_action()
    pass