# import json
from json import dumps as json_dumps
from typing import Dict, List
from urllib3.util import Retry
from requests import Request, Session
import requests
# from baidu_client.utils import pretty_print_POST


class ClientError(Exception):
    pass


class BaiDuClient:

    def __init__(self, timeout=10) -> None:
        self.timeout: int = timeout

    def do_request(self, method, url, params=None, json=None, headers=None, files=None):
        req = Request(method=method, url=url, params=params, json=json, headers=headers, files=files)
        prepared = req.prepare()

        if json:
            prepared.body = json_dumps(json, ensure_ascii=False, allow_nan=False).encode('utf-8')
            prepared.prepare_content_length(prepared.body)
        # pretty_print_POST(prepared)

        try:
            s = Session()
            # s.mount('http://', HTTPAdapter(max_retries=self.retries))
            return s.send(prepared, timeout=self.timeout)
        except requests.exceptions.ReadTimeout as err:
            raise ClientError(err)
        except requests.exceptions.ConnectionError as err:
            raise ClientError(err)

    def do_get(self, url, params=None, headers=None):
        return self.do_request('get', url, params=params, headers=headers)

    def do_post(self, url, params=None, json=None, headers=None):
        return self.do_request('post', url, params=params, json=json, headers=headers)

    # def join_url(self, path):
    #     return self.base_url + path

    def handle_response(self, resp):
        pass

    def create_tts(self):
        """创建长文本在线合成任务
        TODO
        
        ref: https://cloud.baidu.com/doc/SPEECH/s/ulbxh8rbu#%E5%88%9B%E5%BB%BA%E9%95%BF%E6%96%87%E6%9C%AC%E5%9C%A8%E7%BA%BF%E5%90%88%E6%88%90%E4%BB%BB%E5%8A%A1
        """
        url = 'https://aip.baidubce.com/rpc/2.0/tts/v1/create'
        params = {
        }
        resp = self.do_post(url, params=params)
        self.handle_response(resp)
        return resp.json()

    def query_tts(self):
        """查询长文本在线合成任务结果
        TODO
        
        ref: https://cloud.baidu.com/doc/SPEECH/s/ulbxh8rbu#%E6%9F%A5%E8%AF%A2%E9%95%BF%E6%96%87%E6%9C%AC%E5%9C%A8%E7%BA%BF%E5%90%88%E6%88%90%E4%BB%BB%E5%8A%A1%E7%BB%93%E6%9E%9C
        """
        url = 'https://aip.baidubce.com/rpc/2.0/tts/v1/create'
        params = {
        }
        resp = self.do_post(url, params=params)
        self.handle_response(resp)
        return resp.json()
