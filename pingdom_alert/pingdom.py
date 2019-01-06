import json
from urllib.request import urlopen, Request
from base64 import b64encode


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
            return json.loads(data.decode('utf-8'))


def b64encode_string(s):
    return b64encode(s.encode('utf-8')).decode('utf-8')
