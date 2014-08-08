from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from time import sleep


class TicketBot(object):

    """A bot that can poll the Colbert Report web site and sign up for tickets.

       Usage:

       from colbertix import TicketBot
       from datetime import datetime

       info = dict(first_name='John',
                   last_name='Doe',
                   zip='10003',
                   state='NY',
                   daytime_phone='6165551212',
                   evening_phone='6165551212',
                   mobile_phone='6165551212',
                   email='example@example.com')

       start = datetime(2014, 8, 1)
       end = datetime(2014, 8, 31)
       blackouts = [ datetime(2014, 8, 24) ]

       tixbot = TicketBot()
       tixbot.reserve_tickets(wanted_tickets=2, info=info, start_date=start,
                              end_date=end, bad_dates=blackouts)
    """

    def __init__(self):
        """Initializer for the bot. It will start the web browser and wait for commands."""
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(1)
        self.driver.maximize_window()
        self.base_url = "http://impresario.comedycentral.com/show/5b2eb3b0eb99f143"
        self.accept_next_alert = True


    def visit_site(self):
        """Requests the ticket website. This will refresh the page as well."""
        self.driver.get(self.base_url)


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
            return (datestr, datetime.strptime(datestr, "%B %d, %Y"))
        except NoSuchElementException:
            return (None, None)


    def register_form(self, wanted_tickets, info):
        """Fills out the registration form on the current page."""
        d = self.driver

        if wanted_tickets == 1:
            ticket_sel = "1 ticket"
        else:
            ticket_sel = "%s tickets" % (wanted_tickets)

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


    def sign_up(self, info=None, wanted_tickets=2, start_date=None, end_date=None, bad_dates=None):

        """Runs a single attempt to sign up for tickets. 
           Returns True if successful, otherwise False."""

        self.visit_site()

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
        if (start_date and ticket_date < start_date) or \
            (end_date and ticket_date > end_date) or \
            (bad_dates and ticket_date in bad_dates):
            print "%s tickets are available for %s, but it's bad date for you." % (num_tickets, ticket_datestr)
            return False

        print "Attempting to register for %s tickets on %s" % (wanted_tickets, ticket_datestr)
        self.register_form(wanted_tickets, info)

        return True


    def take_screenshot(self, msgtype="SUCCESS"):

        """Takes picture of the web browser screen."""

        self.driver.get_screenshot_as_file("tickets-%s-%s.png" % (datetime.now().isoformat(), msgtype))


    def reserve_tickets(self, wait_seconds=1, screencapture_failed=False, **kwargs):

        """Repeatedly tries to sign up for tickets. If successful, it takes a 
        screenshot, closes the browser and halts."""

        while not self.sign_up(**kwargs):
            if screencapture_failed:
                self.take_screenshot('FAILED')
            sleep(wait_seconds)
        sleep(wait_seconds)
        self.take_screenshot()
        self.close()


    def close(self):

        """Closes the bot for business. This quits the browser session."""

        driver = self.driver
        driver.quit()
