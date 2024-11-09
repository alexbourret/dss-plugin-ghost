import requests
import logging
import jwt
from datetime import datetime
from ghost_commons import get_api_token_from_config, get_id_and_secret


logging.basicConfig(level=logging.INFO, format='dss-plugin-ghost %(levelname)s - %(message)s')
logger = logging.getLogger()

FIVE_MINUTE = 5*60

class GhostAuth(requests.auth.AuthBase):
    def __init__(self, config):
        api_token = get_api_token_from_config(config)
        self.key_id, self.secret = get_id_and_secret(api_token)
        self.token = None

    def __call__(self, request):
        if not self.token:
            self.token = self._get_new_token()
        request.headers["Authorization"] = "Ghost {}".format(self.token)
        return request
    
    def _get_new_token(self):
        iat = int(datetime.now().timestamp())
        payload = {
            "iat": iat,
            "exp": iat + FIVE_MINUTE,
            "aud": "/admin/"
        }
        headers =  {
            "alg": "HS256",
            "typ": "JWT",
            "kid": self.key_id
        }
        token = jwt.encode(
            payload,
            bytes.fromhex(self.secret),
            algorithm="HS256",
            headers=headers
        )
        return token


'''
import requests # pip install requests
import jwt	# pip install pyjwt
from datetime import datetime as date

# Admin API key goes here
key = ''

# Split the key into ID and SECRET
id, secret = key.split(':')

# Prepare header and payload
iat = int(date.now().timestamp())

header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id}
payload = {
    'iat': iat,
    'exp': iat + 5 * 60,
    'aud': '/admin/'
}

# Create the token (including decoding secret)
token = jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers=header)

# Make an authenticated request to create a post
url = 'https://bla.com/ghost/api/admin/posts/'
headers = {'Authorization': 'Ghost {}'.format(token)}
body = {'posts': [{'title': 'Hello World'}]}
r = requests.post(url, json=body, headers=headers)
'''