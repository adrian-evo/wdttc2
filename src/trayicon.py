"""
Display an icon with text and specific color in systray, and update specific vault.json file with times
  Grey - during the day, Yellow - 30' min before leave, Green - Should leave, Red - Left, Blue - During break.
  Next day in the morning should be Red, means check-in not performed
the update is based on data from custom vault.json given as argument to main
"""

from threading import Event
import pystray
from pystray import Menu, MenuItem
from PIL import Image, ImageDraw,ImageFont
import os, sys, json
from os.path import exists
import subprocess
from datetime import datetime, timedelta
import psutil
from taskslocales import _
from devdata_path import *
from common_keywords import *

# Determine if running as PyInstaller bundle
if getattr(sys, 'frozen', False):
    # If running as PyInstaller bundle
    application_path = sys._MEIPASS
else:
    # If running as script
    application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add plugins directory to path
#plugins_path = os.path.join(application_path, 'plugins')
sys.path.append(application_path)

# Try to import overtimemenu_dev first, fallback to overtimemenu
try:
    from plugins import overtimemenu_dev as overtimemenu
except ImportError:
    from plugins import overtimemenu

from plugins import aboutaction

# icon data
icon_size = (48, 48)
font_size = 22

# platform specific variables - macOS or Windows
if sys.platform.startswith('darwin'):
    ttf_font = 'SFNS.ttf'
    run_task_command = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'run-tasks.sh')
    python_str = 'python'
else:
    ttf_font = 'arialbd.ttf'
    run_task_command = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'run-tasks.bat')
    python_str = 'python.exe'

# how often to update the tray icon, color and tooltip text. default 10 seconds
event_time_sleep = 10

# time gap to display notification for new day started, in seconds. default 60 seconds
new_day_notification_time_gap = 60

# workday tray icon class
class WorkdayTrayIcon:
    instance = None

    def __init__(self, vault):
        # is break enabled or active
        self.break_enabled = False
        self.break_active = False

        # is overtime menu visible or active
        self.overtime_active = False

        self.exit_event = None
        self.icon = None
        self.vault = vault

        # store last activity time of the icon
        self.last_activity_time = None

        # Double-click detection
        self.last_click_time = 0
        self.double_click_threshold = 0.5  # 500ms threshold for double-click
        self.single_click_timer = None  # Timer for delayed single-click handling
        self.double_click_detected = False  # Flag to prevent single-click when double-click occurs

    def create_icon(self):
        self.exit_event = Event()

        # create image
        img = Image.new('RGBA', icon_size)
        d = ImageDraw.Draw(img)

        # add text to the image
        font_type  = ImageFont.truetype(ttf_font, font_size)
        d.text((10, 0.5), f"00\n00", font=font_type)

        # display icon image in systray 
        self.icon = pystray.Icon(_('Check In-Out time'))

        # icon menus
        actual_version, new_version, description, released_at = self.check_release()        

        if new_version <= actual_version:
            about = _('About')
        else:
            about = _('About (Upgrade available)')

        self.icon.menu = Menu(
            MenuItem('', lambda: self.handle_click(), default=True, visible=False),  # Hidden click handler
            MenuItem(_('Check In'), lambda : self.checkin_action()), 
            MenuItem(_('Check Out'), lambda : self.checkout_action()), 
            MenuItem(_('Verify'), lambda : self.verify_action()), 
            MenuItem(_('Custom'), lambda : self.custom_action()), 
            Menu.SEPARATOR,
            # Update the state in `break_action` and return the new state in a `checked` callable
            #MenuItem(_('Break'), self.break_action, checked=lambda _: self.break_active, default=True, enabled=lambda _: self.break_enabled), 
            MenuItem(_('Break'), self.break_action, checked=lambda _: self.break_active, enabled=lambda _: self.break_enabled), 
            MenuItem(_('Overtime'), self.overtime_action, checked=lambda _: self.overtime_active, visible=lambda _: self.overtime_visible), 
            MenuItem(_('Reset'), lambda : self.reset_action()), 
            Menu.SEPARATOR,
            MenuItem(_('Setup'), lambda : self.setup_action()), 
            MenuItem(about, lambda : self.about_action()), 
            MenuItem(_('Quit'), lambda : self.exit_action()), 
        )
        self.icon.icon = img
        self.icon.run(WorkdayTrayIcon.setup)

    @staticmethod
    def setup(icon) -> None:
        icon.visible = True
        while not WorkdayTrayIcon.instance.exit_event.is_set():
            WorkdayTrayIcon.instance.update_icon()
            WorkdayTrayIcon.instance.other_action()
            WorkdayTrayIcon.instance.exit_event.wait(event_time_sleep)  # allows exiting while waiting. time.sleep would block

    def update_icon(self):
        # the update is based on data from custom vault.json given as argument to main
        with open(self.vault) as f:
            data = json.load(f)

        checkin_str = data['OUTPUT']['CHECKIN_DATE']
        checkout_str = data['OUTPUT']['CHECKOUT_CALC_DATE']
        # check if it is old format with miliseconds
        if '.' in checkin_str:
            checkin_str = checkin_str.split('.')[0]
        if '.' in checkout_str:
            checkout_str = checkout_str.split('.')[0]
        timenow = datetime.now()

        # 1. If check-in is empty it means first run. Icon color - RED
        if checkin_str == '':
            self.icon.title = _('Welcome!') + ' ' +_('Please start with a Check-in task in the morning.')
            self.update_image(timenow.strftime("%H:%M"), data['ICON_DATA']['CHECKOUT_DONE_COLOR'])
            self.break_enable(False)
            return

        # 2. If check-in is 00:00 it means check-out was performed. Icon color - RED
        if checkin_str == '00:00' and checkout_str != '00:00':
            checkout_calc = datetime.strptime(checkout_str, '%Y-%m-%d %H:%M:%S')
            # On the same day, display End of the working day. On a new day, display New day started.
            if timenow.date() > checkout_calc.date():
                self.icon.title = _('New day started!') + ' ' +_('Please start with a Check-in task in the morning.')
                if self.last_activity_time is None:
                    self.last_activity_time = timenow
                    self.update_image(timenow.strftime("%H:%M"), data['ICON_DATA']['CHECKOUT_DONE_COLOR'])
            else:
                self.icon.title = _('End of the working day')
                self.update_image(checkin_str, data['ICON_DATA']['CHECKOUT_DONE_COLOR'])
            self.break_enable(False)

            # On a new day, reset the checkout and display a tooltip notification only once, after time gap minutes of activity
            if timenow.date() > checkout_calc.date():
                time_gap = (timenow - self.last_activity_time).total_seconds()
                #print('Time gap since last activity: {} seconds'.format(time_gap))
                if time_gap > new_day_notification_time_gap:
                    # reset last activity time
                    self.last_activity_time = None

                    CommonKeywords().show_tooltip(_('New day started!') + ' ' + _('Please start with a Check-in task in the morning.'))
                    data['OUTPUT']['CHECKOUT_CALC_DATE'] = '00:00'
                    with open(self.vault, 'w') as f:
                        json.dump(data, f, ensure_ascii=True, indent=4)
            return

        if checkin_str == '00:00' and checkout_str == '00:00':
            self.icon.title = _('New day started!') + ' ' +_('Please start with a Check-in task in the morning.')
            self.update_image(checkout_str, data['ICON_DATA']['CHECKOUT_DONE_COLOR'])
            self.break_enable(False)
            return

        # 3. Update Passed, Undertime or Overtime tooltip if check-in was performed for today. Icon color - GREY
        self.break_enable(True)
        checkin = datetime.strptime(checkin_str, '%Y-%m-%d %H:%M:%S')
        checkout_calc = datetime.strptime(checkout_str, '%Y-%m-%d %H:%M:%S')

        # If break is active, then the CHECKOUT_CALC_DATE need to be incremented after the break
        if self.break_active:
            # save the start of break if not saved already
            if data['OUTPUT']['BREAK_TIME_TODAY'] == '':
                data['OUTPUT']['BREAK_TIME_TODAY'] = timenow.strftime('%Y-%m-%d %H:%M:%S')
                with open(self.vault, 'w') as f:
                    json.dump(data, f, ensure_ascii=True, indent=4)

            break_time = datetime.strptime(data['OUTPUT']['BREAK_TIME_TODAY'], '%Y-%m-%d %H:%M:%S')
            minutes = (timenow - break_time).total_seconds() / 60
            break_time += timedelta(minutes=minutes)
            passed_break_str = (datetime.fromordinal(1) + timedelta(minutes=minutes)).time().strftime("%H:%M")
            self.icon.title = _('Break is active for {} hours. Click to deactivate it and to continue working.').format(passed_break_str)
            self.update_image(passed_break_str, data['ICON_DATA']['BREAK_TIME_COLOR'])
            return
        else:
            # reset the break if not reset already
            if data['OUTPUT']['BREAK_TIME_TODAY'] != '':
                # increment and save CHECKOUT_CALC_DATE, with the amount of break time
                break_time = datetime.strptime(data['OUTPUT']['BREAK_TIME_TODAY'], '%Y-%m-%d %H:%M:%S')
                minutes = (timenow - break_time).total_seconds() / 60
                checkout_calc += timedelta(minutes=minutes)
                data['OUTPUT']['BREAK_TIME_TODAY'] = ''
                data['OUTPUT']['CHECKOUT_CALC_DATE'] = checkout_calc.strftime('%Y-%m-%d %H:%M:%S')
                with open(self.vault, 'w') as f:
                    json.dump(data, f, ensure_ascii=True, indent=4)

        checkin_time = checkin.strftime("%H:%M")
        checkout_time = checkout_calc.strftime("%H:%M")
        hover_text = _('Check In-Out time') + ': {}-{}'.format(checkin_time, checkout_time)
        passed = str(timenow - checkin).split('.',2)[0]
        if timenow < checkout_calc:
            left = str(checkout_calc - timenow).split('.',2)[0]
            hover_text = hover_text + ' ' + _('[Passed: {}, Undertime: {}]').format(passed, left)
            # 30' before end of the day - YELLOW, otherwise - GREY
            if (checkout_calc - timenow) <= timedelta(minutes=data['ICON_DATA']['CHECKOUT_WARNING_MINUTES']):
                self.update_image(checkout_time, data['ICON_DATA']['CHECKOUT_WARNING_COLOR'])
            else:
                self.update_image(checkout_time, data['ICON_DATA']['CHECKIN_DONE_COLOR'])
        # should check out - GREEN
        else:
            extra = str(timenow - checkout_calc).split('.',2)[0]
            hover_text = hover_text + ' ' + _('[Passed: {}, Overtime: {}]').format(passed, extra)
            self.update_image(checkout_time, data['ICON_DATA']['OVERTIME_STARTED_COLOR'])

        if self.overtime_active:
            self.update_image(checkout_time, self.overtime_checked_color)

        # execute a custom action when overtime starts
        if self.overtime_active and timenow > checkout_calc:
            self.overtime_active = False
            self.icon.update_menu()
            self.overtime_custom_action()

        # update the tooltip
        self.icon.title = hover_text

        # reset last activity time of the icon
        self.last_activity_time = None

    def update_image(self, text, color):
        # equal sign (=) in the color name means icon color before and text color after the equal sign
        if "=" in color:
            s = color.split('=')
            icon_color=s[0]
            font_color=s[1]
        else:
            icon_color=color
            font_color="None"

        # icon
        if icon_color == "None":
            img = Image.new('RGBA', icon_size)
        else:
            img = Image.new('RGBA', icon_size, color=icon_color)
        d = ImageDraw.Draw(img)

        # text
        font_type  = ImageFont.truetype(ttf_font, font_size)
        t = text.split(':')
        icon_text = t[0] + ':' + '\n' + t[1]
        #icon_text = text.replace(":", "\n")
        if font_color == "None":
            d.text((10, 0.5), f"{icon_text}", font=font_type)
        else:
            d.text((10, 0.5), f"{icon_text}", font=font_type, fill=font_color)
        self.icon.icon = img

    def exit_action(self):
        # Cancel any pending single click timer
        if hasattr(self, 'single_click_timer') and self.single_click_timer:
            self.single_click_timer.cancel()
            
        self.icon.visible = False
        self.exit_event.set()
        self.icon.stop()

    def _run_task_hidden(self, task_name, hide_window=True):
        """Helper method to run tasks with optional hidden window on Windows
        
        Args:
            task_name: Name of the task to run
            hide_window: If True, hide the console window (default: True)
        """
        creationflags = 0
        env = os.environ.copy()

        if hide_window and sys.platform == 'win32':
            creationflags = subprocess.CREATE_NO_WINDOW
            env['WDTTC_HEADLESS'] = '1'
        else:
            env['WDTTC_HEADLESS'] = '0'
            
        return subprocess.Popen(
            [run_task_command, task_name],
            creationflags=creationflags,
            env=env
        )

    def checkin_action(self):
        # reset break if it is active during check in
        self.break_active = False
        self.update_icon()
        
        # Read vault to check if headless mode is enabled
        with open(self.vault) as f:
            data = json.load(f)
        hide_window = data['LEVEL_2_ACTIONS'].get('OPEN_HEADLESS_APP', False)
        
        return self._run_task_hidden('In', hide_window)

    def checkout_action(self):
        # reset break if it is active during check out
        self.break_active = False
        self.update_icon()
        
        # Read vault to check if headless mode is enabled
        with open(self.vault) as f:
            data = json.load(f)
        hide_window = data['LEVEL_2_ACTIONS'].get('OPEN_HEADLESS_APP', False)
        
        return self._run_task_hidden('Out', hide_window)

    def verify_action(self):
        # Verify action typically doesn't need headless mode
        return self._run_task_hidden('Verify', hide_window=True)

    def custom_action(self):
        # Custom action can use headless mode
        with open(self.vault) as f:
            data = json.load(f)
        hide_window = data['LEVEL_2_ACTIONS'].get('OPEN_HEADLESS_APP', False)
        
        return self._run_task_hidden('Custom', hide_window)

    def setup_action(self):
        # Setup should always show window for user interaction
        return self._run_task_hidden('Setup', hide_window=True)

    def break_action(self, icon, item):
        if not self.break_enabled:
            return
        self.break_active = not item.checked
        self.update_icon()

    def break_enable(self, enable):
        if self.break_enabled != enable:
            self.break_enabled = enable
            self.icon.update_menu()

    def overtime_action(self, icon, item):
        self.overtime_active = not item.checked
        self.update_icon()

    def reset_action(self):
        import ctypes
        mb_topmost_flag = 0x40000
        ret = ctypes.windll.user32.MessageBoxExW(None, _("This action will reset to default all [OUTPUT] related data in your vault file! \n Continue?"), _("Reset Warning"), 4 | 48 | mb_topmost_flag)

        if ret == 6:
            with open(self.vault) as f:
                data = json.load(f)
            data['OUTPUT']['CUMULATED_OVER_UNDER_TIME'] = ''
            data['OUTPUT']['CHECKIN_DATE'] = ''
            data['OUTPUT']['CHECKOUT_CALC_DATE'] = ''
            data['OUTPUT']['BREAK_TIME_TODAY'] = ''
            with open(self.vault, 'w') as f:
                json.dump(data, f, ensure_ascii=True, indent=4)

    def handle_click(self):
        """Handle single click with double-click detection"""
        import time
        import threading
        
        current_time = time.time()
        
        # Check if this is a double-click (within threshold)
        if current_time - self.last_click_time < self.double_click_threshold:
            #print("Double-click detected")
            # Set flag to prevent single-click execution
            self.double_click_detected = True
            # Cancel any pending single click action
            if hasattr(self, 'single_click_timer') and self.single_click_timer:
                self.single_click_timer.cancel()
            # Handle double-click
            self.handle_double_click()
        else:
            # Potential single click - wait to see if double-click follows
            #print("Single click detected, waiting for double-click...")
            self.double_click_detected = False
            
            # Cancel any existing timer first
            if hasattr(self, 'single_click_timer') and self.single_click_timer:
                self.single_click_timer.cancel()
            
            # Use a timer to delay single click action
            self.single_click_timer = threading.Timer(self.double_click_threshold, self.handle_single_click)
            self.single_click_timer.start()
            
        self.last_click_time = current_time

    def handle_single_click(self):
        """Handle single click action (delayed)"""
        with open(self.vault) as f:
            data = json.load(f)
        if not data['LEVEL_1_ACTIONS']['ICON_CLICK_BREAK_ON_OFF']:
            return
        checkin_str = data['OUTPUT']['CHECKIN_DATE']
        checkout_str = data['OUTPUT']['CHECKOUT_CALC_DATE']
        if checkin_str != '' and checkin_str != '00:00' and checkout_str != '00:00':
            # Only execute if double-click wasn't detected
            if not getattr(self, 'double_click_detected', False):
                #print("Single click action executed")
                self.break_active = not self.break_active
                self.icon.update_menu()
                self.update_icon()
        
        # Clean up
        self.single_click_timer = None

    def handle_double_click(self):
        """Handle double-click action based on current state"""
        with open(self.vault) as f:
            data = json.load(f)
        if not data['LEVEL_1_ACTIONS']['ICON_DOUBLE_CLICK_CHECKIN_OUT']:
            return

        checkin_str = data['OUTPUT']['CHECKIN_DATE']
        checkout_str = data['OUTPUT']['CHECKOUT_CALC_DATE']
        
        # On a new day or first run, double-click should check-in
        if checkin_str == '' or checkin_str == '00:00':
            # Ask user confirmation
            if data['LEVEL_1_ACTIONS']['ICON_DOUBLE_CLICK_CONFIRMATION']:
                import ctypes
                mb_topmost_flag = 0x40000
                ret = ctypes.windll.user32.MessageBoxExW(
                    None, 
                    _("Double-click detected. Do you want to checkin?"), 
                    _("Checkin Confirmation"), 
                    4 | 32 | mb_topmost_flag  # 4=Yes/No buttons, 32=Question icon
                )
            else:
                ret = 6  # Simulate Yes
            if ret == 6:  # User clicked Yes
                self.checkin_action()
            # If user clicked No (ret == 7), do nothing
        # During work hours, double-click should check-out
        elif checkin_str != '00:00' and checkout_str != '00:00':
            # Ask user confirmation
            if data['LEVEL_1_ACTIONS']['ICON_DOUBLE_CLICK_CONFIRMATION']:
                import ctypes
                mb_topmost_flag = 0x40000
                ret = ctypes.windll.user32.MessageBoxExW(
                    None, 
                    _("Double-click detected. Do you want to checkout?"), 
                    _("Checkout Confirmation"), 
                    4 | 32 | mb_topmost_flag  # 4=Yes/No buttons, 32=Question icon
                )
            else:
                ret = 6  # Simulate Yes            
            if ret == 6:  # User clicked Yes
                self.checkout_action()
            # If user clicked No (ret == 7), do nothing

        # Otherwise, double-click should verify
        else:
            pass


def main(arg):
    # vault file given as argument
    vault = devdata_path(arg)
    print(vault)

    # save own process pid
    assert exists(vault)
    with open(vault) as f:
        data = json.load(f)

    # check if it is running and don't run again
    for p in psutil.process_iter(["pid", "name"]):
        if p.info['name'] == python_str and p.info['pid'] == data['OUTPUT']['TRAY_ICON_PID']:
            print('Process with pid {} and name "{}" is running.'.format(p.info['pid'], p.info['name']))
            sys.exit()
        else:
            print('Workday tray icon not running. Starting.')
            break

    data['OUTPUT']['TRAY_ICON_PID'] = os.getpid()
    with open(vault, 'w') as f:
        json.dump(data, f, ensure_ascii=True, indent=4)

    # create workday tray icon instance
    WorkdayTrayIcon.check_release = aboutaction.check_release
    WorkdayTrayIcon.about_action = aboutaction.about_action
    WorkdayTrayIcon.overtime_visible = overtimemenu.overtime_menu_item_visible
    WorkdayTrayIcon.overtime_checked_color = overtimemenu.overtime_checked_color
    WorkdayTrayIcon.overtime_custom_action = overtimemenu.overtime_custom_action
    WorkdayTrayIcon.other_action = overtimemenu.other_action
    
    WorkdayTrayIcon.instance = WorkdayTrayIcon(vault)
    WorkdayTrayIcon.instance.create_icon()


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('No vault.json was specified.')
        sys.exit(1)
    main(sys.argv[1])