#! /usr/bin/env python

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from ConfigParser import ConfigParser
from warnings import warn
from datetime import datetime, timedelta


COLBERT_REPORT_URL = 'http://impresario.comedycentral.com/show/5b2eb3b0eb99f143'
DAILY_SHOW_URL = 'http://impresario.comedycentral.com/show/e0d100ed55c2dc9e'


def date_range(start, end, increment=1):
    """Generates a date range from start to end inclusive by increment days."""
    time_inc = timedelta(days=increment)
    current = start
    while current <= end:
        yield current
        current += time_inc


def parse_date(s):
    """Converts a string in the form mm/dd/yyyy into a datetime object."""
    return datetime.strptime(s, '%m/%d/%Y')


class Config:

    """A utility class for handling configuration of the colbertix config file."""

    def __init__(self, file_name):
        self.parser = ConfigParser()
        self.file_name = file_name
        self.parser.read(self.file_name)
        self.str_config_options = ['url']
        self.int_config_options = ['wanted_tickets', 'wait_seconds']
        self.date_config_options = ['start_date', 'end_date']
        self.dates_config_options = ['bad_dates']
        self.user_info_keys = ['first_name', 'last_name', 'zip', 'state', 'daytime_phone',
                               'evening_phone', 'mobile_phone', 'email']

    def get(self, section, name):
        """Returns the string value for given section and option name."""
        return self.parser.get(section, name)

    def get_date(self, section, name):
        """Returns the date value for given section and option name."""
        return parse_date(self.get(section, name))

    def get_int(self, section, name):
        """Returns the int value for given section and option name."""
        return self.parser.getint(section, name)

    def get_dates(self, section, name):
        """Returns the date list value for given section and option name."""
        def expand_to_dates(dates_and_ranges):
            result = []
            for date_or_range in dates_and_ranges:
                try:
                    bd = date_or_range.split('-')
                    if len(bd) == 1 and bd[0].strip() != '':
                        result.append(parse_date(bd[0]))
                    elif len(bd) == 2:
                        start, end = [parse_date(item) for item in bd]
                        result += list(date_range(start, end))
                except ValueError as date_error:
                    warn("failed to parse date '%s': %s" % (date_or_range, date_error.message))
            return result
        date_strings = [val.strip() for val in self.get(section, name).split(',')]
        return expand_to_dates(date_strings)

    def get_user_info(self):
        """Returns a dict containing user information options."""
        return dict([(key, self.get('user-info', key)) for key in self.user_info_keys])

    def get_config_options(self):
        """Returns a dict containing program configuration options."""
        result = dict()
        result.update(dict([(key, self.get('config', key)) for key in self.str_config_options]))
        result.update(dict([(key, self.get_int('config', key)) for key in self.int_config_options]))
        result.update(dict([(key, self.get_date('config', key)) for key in self.date_config_options]))
        result.update(dict([(key, self.get_dates('config', key)) for key in self.dates_config_options]))
        return result


class TicketBot(object):

    """A bot that can poll the Colbert Report web site and sign up for tickets.

        Usage:

        from colbertix import Config, TicketBot

        cfg = Config('config.ini')
        user_info = cfg.get_user_info()
        config_options = cfg.get_config_options()

        ticket_bot = TicketBot()
        ticket_bot.reserve_tickets(info=user_info, **config_options)
    """

    def __init__(self, driver=None):
        """Initializer for the bot. It will start the web browser and wait for commands."""
        self.attempts = None
        self.finished = None
        if driver:
            self.driver = driver
        else:
            self._driver_init(webdriver.Chrome())

    def _driver_init(self, driver):
        """Initializes the driver implementation."""
        driver.implicitly_wait(1)
        driver.maximize_window()
        self.driver = driver

    def browse_to(self, url):
        """Requests the ticket website. This will refresh the page as well."""
        self.driver.get(url)

    def get_num_tickets(self):
        """Attempts to extract the number of tickets from the current page."""
        try:
            elem_css = "#cont_active_event_ticket_available > span"
            num_tickets_str = self.driver.find_element_by_css_selector(elem_css).text
            return int(num_tickets_str)
        except NoSuchElementException:
            return 0

    def get_ticket_date(self):
        """Attempts to extract the date tickets are available from the page."""
        try:
            elem_css = "span.current_date"
            datestr = self.driver.find_element_by_css_selector(elem_css).text
            return datestr, datetime.strptime(datestr, "%B %d, %Y")
        except NoSuchElementException:
            return None, None

    def register_form(self, wanted_tickets, info):
        """Fills out the registration form on the current page."""
        d = self.driver

        if wanted_tickets == 1:
            ticket_sel = "1 ticket"
        else:
            ticket_sel = "%s tickets" % wanted_tickets

        Select(d.find_element_by_id("fld_tickets_number")).select_by_visible_text(ticket_sel)    
        d.find_element_by_id("fld_firstname").send_keys(info['first_name'])
        d.find_element_by_id("fld_lastname").send_keys(info['last_name'])
        d.find_element_by_id("fld_zip").send_keys(info['zip'])
        Select(d.find_element_by_id("fld_state")).select_by_visible_text(info['state'])
        d.find_element_by_id("fld_phone_daytime").send_keys(info['daytime_phone'])
        d.find_element_by_id("fld_phone_evening").send_keys(info['evening_phone'])
        d.find_element_by_id("fld_phone_mobile").send_keys(info['mobile_phone'])
        d.find_element_by_id("fld_email").send_keys(info['email'])
        d.find_element_by_id("fld_emailVerify").send_keys(info['email'])
        d.find_element_by_id("fld_terms").click()
        d.find_element_by_id("lnk_form_ticket_submit").click()

    def sign_up(self, url=COLBERT_REPORT_URL, info=None, wanted_tickets=2, start_date=None, end_date=None,
                bad_dates=None):

        """Runs a single attempt to sign up for tickets. 
           Returns True if successful, otherwise False."""

        self.browse_to(url)

        # Determine if there are an acceptable number of tickets available
        num_tickets = self.get_num_tickets()
        if num_tickets < wanted_tickets:
            print "%s of %s tickets available, not attempting sign-up." % (num_tickets, wanted_tickets)
            return False

        (ticket_datestr, ticket_date) = self.get_ticket_date()
        if ticket_date is None:
            print "Could not determine date of tickets, not attempting sign-up."
            return False

        # Determine if the tickets are for an acceptable date
        if (start_date and ticket_date < start_date) or (end_date and ticket_date > end_date) \
                or (bad_dates and ticket_date in bad_dates):
            print "%s tickets are available for %s, but it's bad date for you." % (num_tickets, ticket_datestr)
            return False

        print "Attempting to register for %s tickets on %s" % (wanted_tickets, ticket_datestr)
        self.register_form(wanted_tickets, info)

        return True

    def take_screenshot(self, msgtype="SUCCESS"):

        """Takes picture of the web browser screen."""

        self.driver.get_screenshot_as_file("tickets-%s-%s.png" % (datetime.now().isoformat(), msgtype))

    def reserve_tickets(self, wait_seconds=1, screencapture_failed=False, max_attempts=None, **kwargs):

        """Repeatedly tries to sign up for tickets. If successful, it takes a 
        screenshot, closes the browser and halts."""

        self.attempts = 0
        self.finished = False
        while not self.finished and (not max_attempts or self.attempts < max_attempts):
            self.finished = self.sign_up(**kwargs)
            self.attempts += 1
            if self.finished:
                sleep(1)
                self.take_screenshot()
            else:
                if screencapture_failed:
                    self.take_screenshot('FAILED')
                sleep(wait_seconds)
        self.close()

    def close(self):

        """Closes the bot for business. This quits the browser session."""

        driver = self.driver
        driver.quit()

    def run(self, cfg):

        """Runs the bot with the specified config."""

        user_info = cfg.get_user_info()
        config_options = cfg.get_config_options()
        self.reserve_tickets(info=user_info, **config_options)


if __name__ == '__main__':
    TicketBot().run(Config('config.ini'))