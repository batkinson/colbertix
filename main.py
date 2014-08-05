from datetime import datetime, timedelta
from colbertix import TicketBot
from ConfigParser import ConfigParser


def date_range(start, end, increment=1):
    """Generates a date range from start to end inclusive by increment days."""
    time_inc = timedelta(days=increment)
    current = start
    while current <= end:
        yield current
        current += time_inc


if __name__ == '__main__':

    # Load options from config ini file
    cfg = ConfigParser()
    cfg.read("config.ini")
    
    def str_to_date(datestr):
        return datetime.strptime(datestr,'%m/%d/%Y')
        
    def get_cfg_date(key):
        return str_to_date(cfg.get('config', key))
    
    def get_cfg_int(key):
        return cfg.getint('config', key)

    start_date = get_cfg_date('start_date')
    end_date = get_cfg_date('end_date')

    bad_date_strs = [ s.strip() for s in cfg.get('config', 'bad_dates').split(',') ]
    
    def cvt_bad_dates(bdstrs):
        result = []
        for bdstr in bdstrs:
            bd = bdstr.split('-')
            if len(bd) == 1:
                result.append(str_to_date(bd[0]))
            elif len(bd) == 2:
                start, end = [str_to_date(item) for item in bd]
                result += list(date_range(start, end))
        return result

    bad_dates = cvt_bad_dates(bad_date_strs)
    
    # Information for filling out registration form
    info_keys = [ 'first_name', 'last_name', 'zip', 'state', 'daytime_phone', 
                 'evening_phone', 'mobile_phone', 'email' ]
    info = {}
    for key in info_keys:
        info[key] = cfg.get('user-info', key)      

    # Search until we find tickets
    tixbot = TicketBot()
    tixbot.reserve_tickets(info=info,
                           start_date=start_date,
                           end_date=end_date,
                           bad_dates=bad_dates,
                           wait_seconds=get_cfg_int('wait_seconds'),
                           wanted_tickets=get_cfg_int('wanted_tickets'))
