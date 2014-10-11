from os.path import dirname, realpath
from unittest import TestCase
from browser import Browser, Page


class DateFormatTest(TestCase):

    def test_parse_and_format_date(self):
        date_strs = ['October 2, 2014', 'January 11, 1978']
        for date_str in date_strs:
            date = Page.parse_date(date_str)
            self.assertEqual(date_str, Page.format_date(date))


class BrowserTest(TestCase):

    LOCAL_URL = 'file://' + dirname(realpath(__file__)) + '/test_site/ticket-central.html'
    CURRENT_EVENT_DATE = 'September 30, 2014'
    CURRENT_EVENT_TIX = 12
    CURRENT_EVENT = dict(date=Page.parse_date(CURRENT_EVENT_DATE), tickets=CURRENT_EVENT_TIX)
    OTHER_EVENTS = [
        dict(date=Page.parse_date('October 2, 2014'), tickets=1),
        dict(date=Page.parse_date('October 6, 2014'), tickets=12)
    ]
    INFO = {
        'first_name': 'John',
        'last_name': 'Doe',
        'zip': '10003',
        'country': 'US',
        'state': 'NY',
        'daytime_phone': '5558675309',
        'evening_phone': '5558675309',
        'mobile_phone': '5558675309',
        'email': 'john.doe@example.com'
    }
    NON_US_INFO = dict(INFO)
    NON_US_INFO.update(dict(country='GB', zip='SW1A 1AA'))
    NON_US_INFO.pop('state')

    @classmethod
    def setUpClass(cls):
        cls.b = Browser()

    @classmethod
    def tearDownClass(cls):
        cls.b.close()

    def setUp(self):
        self.p = Page(self.b, self.LOCAL_URL)
        self.p.go()

    def test_bad_query_methods(self):
        with self.assertRaises(Exception):
            self.b.elem('should not matter',by='bad_method')
        with self.assertRaises(Exception):
            self.b.elems('should not matter',by='bad_method')

    def test_check_current_query(self):
        query = Page.CHECK_CURRENT_QUERY % (self.CURRENT_EVENT_DATE, self.CURRENT_EVENT_TIX)
        self.assertIsNotNone(self.b.elem(query, by='xpath'))

    def test_check_current(self):
        self.p.check_current(self.CURRENT_EVENT)

    def test_current_event(self):
        self.assertEqual(self.CURRENT_EVENT, self.p.current_event())

    def test_inactive_events(self):
        self.assertEqual(self.OTHER_EVENTS, self.p.inactive_events())

    def test_select_event_query(self):
        query = Page.SELECT_EVENT_QUERY % (self.CURRENT_EVENT_DATE, self.CURRENT_EVENT_TIX)
        elem = self.b.elem(query, by='xpath')
        self.assertIsNotNone(elem)
        self.assertEqual(self.CURRENT_EVENT, self.p.extract_event(elem))

    def test_select_event(self):
        self.p.select_event(self.CURRENT_EVENT)

    def test_register_form(self):
        self.p.register_form(2, self.INFO)
        self.p.wait_for_modal()
        self.assertTrue(self.p.verify_submission(self.CURRENT_EVENT, 2, self.INFO))

    def test_register_form_non_us(self):
        self.p.register_form(2, self.NON_US_INFO)
        self.p.wait_for_modal()
        self.assertTrue(self.p.verify_submission(self.CURRENT_EVENT, 2, self.NON_US_INFO))

    def test_screenshot(self):
        from os import remove
        from os.path import isfile
        f = self.b.screenshot()
        self.assertTrue(isfile(f))
        remove(f)
        f = self.b.screenshot('FAILED')
        self.assertTrue(isfile(f))
        remove(f)

    def test_click_and_register(self):
        event = self.OTHER_EVENTS[1]
        self.p.select_event(event)
        self.p.register_form(2, self.INFO)
        self.p.wait_for_modal()
        self.assertTrue(self.p.verify_submission(event, 2, self.INFO))
