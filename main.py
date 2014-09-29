#! /usr/bin/env python

from colbertix import Config, TicketBot

if __name__ == '__main__':

    cfg = Config('config.ini')
    user_info = cfg.get_user_info()
    config_options = cfg.get_config_options()

    ticket_bot = TicketBot()
    ticket_bot.reserve_tickets(info=user_info, **config_options)
