"""
Provides translation service to tray icon and tasks.py file
"""
import os
import gettext
import json
from devdata_path import *

class Translation:
    def __init__(self):
        self.template = None
        self.custom = None
        
    def get(self, text):
        # load translations only once
        if self.template is None:
            # read locale from env.json
            with open(devdata_path('env.json')) as f:
                data = json.load(f)
            locale = data['LOCALE']
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'locales')
            self.template = gettext.translation('template', localedir=path, languages=[locale])
            # custom translations are optional
            try:
                self.custom = gettext.translation('custom', localedir=path, languages=[locale])
            except FileNotFoundError:
                self.custom = None

        # get custom translation if available, otherwise use template translation
        if self.custom is not None:
            custom_text = self.custom.gettext(text)
            if custom_text != text:
                return custom_text
        return self.template.gettext(text)

# Translation instance
TRANS = Translation()

# Python variable to be used as _('Text')
_ = TRANS.get


# provides credential service based on the operating system (Credential Manager or Keychain)
import keyring

def retrieve_username(system):
    return keyring.get_password(system, 'username')

def retrieve_password(system, username):
    return keyring.get_password(system, username)

def main():
    import subprocess
    import sys
    from pathlib import Path

    head, tail = os.path.split(sys.executable)
    msgfmt = head + '/Tools/i18n/msgfmt.py'
    head, tail = os.path.split(Path(__file__))

    path_en = os.path.join(os.path.dirname(head), 'locales/en/LC_MESSAGES/')
    path_de = os.path.join(os.path.dirname(head), 'locales/de/LC_MESSAGES/')

    # compile english locale
    if os.path.exists(path_en + 'custom.po'):
        print('custom en translation exists')
        subprocess.run(["python", msgfmt, path_en + 'custom.po'])
    subprocess.run(["python", msgfmt, path_en + 'template.po'])

    # compile german locale
    if os.path.exists(path_de + 'custom.po'):
        print('custom de translation exists')
        subprocess.run(["python", msgfmt, path_de + 'custom.po'])
    subprocess.run(["python", msgfmt, path_de + 'template.po'])

    print('done')

# running this file will regenerate the locales
if __name__ == '__main__':
    main()