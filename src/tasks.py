"""
Start and end of working day with Check in and out and Custom task actions
"""
from datetime import datetime, timedelta
from time import sleep
import json
import importlib.util
from taskslocales import _
from common_keywords import *

class WorkdayTasks:
    def __init__(self):
        # read the keywords from the env.json file
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        with open(os.path.join(parent_dir, 'devdata/env.json')) as f:
            envdata = json.load(f)
        keywords = envdata['APP_KEYWORDS']
        module_path = os.path.join(parent_dir, 'src', f"{keywords}.py")

        spec = importlib.util.spec_from_file_location(keywords, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.keywords = module.CustomKeywords()
        self.common = CommonKeywords()

    def workday_check_in(self):
        """Check in and Custom daily tasks"""
        env = self.common.load_vault_file()

        # Verify and perform check-in
        if env['LEVEL_2_ACTIONS']['OPEN_CHECKIN_APP']:
            self.keywords.check_in_app_task()

        # Save current check-in date and time
        date_now = datetime.now()
        # remove microseconds
        date_now -= timedelta(microseconds=date_now.microsecond)
        env['OUTPUT']['CHECKIN_DATE'] = date_now.isoformat(sep=' ')

        # Calculate and save check-out time
        date_out = date_now + self.common.parse_duration(env['MY_DATA']['STANDARD_WORKING_TIME'])
        env['OUTPUT']['CHECKOUT_CALC_DATE'] = date_out.isoformat(sep=' ')
        self.common.save_vault_file(env)

        # Welcome message
        if not env['LEVEL_1_ACTIONS']['SILENT_RUN']:
            text = '0 seconds' if not env['OUTPUT']['CUMULATED_OVER_UNDER_TIME'] \
                else env['OUTPUT']['CUMULATED_OVER_UNDER_TIME']
            undover = _('You have total undertime:') \
                if text[0] == '-' else _('You have total overtime:')
            self.common.pause_execution(
                f"{_('Welcome!')} \n {undover} {text}"
            )
        else:
            sleep(5)

    def workday_check_out(self):
        """Check out task"""
        env = self.common.load_vault_file()

        # Verify check-in status
        if not env['OUTPUT']['CHECKIN_DATE'] or env['OUTPUT']['CHECKIN_DATE'] == '00:00':
            self.common.pause_execution(
                f"{_('Check-in time is not available for today (not performed or workday ended).')} "
                f"{_('Cannot perform Check-out before Check-in.')}"
            )
            return

        # Perform check-out
        if env['LEVEL_2_ACTIONS']['OPEN_CHECKOUT_APP']:
            self.keywords.check_out_app_task()

        # Calculate times
        today_working_time, today_wt_diff, total_wt_diff = self.common.calculate_working_times()
        prefix = '-' if total_wt_diff < 0 else ''
        total_wt_diff = timedelta(seconds=abs(total_wt_diff))
        total_wt_diff -= timedelta(microseconds=total_wt_diff.microseconds)
        total_wt_diff = f"{prefix}{total_wt_diff}"

        # Update JSON
        env['OUTPUT']['CHECKIN_DATE'] = '00:00'
        env['OUTPUT']['CUMULATED_OVER_UNDER_TIME'] = total_wt_diff
        self.common.save_vault_file(env)

        # Goodbye message
        if not env['LEVEL_1_ACTIONS']['SILENT_RUN']:
            undover = _('You have total undertime:') \
                if total_wt_diff[0] == '-' else _('You have total overtime:')
            self.common.pause_execution(
                f"{_('Goodbye!')} \n {undover} {total_wt_diff}"
            )

    def workday_verify(self):
        """Display check in App and calculated working times only"""
        env = self.common.load_vault_file()

        if env['LEVEL_2_ACTIONS']['OPEN_CHECKIN_APP']:
            self.keywords.verify_app_task()

        # Verify check-in status
        if not env['OUTPUT']['CHECKIN_DATE'] or env['OUTPUT']['CHECKIN_DATE'] == '00:00':
            self.common.pause_execution(
                f"{_('Check-in time is not available for today (not performed or workday ended).')} "
                f"{_('Please start with a Check-in task in the morning.')}"
            )
            return

        # Calculate and display times
        today_working_time, today_wt_diff, total_wt_diff = self.common.calculate_working_times()
        today_working_time = timedelta(seconds=today_working_time)
        today_working_time -= timedelta(microseconds=today_working_time.microseconds)

        msg = _('Today undertime') if today_wt_diff < 0 \
            else _('Today overtime')
        prefix = '-' if total_wt_diff < 0 else ''
        today_wt_diff = timedelta(seconds=abs(today_wt_diff))
        today_wt_diff -= timedelta(microseconds=today_wt_diff.microseconds)
        today_wt_diff = f"{prefix}{today_wt_diff}"

        undover = _('You have total undertime:') if total_wt_diff < 0 \
            else _('You have total overtime:')
        prefix = '-' if total_wt_diff < 0 else ''
        total_wt_diff = timedelta(seconds=abs(total_wt_diff))
        total_wt_diff -= timedelta(microseconds=total_wt_diff.microseconds)
        total_wt_diff = f"{prefix}{total_wt_diff}"

        self.common.pause_execution(
            f"{_('Worked so far:')} {today_working_time} \n"
            f"{msg}: {today_wt_diff} \n"
            f"{undover} {total_wt_diff}"
        )

    def custom_task(self):
        """Do Custom task only"""
        # verify if Custom task should be performed and do it
        env = self.common.load_vault_file()
        if env['LEVEL_2_ACTIONS']['OPEN_CUSTOM_APP']:
            self.keywords.custom_app_task()


# tasks called from command line
if __name__ == '__main__':
    import sys
    tasks = WorkdayTasks()
    if sys.argv[1] == 'In':
        tasks.workday_check_in()
        #tasks.custom_task()
    elif sys.argv[1] == 'Out':
        tasks.workday_check_out()
    elif sys.argv[1] == 'Verify':
        tasks.workday_verify()
    elif sys.argv[1] == 'Custom':
        tasks.custom_task()
    else:
        print('Invalid argument. Please use In, Out, Verify or Custom.')