#!/usr/bin/env python3

import logging
from argparse import ArgumentParser
from configparser import ConfigParser
from datetime import timedelta

from twilio.rest import Client

from .monitor import Monitor
from .pingdom import Pingdom
from .twilio import TwilioNotifier


def main():
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(name)s %(levelname)s - %(message)s')

    logger = logging.getLogger(__name__)

    parser = ArgumentParser()
    parser.add_argument('--config', '-c', type=str, default='config.ini')
    args = parser.parse_args()

    config = ConfigParser()
    config.read(args.config)

    twilio = Client(config['twilio']['account'], config['twilio']['token'])

    notifier = TwilioNotifier(twilio,
                              call_from=config['notification']['from_number'],
                              call_to=config['notification']['to_number'])

    pingdom = Pingdom(config['pingdom']['app_key'],
                      config['pingdom']['user'],
                      config['pingdom']['password'])

    monitor = Monitor(pingdom=pingdom, notifier=notifier,
                      alert_after=timedelta(minutes=float(config['monitor']['alert_after'])),
                      alert_again_after=timedelta(minutes=float(config['monitor']['alert_again_after'])))

    try:
        from sdnotify import SystemdNotifier
        sdnotify = SystemdNotifier().notify
    except Exception as e:
        logger.info("Not using sdnotify: %s: %s", e.__class__.__name__, str(e))
        sdnotify = lambda message: None
    else:
        logger.info("Using sdnotify")

    monitor.run_forever(sdnotify=sdnotify)


if __name__ == '__main__':
    main()
