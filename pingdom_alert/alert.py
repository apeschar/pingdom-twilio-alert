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

    monitor.run_forever()


if __name__ == '__main__':
    main()
