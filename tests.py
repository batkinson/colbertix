import re
from unittest import TestCase
from colbertix import Config, TicketBot, COLBERT_REPORT_URL, DAILY_SHOW_URL
from datetime import datetime
from ConfigParser import NoSectionError, NoOptionError
from mock import Mock, patch
from selenium.webdriver import Remote, Chrome


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


class TypeMatcher(object):

    def __init__(self, typ):
        self.type = typ

    def __eq__(self, other):
        return isinstance(other, self.type)


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

    def test_sign_up_simple(self):
        options = dict(SAMPLE_CONFIG_OPTIONS)
        del options['wait_seconds']
        self.bot.browse_to = Mock()
        self.bot.get_num_tickets = Mock(return_value=4)
        self.bot.get_ticket_date = Mock(return_value=('2014/08/09', datetime(2014, 8, 9)))
        self.bot.register_form = Mock()
        self.assertTrue(self.bot.sign_up(info=SAMPLE_USER_INFO, **options), 'Successful should return true')
        self.bot.browse_to.assert_called_once_with(options['url'])
        self.bot.get_num_tickets.assert_called()
        self.bot.get_ticket_date.assert_called()
        self.bot.register_form.assert_called_once_with(options['wanted_tickets'], SAMPLE_USER_INFO)

    def test_sign_up_bad_date(self):
        options = dict(SAMPLE_CONFIG_OPTIONS)
        del options['wait_seconds']
        self.bot.browse_to = Mock()
        self.bot.get_num_tickets = Mock(return_value=4)
        self.bot.get_ticket_date = Mock(return_value=('2014/08/23', datetime(2014, 8, 23)))
        self.bot.register_form = Mock()
        self.assertFalse(self.bot.sign_up(info=SAMPLE_USER_INFO, **options), 'Bad dates should return false')
        self.bot.browse_to.assert_called_once_with(options['url'])
        self.bot.get_num_tickets.assert_called()
        self.bot.get_ticket_date.assert_called()

    def test_sign_up_before_start_date(self):
        options = dict(SAMPLE_CONFIG_OPTIONS)
        del options['wait_seconds']
        self.bot.browse_to = Mock()
        self.bot.get_num_tickets = Mock(return_value=4)
        self.bot.get_ticket_date = Mock(return_value=('2014/07/23', datetime(2014, 7, 23)))
        self.bot.register_form = Mock()
        self.assertFalse(self.bot.sign_up(info=SAMPLE_USER_INFO, **options), 'Bad dates should return false')
        self.bot.browse_to.assert_called_once_with(options['url'])
        self.bot.get_num_tickets.assert_called()
        self.bot.get_ticket_date.assert_called()

    def test_sign_up_after_end_date(self):
        options = dict(SAMPLE_CONFIG_OPTIONS)
        del options['wait_seconds']
        self.bot.browse_to = Mock()
        self.bot.get_num_tickets = Mock(return_value=4)
        self.bot.get_ticket_date = Mock(return_value=('2015/08/23', datetime(2015, 8, 23)))
        self.bot.register_form = Mock()
        self.assertFalse(self.bot.sign_up(info=SAMPLE_USER_INFO, **options), 'Bad dates should return false')
        self.bot.browse_to.assert_called_once_with(options['url'])
        self.bot.get_num_tickets.assert_called()
        self.bot.get_ticket_date.assert_called()

    def test_sign_up_no_start_date(self):
        options = dict(SAMPLE_CONFIG_OPTIONS)
        del options['wait_seconds']
        del options['start_date']
        self.bot.browse_to = Mock()
        self.bot.get_num_tickets = Mock(return_value=4)
        self.bot.get_ticket_date = Mock(return_value=('2014/08/23', datetime(2014, 8, 9)))
        self.bot.register_form = Mock()
        self.assertTrue(self.bot.sign_up(info=SAMPLE_USER_INFO, **options), 'No start date should return true')
        self.bot.browse_to.assert_called_once_with(options['url'])
        self.bot.get_num_tickets.assert_called()
        self.bot.get_ticket_date.assert_called()

    def test_sign_up_no_end_date(self):
        options = dict(SAMPLE_CONFIG_OPTIONS)
        del options['wait_seconds']
        del options['end_date']
        self.bot.browse_to = Mock()
        self.bot.get_num_tickets = Mock(return_value=4)
        self.bot.get_ticket_date = Mock(return_value=('2015/08/23', datetime(2015, 8, 23)))
        self.bot.register_form = Mock()
        self.assertTrue(self.bot.sign_up(info=SAMPLE_USER_INFO, **options), 'No start date should return true')
        self.bot.browse_to.assert_called_once_with(options['url'])
        self.bot.get_num_tickets.assert_called()
        self.bot.get_ticket_date.assert_called()

    def test_sign_up_not_enough_tickets(self):
        options = dict(SAMPLE_CONFIG_OPTIONS)
        del options['wait_seconds']
        self.bot.browse_to = Mock()
        self.bot.get_num_tickets = Mock(return_value=1)
        self.bot.get_ticket_date = Mock(return_value=('2014/08/09', datetime(2014, 8, 9)))
        self.bot.register_form = Mock()
        self.assertFalse(self.bot.sign_up(info=SAMPLE_USER_INFO, **options), 'Not enough tickets should return false')
        self.bot.browse_to.assert_called_once_with(options['url'])
        self.bot.get_num_tickets.assert_called()
        self.bot.get_ticket_date.assert_called()

    def test_sign_up_undetermined_date(self):
        options = dict(SAMPLE_CONFIG_OPTIONS)
        del options['wait_seconds']
        self.bot.browse_to = Mock()
        self.bot.get_num_tickets = Mock(return_value=4)
        self.bot.get_ticket_date = Mock(return_value=(None, None))
        self.bot.register_form = Mock()
        self.assertFalse(self.bot.sign_up(info=SAMPLE_USER_INFO, **options), 'No date should return false')
        self.bot.browse_to.assert_called_once_with(options['url'])
        self.bot.get_num_tickets.assert_called()
        self.bot.get_ticket_date.assert_called()

    def test_run(self):
        cfg = Config('config.ini-example')
        self.bot.reserve_tickets = Mock()
        self.bot.run(cfg)
        self.bot.reserve_tickets.assert_called_once_with(info=SAMPLE_USER_INFO, **SAMPLE_CONFIG_OPTIONS)

    def test_driver_init(self):
        driver = Mock(spec=Remote)
        self.bot._driver_init(driver)
        driver.implicitly_wait.assert_called_once_with(1)
        driver.maximize_window.assert_called_once_with()
        self.assertEquals(driver, self.bot.driver)

    def test_default_init_creates_chrome(self):
        with patch('colbertix.webdriver.Chrome') as mock_chrome, \
                patch.object(TicketBot, '_driver_init', autospec=True) as mock_init:
            t = TicketBot()
            mock_chrome.assert_called()
            mock_init.assert_called_once_with(t, mock_chrome())

