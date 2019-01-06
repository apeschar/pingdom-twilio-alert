import datetime
import logging
import time


class Monitor:

    def __init__(self, *, pingdom, notifier,
                 clock=lambda: datetime.datetime.now(datetime.timezone.utc),
                 alert_after=datetime.timedelta(minutes=15),
                 alert_again_after=datetime.timedelta(minutes=60)):

        self.pingdom = pingdom
        self.notifier = notifier
        self.clock = clock
        self.alert_after = alert_after
        self.alert_again_after = alert_again_after

        self.logger = logging.getLogger(__name__)
        self.down_since = {}
        self.alerted_at = {}

    def run_forever(self, *, interval=60, sdnotify=lambda message: None):
        self.logger.info("Start")
        sdnotify('READY=1')

        while True:
            try:
                self.tick()
            except Exception:
                self.logger.exception("Ignoring exception")
            else:
                sdnotify('WATCHDOG=1')
            time.sleep(interval)

    def tick(self):
        checks = self.pingdom.get_checks()

        self.down_since = dict((c['id'], self.down_since.get(c['id'], self.clock()))
                               for c in checks if c['status'] == 'down')

        self.logger.info("%d checks, %d down" % (len(checks), len(self.down_since)))

        for c in checks:
            if c['id'] in self.down_since:
                self.logger.info("%s: down since %s", c['name'],
                                 self.down_since[c['id']].strftime('%Y-%m-%d %H:%M:%S %Z'))

        messages = []
        alerted = set()

        for check_id, down_since in self.down_since.items():
            down_for = self.clock() - down_since
            if down_for < self.alert_after:
                continue
            if check_id in self.alerted_at and \
               self.clock() - self.alerted_at[check_id] < self.alert_again_after:
                continue
            check = next(c for c in checks if c['id'] == check_id)
            messages.append("Check %s is down since %s." % (
                check['name'],
                down_since.astimezone(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            ))
            alerted.add(check_id)

        if messages:
            joined_message = " ".join(messages)
            self.logger.info("Sending %d alerts: %s", len(messages), joined_message)
            self.notifier.notify(joined_message)

        for check_id in alerted:
            self.alerted_at[check_id] = self.clock()


class TestMonitor:

    def setup_method(self, method):

        class MockPingdom:

            def __init__(self):
                self.status = 'down'

            def get_checks(self):
                return [
                    {
                        'id': 1,
                        'status': self.status,
                        'name': 'Test 1',
                    }
                ]

        class MockNotifier:

            def __init__(self):
                self.notifications = []

            def notify(self, message):
                self.notifications.append(message)

            def get_notifications(self):
                try:
                    return self.notifications
                finally:
                    self.notifications = []

        self.now = datetime.datetime(2019, 1, 1, tzinfo=datetime.timezone.utc)

        self.pingdom = MockPingdom()
        self.notifier = MockNotifier()

        self.monitor = Monitor(pingdom=self.pingdom,
                               notifier=self.notifier,
                               clock=lambda: self.now)

    def test_monitor(self):
        self.expect_notification_after_minutes(16)
        self.expect_notification_after_minutes(60)
        self.expect_notification_after_minutes(60)

    def test_flap(self):
        self.monitor.tick()
        self.pingdom.status = 'up'
        self.expect_no_notifications_for_minutes(60)
        self.pingdom.status = 'down'
        self.expect_notification_after_minutes(16)
        self.expect_notification_after_minutes(60)

    def test_no_second_alert_after_flap(self):
        self.expect_notification_after_minutes(16)
        self.pingdom.status = 'up'
        self.expect_no_notifications_for_minutes(10)
        self.pingdom.status = 'down'
        self.expect_notification_after_minutes(50)
        self.expect_notification_after_minutes(60)

    def expect_notification_after_minutes(self, minutes):
        self.expect_no_notifications_for_minutes(minutes - 1)
        self.tick_and_expect_notifications(1, minutes=1)

    def expect_no_notifications_for_minutes(self, minutes):
        for _ in range(minutes):
            self.tick_and_expect_notifications(0, minutes=1)

    def tick_and_expect_notifications(self, n, minutes=10):
        self.now += datetime.timedelta(minutes=minutes)
        self.monitor.tick()
        assert len(self.notifier.get_notifications()) == n
