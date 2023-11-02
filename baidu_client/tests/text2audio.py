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


def test_text2audio():
    """
    pytest baidu_client/tests/text2audio.py::test_text2audio -s
    """
    from baidu_client.client import BaiDuClient
    client = BaiDuClient()
    json_resp = client.get_access_token(BAIDU_APIKEY, BAIDU_SECRETKEY)
    # print(json_resp)
    token = json_resp['access_token']
    cuid = 'test'
    resp = client.text2audio('你好', token=token, cuid=cuid)
    print(resp.headers)
    assert 'audio' in resp.headers['Content-Type']


def test_text2audio_wav():
    """
    pytest baidu_client/tests/text2audio.py::test_text2audio_wav -s
    """
    from baidu_client.client import BaiDuClient
    client = BaiDuClient()
    json_resp = client.get_access_token(BAIDU_APIKEY, BAIDU_SECRETKEY)
    # print(json_resp)
    token = json_resp['access_token']
    cuid = 'test'
    resp = client.text2audio('你好', token=token, cuid=cuid, aue=6)
    print(resp.headers)
    assert 'audio/wav' == resp.headers['Content-Type']
