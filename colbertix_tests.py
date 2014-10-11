import re
from unittest import TestCase
from colbertix import Config, TicketBot, COLBERT_REPORT_URL, DAILY_SHOW_URL
from browser import Browser, Page
from datetime import datetime, timedelta
from ConfigParser import NoSectionError, NoOptionError
from mock import Mock, patch


SAMPLE_USER_INFO = {'first_name': 'John',
                    'last_name': 'Doe',
                    'zip': '10003',
                    'state': 'NY',
                    'country': 'US',
                    'daytime_phone': '6165551212',
                    'evening_phone': '6165551212',
                    'mobile_phone': '6165551212',
                    'email': 'someone@example.com'}

START_DATE = datetime(2014, 8, 8)
END_DATE = datetime(2014, 10, 15)
CFG_BAD_DATES = [datetime(2014, 10, 2),
                 datetime(2014, 8, 23),
                 datetime(2014, 8, 24),
                 datetime(2014, 8, 25),
                 datetime(2014, 8, 30),
                 datetime(2014, 8, 31),
                 datetime(2014, 9, 1)]

SAMPLE_CONFIG_OPTIONS = {'url': COLBERT_REPORT_URL,
                         'wanted_tickets': 2,
                         'wait_seconds': 1,
                         'start_date': START_DATE,
                         'end_date': END_DATE,
                         'bad_dates': CFG_BAD_DATES}


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


WANTED_TICKETS = SAMPLE_CONFIG_OPTIONS['wanted_tickets']
GOOD_DATES = [START_DATE, END_DATE, END_DATE - timedelta(days=1)]
BAD_DATES = CFG_BAD_DATES + [START_DATE - timedelta(days=1), END_DATE + timedelta(days=1)]
GOOD_EVENTS = [dict(date=date, tickets=WANTED_TICKETS) for date in GOOD_DATES]
BAD_EVENTS = [dict(date=date, tickets=WANTED_TICKETS-1) for date in GOOD_DATES] \
             + [dict(date=date, tickets=WANTED_TICKETS) for date in BAD_DATES]


class TypeMatcher(object):

    def __init__(self, typ):
        self.type = typ

    def __eq__(self, other):
        return isinstance(other, self.type)


class TicketBotTest(TestCase):

    def setUp(self):
        self.brz = Mock(spec=Browser)
        self.pg = Mock(spec=Page)
        self.cfg = Config('config.ini-example')
        self.bot = TicketBot(self.brz, self.pg, self.cfg)

    def test_init_sets_config_options(self):
        for key, val in self.cfg.get_config_options().items():
            self.assertEqual(val, getattr(self.bot, key))

    def test_init_sets_user_info(self):
        self.assertEqual(self.cfg.get_user_info(), self.bot.info)

    def test_event_ok(self):
        for event in GOOD_EVENTS:
            self.assertTrue(self.bot.event_ok(event))
        for event in BAD_EVENTS:
            self.assertFalse(self.bot.event_ok(event))

    def test_reserve_tickets_success(self):
        with patch('colbertix.sleep') as m_sleep, patch.object(TicketBot, 'sign_up', autospec=True) as m_sign_up:
            m_bot = TicketBot(self.brz, self.pg, self.cfg)
            m_sign_up.return_value = True

            m_bot.reserve_tickets()  # Code under test

            self.pg.go.assert_called_once_with()
            m_sign_up.assert_called_once_with(m_bot)
            m_sleep.assert_called_once_with(SAMPLE_CONFIG_OPTIONS['wait_seconds'])
            self.brz.screenshot.assert_called_once_with()
            self.brz.close.assert_called_once_with()
            self.assertTrue(m_bot.finished)
            self.assertEqual(1, m_bot.attempts)

    def test_reserve_tickets_failures(self):
        with patch('colbertix.sleep') as m_sleep, patch.object(TicketBot, 'sign_up', autospec=True) as m_sign_up:
            m_bot = TicketBot(self.brz, self.pg, self.cfg)
            attempts = 1
            m_sign_up.return_value = False

            m_bot.reserve_tickets(max_attempts=attempts)  # Code under test

            self.pg.go.assert_called_once_with()
            m_sign_up.assert_called_once_with(m_bot)
            m_sleep.assert_called_once_with(SAMPLE_CONFIG_OPTIONS['wait_seconds'])
            self.brz.close.assert_called_once_with()
            self.assertFalse(m_bot.finished)
            self.assertEqual(attempts, m_bot.attempts)

    def test_reserve_tickets_failures_with_capture(self):
        with patch('colbertix.sleep') as m_sleep, patch.object(TicketBot, 'sign_up', autospec=True) as m_sign_up:
            m_bot = TicketBot(self.brz, self.pg, self.cfg)
            attempts = 1
            m_sign_up.return_value = False

            m_bot.reserve_tickets(max_attempts=attempts, screencapture_failed=True)  # Code under test

            self.pg.go.assert_called_once_with()
            m_sign_up.assert_called_once_with(m_bot)
            m_sleep.assert_called_once_with(SAMPLE_CONFIG_OPTIONS['wait_seconds'])
            self.brz.close.assert_called_once_with()
            self.assertFalse(m_bot.finished)
            self.assertEqual(attempts, m_bot.attempts)

    def test_sign_up_current_ok(self):
        self.pg.current_event.return_value = GOOD_EVENTS[0]
        result = self.bot.sign_up()
        self.assertTrue(result)
        self.pg.register_form.assert_called_once_with(WANTED_TICKETS, SAMPLE_USER_INFO)

    def test_sign_up_other_ok(self):
        self.pg.current_event.return_value = BAD_EVENTS[0]
        self.pg.inactive_events.return_value = GOOD_EVENTS
        result = self.bot.sign_up()
        self.assertTrue(result)
        self.pg.select_event.assert_called_once_with(GOOD_EVENTS[0])
        self.pg.register_form.assert_called_once_with(WANTED_TICKETS, SAMPLE_USER_INFO)

    def test_sign_up_current_bad_no_others(self):
        self.pg.current_event.return_value = BAD_EVENTS[0]
        self.pg.inactive_events.return_value = []
        result = self.bot.sign_up()
        self.assertFalse(result)

    def test_sign_up_all_bad(self):
        self.pg.current_event.return_value = BAD_EVENTS[0]
        self.pg.inactive_events.return_value = BAD_EVENTS
        result = self.bot.sign_up()
        self.assertFalse(result)
        self.assertFalse(self.pg.register_form.called)

    def test_sign_up_current_raises(self):
        self.pg.current_event.side_effect = Exception
        result = self.bot.sign_up()
        self.assertFalse(result)
        self.assertFalse(self.pg.register_form.called)

    def test_sign_up_inactive_events_raises(self):
        self.pg.current_event.return_value = BAD_EVENTS[0]
        self.pg.inactive_events.side_effect = Exception
        result = self.bot.sign_up()
        self.assertFalse(result)
        self.assertFalse(self.pg.register_form.called)

    def test_sign_up_select_event_raises(self):
        self.pg.current_event.return_value = BAD_EVENTS[0]
        self.pg.inactive_events.return_value = GOOD_EVENTS
        self.pg.select_event.side_effect = Exception
        result = self.bot.sign_up()
        self.assertFalse(result)
        self.assertFalse(self.pg.register_form.called)

    def test_run(self):
        with patch('colbertix.Browser') as m_brz, patch('colbertix.TicketBot') as m_bot:
            m_bot.return_value = m_bot
            TicketBot.run(Config('config.ini-example'))
            m_bot.assert_called_with_any(TypeMatcher(Browser), TypeMatcher(Page), TypeMatcher(Config))
            m_brz.assert_called_with()
            m_bot.reserve_tickets.assert_called_with()


