from unittest import TestCase
from colbertix import Config, COLBERT_REPORT_URL, DAILY_SHOW_URL
from datetime import datetime
from ConfigParser import NoSectionError, NoOptionError


class ConfigTest(TestCase):

    def setUp(self):
        self.cfg = Config('config.ini-example')

    def test_example_user_info(self):
        expected = {'first_name': 'John',
                    'last_name': 'Doe',
                    'zip': '10003',
                    'state': 'NY',
                    'daytime_phone': '6165551212',
                    'evening_phone': '6165551212',
                    'mobile_phone': '6165551212',
                    'email': 'someone@example.com'}
        user_info = self.cfg.get_user_info()
        self.assertEqual(expected, user_info)

    def test_example_config_options(self):
        expected = {'url': COLBERT_REPORT_URL,
                    'wanted_tickets': 2,
                    'wait_seconds': 1,
                    'start_date': datetime(2014, 8, 8),
                    'end_date': datetime(2014, 10, 15),
                    'bad_dates': [datetime(2014, 10, 2),
                                  datetime(2014, 8, 23),
                                  datetime(2014, 8, 24),
                                  datetime(2014, 8, 25),
                                  datetime(2014, 8, 30),
                                  datetime(2014, 8, 31),
                                  datetime(2014, 9, 1)]}
        config_options = self.cfg.get_config_options()
        self.assertEqual(expected, config_options)

    def test_missing_section(self):
        with self.assertRaises(NoSectionError):
            self.cfg.get('bad-section', 'first_name')

    def test_missing_option(self):
        with self.assertRaises(NoOptionError):
            self.cfg.get('user-info', 'bad-option')

    def test_empty_bad_dates(self):
        cfg = Config('test_configs/empty_bad_dates.ini')
        expected = []
        self.assertEqual(expected, cfg.get_dates('config', 'bad_dates'))

    def test_malformed_bad_dates(self):
        cfg = Config('test_configs/contains_bad_dates.ini')
        expected = []
        self.assertEqual(expected, cfg.get_dates('config', 'bad_dates'))

    def test_missing_bad_dates(self):
        cfg = Config('test_configs/missing_bad_dates.ini')
        with self.assertRaises(NoOptionError):
            cfg.get_dates('config', 'bad_dates')

    def test_alternative_url(self):
        cfg = Config('test_configs/daily_show_url.ini')
        self.assertEqual(DAILY_SHOW_URL, cfg.get_config_options()['url'])

    def test_comments(self):
        cfg = Config('test_configs/commented_url.ini')
        self.assertEqual(COLBERT_REPORT_URL, cfg.get_config_options()['url'])

