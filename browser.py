from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from json import dumps
from time import sleep


def create_driver():
    """Creates an returns webdriver instance."""
    drv = webdriver.Chrome()
    drv.implicitly_wait(1)
    drv.maximize_window()
    return drv


SINGLE_ELEM_QUERIES = {
    'id': 'find_element_by_id',
    'css': 'find_element_by_css_selector',
    'xpath': 'find_element_by_xpath'
}
SINGLE_ELEM_QUERY_TYPES = set(SINGLE_ELEM_QUERIES.keys())

MULTI_ELEM_QUERIES = {
    'id': 'find_elements_by_id',
    'css': 'find_elements_by_css_selector',
    'xpath': 'find_elements_by_xpath'
}
MULTI_ELEM_QUERY_TYPES = set(MULTI_ELEM_QUERIES.keys())


class Browser(object):

    def __init__(self):
        """Initializes the browser."""
        self.driver = create_driver()

    def go(self, url):
        """Navigates the browser to the specified URL."""
        self.driver.get(url)

    def elem(self, query, root=None, by='id'):
        """Finds a single element under the root element."""
        if not by in SINGLE_ELEM_QUERY_TYPES:
            raise Exception('invalid query type: %s' % by)
        if root is None:
            root = self.driver
        return getattr(root, SINGLE_ELEM_QUERIES[by])(query)

    def elems(self, query, root=None, by='css'):
        """Finds elements under the root element."""
        if not by in MULTI_ELEM_QUERY_TYPES:
            raise Exception('invalid query type: %s' % by)
        if root is None:
            root = self.driver
        return getattr(root, MULTI_ELEM_QUERIES[by])(query)

    def keys(self, data, *args, **kwargs):
        """Types the specified data into the queried elements."""
        for e in self.elems(*args, **kwargs):
            e.send_keys(data)

    def select(self, item_value, *args, **kwargs):
        """Selects the specified item in the queried elements selections."""
        for e in self.elems(*args, **kwargs):
            Select(e).select_by_value(item_value)

    def click(self, *args, **kwargs):
        """Clicks the queried elements."""
        for e in self.elems(*args, **kwargs):
            self.driver.execute_script('arguments[0].click();', e)

    def exec_js(self, script):
        return self.driver.execute_script(script)

    def screenshot(self, msgtype="SUCCESS"):
        """Takes picture of the web browser screen, returns filename."""
        file_name = "tickets-%s-%s.png" % (datetime.now().isoformat(), msgtype)
        self.driver.get_screenshot_as_file(file_name)
        return file_name

    def close(self):
        """Closes the browser."""
        self.driver.quit()


class Page(object):

    DATE_FORMAT = "%B %-d, %Y"
    DATE_PARSE_FORMAT = "%B %d, %Y"
    INACTIVE_EVENTS_QUERY = "//*[contains(@class,'event_list_item') and not(contains(@class,'selectedDay'))" \
                            " and ./div[contains(@class,'eventsCount')]]"
    SELECT_EVENT_QUERY = "//*[contains(@class,'event_list_item')" \
                         " and ./div[contains(@class, 'carEvent') and contains(text(),'%s')]" \
                         " and ./div[contains(@class,'eventsCount') and text()='%s']]"
    CHECK_CURRENT_QUERY = "//div[contains(@class,'form_header')" \
                          " and .//span[contains(@class,'current_date') and text()='%s']" \
                          " and ./*[contains(@class,'tickets_remaining') and ./span[text()='%s']]]"

    def __init__(self, browser, url):
        self.browser = browser
        self.url = url

    @staticmethod
    def format_date(dt):
        """Formats datetime object into page format."""
        return dt.strftime(Page.DATE_FORMAT)

    @staticmethod
    def parse_date(dtstr):
        """Parses date string into datetime object."""
        return datetime.strptime(dtstr, Page.DATE_PARSE_FORMAT)

    def go(self):
        """Navigate/refresh this page."""
        self.browser.go(self.url)

    def current_event(self):
        """Returns the current event for page as a dictionary. {date: (datetime), tickets: (int)}"""
        current_date = Page.parse_date(self.browser.elem('span.current_date', by='css').text)
        current_tickets = int(self.browser.elem('div.tickets_remaining > span', by='css').text)
        return {'date': current_date, 'tickets': current_tickets}

    def extract_event_tickets(self, elem):
        """Returns the ticket count for the specified event element."""
        return int(self.browser.elem('div.eventsCount', root=elem, by='css').text)

    def extract_event_date_text(self, elem):
        """Returns the date for the specified event element."""
        return self.browser.elem('div.carEvent', root=elem, by='css').text.split('\n')[1]

    def extract_event_date(self, elem):
        """Returns the date for the specified event element as a datetime object."""
        return Page.parse_date(self.extract_event_date_text(elem))

    def extract_event(self, elem):
        """Returns an event dict extracted from the specified element."""
        return {'date': self.extract_event_date(elem), 'tickets': self.extract_event_tickets(elem)}

    def inactive_events(self):
        """Returns a list of dictionaries for all inactive events."""
        elems = self.browser.elems(Page.INACTIVE_EVENTS_QUERY, by='xpath')
        return [self.extract_event(e) for e in elems]

    def select_event(self, event):
        """Selects the given event and waits for current event to be updated to it."""
        query = self.SELECT_EVENT_QUERY % (Page.format_date(event['date']), event['tickets'])
        self.browser.click(query, by='xpath')
        self.check_current(event)

    def check_current(self, event):
        """Checks that the form is displaying the specified event as the current one."""
        query = Page.CHECK_CURRENT_QUERY % (Page.format_date(event['date']), event['tickets'])
        self.browser.elem(query, by='xpath')

    def register_form(self, wanted_tickets, info, submit=True):
        """Fills out the registration form on the current page."""
        b = self.browser
        b.select(str(wanted_tickets), '#fld_tickets_number')
        b.keys(info['first_name'], '#fld_firstname')
        b.keys(info['last_name'], '#fld_lastname')
        b.keys(info['zip'], '#fld_zip')
        if b.elem('fld_state').is_displayed():
            b.select(info['state'], '#fld_state')
        b.select(info['country'], '#fld_country')
        b.keys(info['daytime_phone'], '#fld_phone_daytime')
        b.keys(info['evening_phone'], '#fld_phone_evening')
        b.keys(info['mobile_phone'], '#fld_phone_mobile')
        b.keys(info['email'], '#fld_email')
        b.keys(info['email'], '#fld_emailVerify')
        b.click('#fld_terms')
        if submit:
            b.click('#lnk_form_ticket_submit')

    def wait_for_modal(self):
        """Hack to wait for the modal wait message to be hidden.
           Explicit wait via an EC was not available in this version of selenium.
        """
        try:
            while True:
                self.browser.elem('div.blockUI.blockMsg.blockElement', by='css')
                sleep(.1)
        except NoSuchElementException:
            pass

    def verify_submission(self, event, tickets, info):
        """Only useful with the test page, confirms the submitted data matches the specified data."""
        verify_obj = {
            'event_date': self.format_date(event['date']),
            'tickets_number': tickets,
            'firstname': info['first_name'],
            'lastname':  info['last_name'],
            'zip': info['zip'],
            'country': info['country'],
            'state': info['state'],
            'phone_daytime': info['daytime_phone'],
            'phone_evening': info['evening_phone'],
            'phone_mobile': info['mobile_phone'],
            'email': info['email'],
            'emailVerify': info['email'],
            'terms': 'ON'
        }
        return self.browser.exec_js('return verifySubmit(%s)' % dumps(verify_obj))
