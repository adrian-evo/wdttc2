"""
Common keywords for all tasks
"""
import json
import datetime
from datetime import datetime, timedelta
import ctypes
from os.path import exists
import re
from taskslocales import *
from taskslocales import _
from devdata_path import *

class CommonKeywords:
    def __init__(self):
        with open(devdata_path('env.json')) as f:
            data = json.load(f)
        self.vault = devdata_path(data['VAULT_FILE'])
        assert exists(self.vault)

    def load_vault_file(self):
        """Load vault file"""
        with open(self.vault) as f:
            return json.load(f)
    
    def save_vault_file(self, data):
        """Save vault file"""
        with open(self.vault, 'w') as f:
            json.dump(data, f, ensure_ascii=True, indent=4)

    def pause_execution(self, msg):
        mb_topmost_flag = 0x40000
        ctypes.windll.user32.MessageBoxExW(None, msg, _("Info"), 0 | 64 | mb_topmost_flag)

    def parse_duration(self, duration_str):
        # Remove any whitespace and convert to lowercase
        duration_str = duration_str.lower().strip()
        
        # Define regex patterns for different formats
        patterns = [
            # "1 day, 0:09:11" or "2 days, 1:30:45"
            r'^(\d+)\s*days?\s*,\s*(\d+):(\d+):(\d+)(?:\.(\d+))?$',
            # "hours:minutes:seconds.milliseconds"
            r'^(\d+):(\d+):(\d+)\.(\d+)$',
            # "hours:minutes:seconds"
            r'^(\d+):(\d+):(\d+)$',
            # "8 hours 30 minutes" or "8 hours"
            r'^(\d+)\s*hours?\s*(?:(\d+)\s*minutes?)?$',
            # "8h30'" or "8h"
            r'^(\d+)h(?:(\d+)\'?)?$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, duration_str)
            if match:
                groups = match.groups()
                
                # Handle "days, hours:minutes:seconds" format
                if pattern.startswith(r'^(\d+)\s*days?'):
                    days = int(groups[0])
                    hours = int(groups[1])
                    minutes = int(groups[2])
                    seconds = int(groups[3])
                    microseconds = 0
                    if groups[4]:  # If milliseconds are present
                        ms_str = groups[4].ljust(6, '0')[:6]
                        microseconds = int(ms_str)
                    return timedelta(days=days, hours=hours, minutes=minutes,
                                seconds=seconds, microseconds=microseconds)
                
                # Handle "hours:minutes:seconds.milliseconds" format
                elif len(groups) == 4:
                    hours = int(groups[0])
                    minutes = int(groups[1])
                    seconds = int(groups[2])
                    ms_str = groups[3].ljust(6, '0')[:6]
                    microseconds = int(ms_str)
                    return timedelta(hours=hours, minutes=minutes,
                                seconds=seconds, microseconds=microseconds)
                
                # Handle "hours:minutes:seconds" format
                elif len(groups) == 3:
                    hours = int(groups[0])
                    minutes = int(groups[1])
                    seconds = int(groups[2])
                    return timedelta(hours=hours, minutes=minutes, seconds=seconds)
                
                # Handle other formats
                hours = int(groups[0])
                minutes = int(groups[1]) if groups[1] else 0
                return timedelta(hours=hours, minutes=minutes)
        
        raise ValueError(f"Unable to parse duration string: {duration_str}")

    def calculate_working_times(self):
        """Return working times in seconds"""
        # read today check-in date and time and standard working time from json file
        env = self.load_vault_file()

        # 1. calculate already worked time today compared with check-in time
        today_working_seconds = (datetime.now() - datetime.fromisoformat(env['OUTPUT']['CHECKIN_DATE'])).total_seconds()

        # 2. calculate today under or overtime compared with standard working time
        standard_working_seconds = self.parse_duration(env['MY_DATA']['STANDARD_WORKING_TIME']).total_seconds()
        today_wt_diff = today_working_seconds - standard_working_seconds

        # 3. calculate cumulated under or overtime to date
        cumulated = env['OUTPUT']['CUMULATED_OVER_UNDER_TIME']       
        if cumulated != '':
            if cumulated[0] == '-':
                cumulated_seconds = -self.parse_duration(cumulated[1:]).total_seconds()
            else:
                try:
                    cumulated_seconds = self.parse_duration(cumulated).total_seconds()
                except ValueError:
                    cumulated_seconds = 0
                    print("The ['OUTPUT']['CUMULATED_OVER_UNDER_TIME'] should be in the format 'x days, hh:mm:ss' or 'hh:mm:ss'.")
            total_wt_diff = cumulated_seconds + today_wt_diff
        else:
            total_wt_diff = today_wt_diff

        return today_working_seconds, today_wt_diff, total_wt_diff

    def retrieve_checkin_credentials(self):
        """Get User and Password fields based on Title from vault json or Keepass database"""
        env = self.load_vault_file()

        # if user field from json is empty, try to use keyring specific database
        if env['MY_DATA']['CHECKIN']['USER'] == '':
            user = retrieve_username(env['MY_DATA']['CHECKIN']['SYSTEM'])
        else:
            user = env['MY_DATA']['CHECKIN']['USER']

        if env['MY_DATA']['CHECKIN']['PASSWORD'] == '':
            pw = retrieve_password(env['MY_DATA']['CHECKIN']['SYSTEM'], user)
        else:
            pw = env['MY_DATA']['CHECKIN']['PASSWORD']

        if not user or not pw:
            self.common.pause_execution(
                _('Cannot retrieve user or password. Check vault json file or the credential system under use.')
            )
            raise Exception("Failed to retrieve credentials")

        return user, pw

    def retrieve_custom_credentials(self):
        """Get User and Password fields for custom system"""
        env = self.load_vault_file()

        if env['MY_DATA']['CUSTOM']['USER'] == '':
            user = retrieve_username(env['MY_DATA']['CUSTOM']['SYSTEM'])
        else:
            user = env['MY_DATA']['CUSTOM']['USER']

        if env['MY_DATA']['CUSTOM']['PASSWORD'] == '':
            pw = retrieve_password(env['MY_DATA']['CUSTOM']['SYSTEM'], user)
        else:
            pw = env['MY_DATA']['CUSTOM']['PASSWORD']

        if not user or not pw:
            self.common.pause_execution(
                _('Cannot retrieve user or password. Check vault json file or the credential system under use.')
            )
            raise Exception("Failed to retrieve credentials")

        return user, pw