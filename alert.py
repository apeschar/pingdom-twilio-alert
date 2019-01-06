#!/usr/bin/env python3

import datetime
import json
import logging
import time
from urllib.request import urlopen, Request
from base64 import b64encode


class Monitor:
    INTERVAL = 60
    ALERT_AFTER = datetime.timedelta(minutes=15)
    ALERT_AGAIN_AFTER = datetime.timedelta(minutes=60)

    def __init__(self, pingdom, notifier, *, clock=datetime.datetime.now):
        self.pingdom = pingdom
        self.notifier = notifier
        self.clock = clock
        self.logger = logging.getLogger(__name__)
        self.down_since = {}
        self.alerted_at = {}

    def run_forever(self):
        while True:
            try:
                self.tick()
            except Exception:
                self.logger.exception("Ignoring exception")
            time.sleep(self.INTERVAL)

    def tick(self):
        checks = self.pingdom.get_checks()

        down_check_ids = set(c['id'] for c in checks if c['status'] == 'down')

        for k in set(self.down_since.keys()) - down_check_ids:
            del self.down_since[k]
        for k in down_check_ids - set(self.down_since.keys()):
            self.down_since[k] = self.clock()

        alert_before = self.clock() - self.ALERT_AFTER
        alert_again_before = self.clock() - self.ALERT_AGAIN_AFTER

        messages = []
        alerted = set()

        for check_id, since in self.down_since.items():
            if since > alert_before:
                continue
            if check_id in self.alerted_at and \
               self.alerted_at[check_id] > alert_again_before:
                continue
            check = next(c for c in checks if c['id'] == check_id)
            messages.append("Check %s is down since %s." % (
                check['name'],
                since.astimezone(datetime.timezone.utc)
                    .strftime('%Y-%m-%d %H:%M:%S UTC')
            ))
            alerted.add(check_id)

        if messages:
            self.notifier.notify(" ".join(messages))

        for check_id in alerted:
            self.alerted_at[check_id] = self.clock()


class TestMonitor:

    def test_monitor(self):

        class MockPingdom:

            def get_checks(self):
                return [
                    {
                        'id': 1,
                        'status': 'down',
                        'name': 'Test 1',
                    }
                ]

        class MockNotifier:

            def __init__(self):
                self.notifications = []

            def notify(self, message):
                self.notifications.append(message)

        now = datetime.datetime(2019, 1, 1)

        pingdom = MockPingdom()
        notifier = MockNotifier()

        monitor = Monitor(pingdom, notifier, clock=lambda: now)
        monitor.tick()

        def tick_and_expect_notifications(n, minutes=10):
            nonlocal now
            now += datetime.timedelta(minutes=minutes)
            monitor.tick()
            assert len(notifier.notifications) == n
            notifier.notifications = []

        tick_and_expect_notifications(0)
        tick_and_expect_notifications(1)
        tick_and_expect_notifications(0)
        tick_and_expect_notifications(1, minutes=60)
        tick_and_expect_notifications(0)


class Pingdom:
    BASE_URL = 'https://api.pingdom.com/'

    def __init__(self, app_key, username, password):
        self.app_key = app_key
        self.username = username
        self.password = password

    def get_checks(self):
        return self.get('checks')['checks']

    def get(self, path):
        url = self.BASE_URL + 'api/2.1/' + path
        credentials = '%s:%s' % (self.username, self.password)
        request = Request(url, headers={
            'Authorization': 'Basic %s' % b64encode_string(credentials),
            'App-Key': self.app_key,
        })
        with urlopen(request) as f:
            data = f.read()
            return json.loads(data)


def b64encode_string(s):
    return b64encode(s.encode('utf-8')).decode('utf-8')


if __name__ == '__main__':
    main()
