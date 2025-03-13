"""
App keywords sample that are executed for Check in out tasks. To be customised or replaced with other actions.
"""
from playwright.sync_api import sync_playwright
from time import sleep
from taskslocales import *
from taskslocales import _
from common_keywords import *

class CustomKeywords:
    def __init__(self):
        self.BROWSER_TIMEOUT = 10000
        self.common = CommonKeywords()
        self.page = None
        self.browser = None
        self.p = None

    def check_in_app_task(self):
        """Check in App task"""
        self.open_checkin_app()
        self.fill_checkin_credentials()

        env = self.common.load_vault_file()
        if env['LEVEL_3_ACTIONS']['DO_CHECKIN_ACTION']:
            self.common.pause_execution(
                _('Automatic check in action was not implemented.')
            )
        else:
            self.common.pause_execution(
                _('Please click [Check In] button and then press OK to continue.')
            )
        self.close_checkin_app()

    def check_out_app_task(self):
        """Check out App task"""
        self.open_checkin_app()
        self.fill_checkin_credentials()

        env = self.common.load_vault_file()
        if env['LEVEL_3_ACTIONS']['DO_CHECKOUT_ACTION']:
            self.common.pause_execution(
                _('Automatic check out action was not implemented.')
            )
        else:
            self.common.pause_execution(
                _('Please click [Check Out] button and then press OK to continue.')
            )
        self.close_checkin_app()

    def verify_app_task(self):
        """Verify App task"""
        self.open_checkin_app()
        self.fill_checkin_credentials()
        self.close_checkin_app()

    def open_checkin_app(self):
        """Open a browser and go to check in URL"""
        env = self.common.load_vault_file()
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(headless=False, channel='chrome')
        self.page = self.browser.new_page()
        self.page.set_default_timeout(self.BROWSER_TIMEOUT)
        self.page.goto(env['MY_DATA']['CHECKIN']['URL'])

    def fill_checkin_credentials(self):
        """Fill username and password with enhanced security"""
        
        # Note: Don't use logging for password
        user, pw = self.common.retrieve_checkin_credentials()

        if not user or not pw or user == 'None' or pw == 'None':
            self.common.pause_execution(
                _('Cannot retrieve user or password. Check vault json file or the credential system under use.')
            )
        else:
            self.page.locator('input[name=username]').fill(user)
            self.page.locator('id=login-signin').click()
            try:
                self.page.wait_for_selector('input[name=password]', timeout=10000)
            except:
                self.common.pause_execution(
                    _('Cannot find password input field. Check the page or the credential system under use.')
                )
            self.common.pause_execution(
                _('This is a sample implementation. Continue similarly for own system login.')
            )

    def close_checkin_app(self):
        """Close the browser"""
        self.browser.close()
        self.p.stop()

    def custom_app_task(self):
        """Custom App task"""
        self.open_custom_app()
        self.fill_custom_credentials()

        env = self.common.load_vault_file()
        if env['LEVEL_3_ACTIONS']['DO_CUSTOM_ACTION']:
            self.common.pause_execution(
                _('Automatic custom action was not implemented.')
            )
        else:
            self.common.pause_execution(
                _('Please do custom task action and then press OK to continue!')
            )
        self.close_custom_app()

    def open_custom_app(self):
        """Open a browser and go to custom URL"""
        env = self.common.load_vault_file()
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(headless=False, channel='chrome')
        self.page = self.browser.new_page()
        self.page.set_default_timeout(self.BROWSER_TIMEOUT)
        self.page.goto(env['MY_DATA']['CUSTOM']['URL'])

        # approve url cookie
        self.page.locator('button >> text=AGREE').click()

    def fill_custom_credentials(self):
        """Filling username and password"""
        
        #user, pw = self.common.retrieve_custom_credentials()

        # Similar with above Fill Checkin Credentials if needed
        pass

    def close_custom_app(self):
        """Close the browser"""
        self.browser.close()
        self.p.stop()