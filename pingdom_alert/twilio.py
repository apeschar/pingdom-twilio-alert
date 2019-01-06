from urllib.parse import urlencode, parse_qsl

from twilio.twiml.voice_response import VoiceResponse


class TwilioNotifier:

    def __init__(self, twilio_client, *, call_from, call_to):
        self.twilio = twilio_client
        self.call_from = call_from
        self.call_to = call_to

    def notify(self, message):
        twiml = VoiceResponse()
        twiml.say(message, language='en-AU', loop=10)
        self.twilio.calls.create(
            url=self._echo_twiml(twiml),
            from_=self.call_from,
            to=self.call_to,
        )

    def _echo_twiml(self, twiml):
        return 'https://twimlets.com/echo?' + urlencode({'Twiml': str(twiml)})


class TestTwilioNotifier:

    def test_notify(self):
        class mock_client:
            class calls:
                def create(*, url, from_, to):
                    assert from_ == '+1234'
                    assert to == '+5678'
                    base, query = url.split('?')
                    assert base == 'https://twimlets.com/echo'
                    params = parse_qsl(query)
                    assert len(params) == 1
                    k, v = params[0]
                    assert k == 'Twiml'
                    assert "Hello, World!" in v

        notifier = TwilioNotifier(mock_client, call_from='+1234', call_to='+5678')
        notifier.notify("Hello, World!")
