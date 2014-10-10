#!/usr/bin/env python

from time import sleep
from ConfigParser import ConfigParser
from warnings import warn
from datetime import datetime, timedelta
from browser import Browser, Page


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


def format_date(d):
    """Formats a date for human consumption."""
    return d.strftime('%m/%d/%Y')


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
        self.user_info_keys = ['first_name', 'last_name', 'zip', 'country', 'state', 'daytime_phone',
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
        return dict((key, self.get('user-info', key)) for key in self.user_info_keys)

    def get_config_options(self):
        """Returns a dict containing program configuration options."""
        result = dict()
        gets = [self.get, self.get_int, self.get_date, self.get_dates]
        cfgs = [self.str_config_options, self.int_config_options, self.date_config_options, self.dates_config_options]
        for get, cfg in zip(gets, cfgs):
            result.update(dict((key, get('config', key)) for key in cfg))
        return result


class TicketBot(object):
    """A bot that can poll the Colbert Report web site and sign up for tickets.

        Usage:

        from colbertix import TicketBot, Config

        TicketBot().run(Config('config.ini'))
    """

    def __init__(self, browser, page, cfg):
        """Initializer for the bot. It will start the web browser and wait for commands."""
        self.attempts = None
        self.finished = None
        self.browser = browser
        self.page = page
        for key, value in cfg.get_config_options().items():
            setattr(self, key, value)
        self.info = cfg.get_user_info()

    def event_ok(self, event):
        """Returns whether the specified event is acceptable for signing up."""
        if event['tickets'] < self.wanted_tickets:
            return False
        event_date = event['date']
        if (self.start_date and event_date < self.start_date) \
                or (self.end_date and event_date > self.end_date) \
                or (self.bad_dates and event_date in self.bad_dates):
            return False
        return True

    def log_attempt(self, event):
        """Outputs a message indicating what the bot is attempting to register for."""
        print "Attempting to register for %s tickets on %s" % (self.wanted_tickets, Page.format_date(event['date']))

    def log_candidates(self, events, msg="Found %s candidates:"):
        """Outputs a message indicating that candidate events were found."""
        if isinstance(events, dict):
            events = [events]
        print msg % len(events)
        for event in events:
            print "    %s, tickets %s" % (format_date(event['date']), event['tickets'])

    def reserve_tickets(self, screencapture_failed=False, max_attempts=None):
        """Repeatedly attempt to register for tickets, closes the browser and halts on success."""
        self.attempts = 0
        self.finished = False
        while not self.finished and (not max_attempts or self.attempts < max_attempts):
            self.page.go()
            self.finished = self.sign_up()
            self.attempts += 1
            if self.finished:
                sleep(1)
                self.browser.screenshot()
            else:
                if screencapture_failed:
                    self.browser.screenshot('FAILED')
                sleep(self.wait_seconds)
        self.browser.close()

    def sign_up(self):
        """Attempts to sign up for available tickets. Returns True if success, False otherwise."""

        try:
            try:
                event = self.page.current_event()
                self.log_candidates(event)
            except:
                raise Exception('event not found')
            if self.event_ok(event):
                self.log_attempt(event)
                self.page.register_form(self.wanted_tickets, self.info)
                return True
            else:
                try:
                    other_events = self.page.inactive_events()
                    if other_events:
                        self.log_candidates(other_events, msg="Found %s additional candidates")
                except:
                    raise Exception('no selectable events not found')
                acceptable_events = filter(self.event_ok, other_events)
                if acceptable_events:
                    event = acceptable_events[0]  # Just attempt to register for the first valid event
                    self.log_attempt(event)
                    self.page.select_event(event)
                    self.page.register_form(self.wanted_tickets, self.info)
                    return True
                else:
                    raise Exception('no acceptable events found')
        except Exception as e:
            print "Failed to sign up: " + e.message
        return False

    @staticmethod
    def run(cfg):
        """Creates and runs a bot with the specified config."""
        options = cfg.get_config_options()
        url = options.pop('url')
        browser = Browser()
        bot = TicketBot(browser, Page(browser, url), cfg)
        bot.reserve_tickets()


if __name__ == '__main__':
    TicketBot.run(Config('config.ini'))
