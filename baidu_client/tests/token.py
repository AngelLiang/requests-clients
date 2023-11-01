import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())

env_path = os.path.join(os.getcwd(), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

BAIDU_APIKEY = os.getenv('BAIDU_APIKEY')
BAIDU_SECRETKEY = os.getenv('BAIDU_SECRETKEY')
if not BAIDU_APIKEY:
    raise ValueError('apikey错误')
if not BAIDU_SECRETKEY:
    raise ValueError('secretkey错误')


def test_get_token():
    """
    pytest baidu_client/tests/token.py::test_get_token -s
    """
    from baidu_client.client import BaiDuClient
    client = BaiDuClient()
    json_resp = client.get_access_token(BAIDU_APIKEY, BAIDU_SECRETKEY)
    # print(f'json_resp:{json_resp}')
    assert 'access_token' in json_resp
    # token = json_resp['access_token']
