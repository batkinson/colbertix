import re
from unittest import TestCase
from colbertix import Config, TicketBot, COLBERT_REPORT_URL, DAILY_SHOW_URL
from datetime import datetime
from ConfigParser import NoSectionError, NoOptionError
from mock import Mock, patch
from selenium.webdriver import Remote

SAMPLE_USER_INFO = {'first_name': 'John',
                    'last_name': 'Doe',
                    'zip': '10003',
                    'state': 'NY',
                    'daytime_phone': '6165551212',
                    'evening_phone': '6165551212',
                    'mobile_phone': '6165551212',
                    'email': 'someone@example.com'}

SAMPLE_CONFIG_OPTIONS = {'url': COLBERT_REPORT_URL,
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

class ConfigTest(TestCase):

    def setUp(self):
        self.cfg = Config('config.ini-example')

    def test_example_user_info(self):
        user_info = self.cfg.get_user_info()
        self.assertEqual(SAMPLE_USER_INFO, user_info)

    def test_example_config_options(self):
        config_options = self.cfg.get_config_options()
        self.assertEqual(SAMPLE_CONFIG_OPTIONS, config_options)

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


class ScreenshotMatcher(object):

    def __init__(self, pattern):
        self.pattern = re.compile(pattern)

    def __eq__(self, other):
        return self.pattern.search(other)


class TicketBotTest(TestCase):

    def setUp(self):
        self.mock_driver = Mock(spec=Remote)
        self.bot = TicketBot(self.mock_driver)

    def test_browse_to(self):
        expected_url = 'http://www.example.com/'
        self.bot.browse_to(expected_url)
        self.mock_driver.get.assert_called_with(expected_url)

    def test_close(self):
        self.bot.close()
        self.mock_driver.quit.assert_called()

    def test_take_screenshot_success(self):
        self.bot.take_screenshot()
        match_success = ScreenshotMatcher('-SUCCESS.png$')
        self.mock_driver.get_screenshot_as_file.assert_called_with(match_success)

    def test_take_screenshot_failure(self):
        self.bot.take_screenshot('FAILURE')
        match_failure = ScreenshotMatcher('-FAILURE.png$')
        self.mock_driver.get_screenshot_as_file.assert_called_with(match_failure)

    def test_reserve_tickets_success(self):
        options = dict(SAMPLE_CONFIG_OPTIONS)
        options['wait_seconds'] = 10  # Should never be used
        with patch('colbertix.sleep') as mock_sleep:
            self.bot.sign_up = Mock(return_value=True)
            self.bot.take_screenshot = Mock()
            self.bot.close = Mock()
            self.bot.reserve_tickets(**options)
            self.bot.sign_up.assert_called()
            self.bot.take_screenshot.assert_called()
            self.bot.close.assert_called()
            mock_sleep.assert_called_with(1)

    def test_reserve_tickets_max_attempts(self):
        with patch('colbertix.sleep') as mock_sleep:
            self.bot.sign_up = Mock(return_value=False)
            self.bot.take_screenshot = Mock()
            self.bot.close = Mock()
            self.bot.reserve_tickets(max_attempts=1, **SAMPLE_CONFIG_OPTIONS)
            self.bot.sign_up.assert_called()
            self.bot.take_screenshot.assert_called()
            self.bot.close.assert_called()
            mock_sleep.assert_called_with(SAMPLE_CONFIG_OPTIONS['wait_seconds'])
            self.assertEqual(1, self.bot.attempts)

    def test_reserve_tickets_failed(self):
        with patch('colbertix.sleep') as mock_sleep:
            self.bot.sign_up = Mock(return_value=False)
            self.bot.close = Mock()
            self.bot.reserve_tickets(max_attempts=1, **SAMPLE_CONFIG_OPTIONS)
            self.bot.sign_up.assert_called()
            self.bot.close.assert_called()
            mock_sleep.assert_called_with(SAMPLE_CONFIG_OPTIONS['wait_seconds'])
            self.assertEqual(1, self.bot.attempts)

    def test_reserve_tickets_failed_with_screenshot(self):
        with patch('colbertix.sleep') as mock_sleep:
            self.bot.sign_up = Mock(return_value=False)
            self.bot.take_screenshot = Mock()
            self.bot.close = Mock()
            self.bot.reserve_tickets(max_attempts=1, screencapture_failed=True, **SAMPLE_CONFIG_OPTIONS)
            self.bot.sign_up.assert_called()
            self.bot.take_screenshot.assert_called_once_with('FAILED')
            self.bot.close.assert_called()
            mock_sleep.assert_called_with(SAMPLE_CONFIG_OPTIONS['wait_seconds'])
            self.assertEqual(1, self.bot.attempts)
