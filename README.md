# pingdom-twilio-alert

Get a call via Twilio when one of your Pingdom-monitored services is down for
longer than a specified amount of time.

Get a call again if the service stays down.

Systemd software watchdog is supported.


## Configuration

Copy config.ini.sample to config.ini.  Configuration should be fairly
self-evident.

alert_after and alert_again_after are in minutes.

For testing you might want to set the alert_after setting to 0, and add a
Pingdom check that is always down.  When you run the monitor, you should get a
call immediately.


## Execution

Use make to prepare the python venv.

    make

Then you should be able to run the alerted as follows:

    venv/bin/python bin/alert


## Run as systemd unit

Install, enable the systemd unit:

    sudo cp pingdom-twilio-alert.service /etc/systemd/system
    sudo systemctl enable pingdom-twilio-alert
    sudo systemctl start pingdom-twilio-alert
