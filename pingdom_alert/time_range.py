import re

import pytz
import dateutil.parser


class TimeRange:

    def __init__(self, time_str, timezone_str):
        time_pattern = r'\s*([01]?[0-9]|2[0-3]):([0-5][0-9])\s*'
        match = re.match(time_pattern + '-' + time_pattern, time_str)
        if not match:
            raise ValueError("Unparsable time range: %s" % time_str)
        self.start_time = (int(match.group(1)), int(match.group(2)))
        self.end_time = (int(match.group(3)), int(match.group(4)))
        self.timezone = pytz.timezone(timezone_str)

    def includes(self, time):
        localtime = time.astimezone(self.timezone)
        t = (localtime.hour, localtime.minute)
        if self.start_time <= self.end_time:
            return self.start_time <= t <= self.end_time
        else:
            return self.start_time <= t or t <= self.end_time

    def excludes(self, time):
        return not self.includes(time)

    def __repr__(self):
        return '<TimeRange %02d:%02d - %02d:%02d %s>' % (
            self.start_time + self.end_time + (self.timezone,))


class TestTimeRange:

    def test_time_range(self):
        EET = 'Europe/Sofia'
        dt = dateutil.parser.parse

        values = (

            (EET, '00:00 - 23:59', dt('00:00 EET'), True),
            (EET, '00:00 - 23:59', dt('12:00 EET'), True),
            (EET, '00:00 - 23:59', dt('23:59 EET'), True),

            (EET, '00:00 - 09:00', dt('23:59 EET'), False),
            (EET, '00:00 - 09:00', dt('00:00 EET'), True),
            (EET, '00:00 - 09:00', dt('09:00 EET'), True),
            (EET, '00:00 - 09:00', dt('09:01 EET'), False),

            (EET, '22:00 - 04:00', dt('21:59 EET'), False),
            (EET, '22:00 - 04:00', dt('22:00 EET'), True),
            (EET, '22:00 - 04:00', dt('03:00 EET'), True),
            (EET, '22:00 - 04:00', dt('04:00 EET'), True),
            (EET, '22:00 - 04:00', dt('04:01 EET'), False),

            (EET, '21:00 - 21:00', dt('20:59 EET'), False),
            (EET, '21:00 - 21:00', dt('21:00 EET'), True),
            (EET, '21:00 - 21:00', dt('21:01 EET'), False),

            (EET, '21:00 - 21:30', dt('2019-01-01 18:59 UTC'), False),
            (EET, '21:00 - 21:30', dt('2019-01-01 19:00 UTC'), True),
            (EET, '21:00 - 21:30', dt('2019-01-01 19:30 UTC'), True),
            (EET, '21:00 - 21:30', dt('2019-01-01 19:31 UTC'), False),

        )

        for timezone_str, time_str, test_time, should_include in values:
            time_range = TimeRange(time_str, timezone_str)
            assert time_range.includes(test_time) == should_include
