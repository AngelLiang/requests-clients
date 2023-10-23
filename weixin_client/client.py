import json
from json import dumps as json_dumps
from typing import Dict, List
from urllib3.util import Retry
from requests import Request, Session
import requests
from weixin_client.utils import pretty_print_POST

from weixin_client.errors import InvaildMaterialError
from weixin_client import result_code


class ClientError(Exception):
    pass


class WeiXinClient:

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
        try:
            resp_json = resp.json()
            if 'errcode' in resp_json:
                if resp_json['errcode'] == result_code.INVALID_MEDIA:
                    raise InvaildMaterialError(detail=str(resp_json))
        except json.decoder.JSONDecodeError:
            pass

    def get_access_token(self, appid: str, appsecret: str, grant_type='client_credential'):
        """获取access token"""
        url = 'https://api.weixin.qq.com/cgi-bin/token'
        params = {
            'grant_type': grant_type,
            'appid': appid,
            'secret': appsecret
        }
        resp = self.do_get(url, params=params)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_stable_token(self, appid: str, appsecret: str, grant_type='client_credential', force_refresh=False):
        """获取stable_token"""
        url = 'https://api.weixin.qq.com/cgi-bin/stable_token'
        data = {
            'grant_type': grant_type,
            'appid': appid,
            'secret': appsecret,
            'force_refresh': force_refresh,
        }
        resp = self.do_post(url, json=data)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_jsapi_ticket(self, access_token: str, type='jsapi'):
        """获取jsapi ticket"""
        url = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket'
        params = {
            'access_token': access_token,
            'type': type,
        }
        resp = self.do_get(url, params=params)
        resp_json = self.handle_response(resp)
        return resp.json()

    def bizsend_message(
        self,
        access_token: str,
        openid: str,
        template_id: str,
        data: Dict,
        page=None,
        miniprogram=None,
    ):
        """
        发送订阅通知

        :param access_token: 接口调用凭证
        :param openid: 接收者（用户）的 openid
        :param template_id: 下发的订阅模板id
        :param data: 模板内容，格式形如 { "key1": { "value": any }, "key2": { "value": any } }

        #send%E5%8F%91%E9%80%81%E8%AE%A2%E9%98%85%E9%80%9A%E7%9F%A5
        ref: https://developers.weixin.qq.com/doc/offiaccount/Subscription_Messages/api.html
        """

        url = 'https://api.weixin.qq.com/cgi-bin/message/subscribe/bizsend'
        params = {
            'access_token': access_token,
        }
        body_json = {
            'touser': openid,
            'template_id': template_id,
            'data': data,
        }
        resp = self.do_post(url, params=params, json=body_json)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_category(self, access_token):
        """获取公众号所属类目，可用于查询类目下的公共模板"""
        url = 'https://api.weixin.qq.com/wxaapi/newtmpl/getcategory'
        params = {
            'access_token': access_token,
        }
        resp = self.do_get(url, params=params)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_pub_template_title_list(self, access_token, category_ids):
        url = 'https://api.weixin.qq.com/wxaapi/newtmpl/getpubtemplatetitles'
        params = {
            'access_token': access_token,
        }
        # body_json = {
        #     'touser': openid,
        #     'template_id': template_id,
        #     'data': data,
        # }
        # resp = self.do_post(url, params=params, json=body_json)
        # resp_json = self.handle_response(resp)
        # return resp.json()

    def get_user_list(self, access_token, next_openid=None):
        pass
        url = 'https://api.weixin.qq.com/cgi-bin/user/get'
        params = {
            'access_token': access_token,
        }
        if next_openid:
            params['next_openid'] = next_openid
        resp = self.do_get(url, params=params)
        resp_json = self.handle_response(resp)
        return resp.json()

    def add_poi(self, access_token, json):
        """创建门店

        参考资料：https://developers.weixin.qq.com/doc/offiaccount/WeChat_Stores/WeChat_Store_Interface.html#_3-2%E5%88%9B%E5%BB%BA%E9%97%A8%E5%BA%97
        """
        # url = self.base_url + "/cgi-bin/poi/addpoi"
        url = 'http://api.weixin.qq.com/cgi-bin/poi/addpoi'
        params = {
            "access_token": access_token,
        }
        resp = self.do_post(url, params=params, json=json)
        resp_json = self.handle_response(resp)
        return resp.json()

    def add_card(self, access_token, json):
        """创建卡券

        参考资料：https://developers.weixin.qq.com/doc/offiaccount/Cards_and_Offer/Create_a_Coupon_Voucher_or_Card.html#6


        调用接口后，返回的消息
        ```
        {'errcode': 73219,
            'errmsg': '暂不支持本账号创建优惠券，具体可访问mp.weixin.qq.com,关注卡券下线公告通知。12月10日0点起，商户可正常申请开通“微信卡券”功能，申请开通后，“优惠券”功能将不再支持使用。新开通卡券功能的商户使用“会员卡”、“礼品卡”或“票证”等能力不受影响；如商户有在微信生态内发放优惠券的需求，可使用微信支付优惠券：商家券或支付券（即代金券）。如需了解更多，可查阅微信支付优惠券产品功能介绍。 hint: [2BNQIA0112r122]'}
        ```
        """
        # url = self.base_url + "/card/create"
        url = 'https://api.weixin.qq.com/card/create'
        params = {
            "access_token": access_token,
        }
        resp = self.do_post(url, params=params, json=json)
        resp_json = self.handle_response(resp)
        return resp.json()

    def set_card_testwhitelist(self, openid_list: List):
        """设置卡券测试白名单

        """
        url = self.base_url + "/card/testwhitelist/set"
        params = {
            "access_token": self.token,
        }
        body = {'openid': []}
        for openid in openid_list:
            body['openid'].append(openid)
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_card_code(self, code, card_id=None, check_consume=None):
        """
        查询当前code是否可以被核销并检查code状态

        参考资料：https://developers.weixin.qq.com/doc/offiaccount/Cards_and_Offer/Managing_Coupons_Vouchers_and_Cards.html#0
        """
        url = self.base_url + "/card/code/get"
        params = {
            "access_token": self.token,
        }
        body = {
            'code': code,
        }
        if card_id:
            body['card_id'] = card_id
        if check_consume:
            body['check_consume'] = check_consume
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_card(self, card_id):
        """ 查看卡券详情
        :param card_id: 卡券ID
        """
        url = self.base_url + "/card/get"
        params = {
            "access_token": self.token,
        }
        body = {
            'card_id': card_id,
        }
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def batchget_card(self, access_token, offset=0, count=10, status_list=None):
        """
        批量查询卡券列表

        :param status_list: 支持开发者拉出指定状态的卡券列表

        “CARD_STATUS_NOT_VERIFY”, 待审核 ；
        “CARD_STATUS_VERIFY_FAIL”, 审核失败；
        “CARD_STATUS_VERIFY_OK”， 通过审核；
        “CARD_STATUS_DELETE”， 卡券被商户删除；
        “CARD_STATUS_DISPATCH”， 在公众平台投放过的卡券；

        参考资料：developers.weixin.qq.com/doc/offiaccount/Cards_and_Offer/Managing_Coupons_Vouchers_and_Cards.html#3
        """
        # url = self.base_url + "/card/batchget"
        url = 'https://api.weixin.qq.com/card/batchget'
        params = {
            "access_token": access_token,
        }
        body = {
            'offset': offset,
            'count': count,
        }
        if status_list:
            body['status_list'] = status_list
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def unavailable_card(self, card_id, code, reason=None):
        """设置卡券失效"""
        url = self.base_url + "/card/code/unavailable"
        params = {
            "access_token": self.token,
        }
        body = {
            'card_id': card_id,
            'code': code,
        }
        if reason:
            body['reason'] = reason
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_card_bizuininfo(self, begin_date, end_date, cond_source):
        """拉取卡券概况数据"""
        url = self.base_url + "/card/code/unavailable"
        params = {
            "access_token": self.token,
        }
        body = {
            'begin_date': begin_date,
            'end_date': end_date,
            'cond_source': cond_source,
        }
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def consume_card(self, code, card_id=None):
        """线下核销卡券

        :params code: 需要核销的卡券code
        :params card_id: 需要核销的卡券id。卡券ID。创建卡券时use_custom_code填写true时必填。非自定义Code不必填写。

        消耗code接口是核销卡券的唯一接口,开发者可以调用当前接口将用户的优惠券进行核销，该过程不可逆。

        参考资料：https://developers.weixin.qq.com/doc/offiaccount/Cards_and_Offer/Redeeming_a_coupon_voucher_or_card.html#_1-2-%E6%A0%B8%E9%94%80Code%E6%8E%A5%E5%8F%A3
        """
        url = self.base_url + "/card/code/consume"
        params = {
            "access_token": self.token,
        }
        body = {
            'code': code,
        }
        if card_id:
            body['card_id'] = card_id
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def update_card(self, data):
        """更改卡券信息
        TODO

        参考资料：https://developers.weixin.qq.com/doc/offiaccount/Cards_and_Offer/Managing_Coupons_Vouchers_and_Cards.html#4
        """
        url = self.base_url + "/card/update"
        params = {
            "access_token": self.token,
        }
        body = data
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def delete_card(self, card_id):
        """删除卡券"""
        url = self.base_url + "/card/delete"
        params = {
            "access_token": self.token,
        }
        body = {'card_id': card_id}
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_material_list(self, access_token, type, offset=0, count=20):
        """获取素材列表

        :params type: 图片（image）、视频（video）、语音 （voice）、图文（news）
        :params offset:
        :params count:

        return:

        {
            "total_count": TOTAL_COUNT,
            "item_count": ITEM_COUNT,
            "item": [{
                "media_id": MEDIA_ID,
                "content": {
                    "news_item": [{
                        "title": TITLE,
                        "thumb_media_id": THUMB_MEDIA_ID,
                        "show_cover_pic": SHOW_COVER_PIC(0 / 1),
                        "author": AUTHOR,
                        "digest": DIGEST,
                        "content": CONTENT,
                        "url": URL,
                        "content_source_url": CONTETN_SOURCE_URL
                    },
                    //多图文消息会在此处有多篇文章
                    ]
                    },
                    "update_time": UPDATE_TIME
                },
                //可能有多个图文消息item结构
            ]
        }

        """
        url = 'https://api.weixin.qq.com/cgi-bin/material/batchget_material'
        params = {
            "access_token": access_token,
        }
        body = {'type': type, 'offset': offset, 'count': count}
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_material_count(self, access_token):
        """获取素材总数

        return:
        {
        "voice_count":COUNT,
        "video_count":COUNT,
        "image_count":COUNT,
        "news_count":COUNT
        }

        """

        url = 'https://api.weixin.qq.com/cgi-bin/material/get_materialcount'
        params = {
            "access_token": access_token,
        }
        resp = self.do_get(url, params=params)
        resp_json = self.handle_response(resp)
        return resp.json()

    def upload_img(self, access_token, img_path):
        """上传图文消息内的图片获取URL

        return:

        {
            "url":  "http://mmbiz.qpic.cn/mmbiz/gLO17UPS6FS2xsypf378iaNhWacZ1G1UplZYWEYfwvuU6Ont96b1roYs CNFwaRrSaKTPCUdBK9DgEHicsKwWCBRQ/0"
        }

        """
        url = 'https://api.weixin.qq.com/cgi-bin/media/uploadimg'
        params = {
            "access_token": access_token,
        }
        files = {'media': open(img_path, 'rb')}
        resp = self.do_request('post', url, params=params, files=files)
        resp_json = self.handle_response(resp)
        return resp.json()

    def add_material(self, access_token, type, media, title: str, intro: str):
        """新增其他类型永久素材

        :param type: 媒体文件类型，分别有图片（image）、语音（voice）、视频（video）和缩略图（thumb）
        :param title: 视频素材的标题
        :param intro: 视频素材的描述

        return:

        {
            "media_id":MEDIA_ID,
            "url":URL
        }

        ref: https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/Adding_Permanent_Assets.html

        """
        url = 'https://api.weixin.qq.com/cgi-bin/material/add_material'
        params = {
            "access_token": access_token,
            'type': type,
        }
        files = {
            'media': open(media, 'rb'),
            'description': json_dumps({
                "title": title,
                "introduction": intro
            })
        }
        resp = self.do_request('post', url, params=params, files=files)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_material(self, access_token, media_id):
        """获取永久素材

        接口返回说明
        图文素材:
        {
            "news_item":
            [
                {
                "title":TITLE,
                "thumb_media_id":THUMB_MEDIA_ID,
                "show_cover_pic":SHOW_COVER_PIC(0/1),
                "author":AUTHOR,
                "digest":DIGEST,
                "content":CONTENT,
                "url":URL,
                "content_source_url":CONTENT_SOURCE_URL
                },
                //多图文消息有多篇文章
            ]
        }

        视频消息素材：
        {
            "title":TITLE,
            "description":DESCRIPTION,
            "down_url":DOWN_URL,
        }

        ref: https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/Getting_Permanent_Assets.html
        """
        url = 'https://api.weixin.qq.com/cgi-bin/material/get_material'
        params = {
            "access_token": access_token,
        }
        body = {
            'media_id': media_id,
        }
        resp = self.do_post(url, params=params, json=body)
        self.handle_response(resp)

        try:
            resp_json = resp.json()
            if resp_json['errcode'] == result_code.INVALID_MEDIA:
                raise InvaildMaterialError(detail=str(resp_json))
        except json.decoder.JSONDecodeError:
            return resp.content

        # return resp.content

    def del_material(self, access_token, media_id):
        """删除永久素材


        正常情况下调用成功时，errcode将为0。
        """

        url = 'https://api.weixin.qq.com/cgi-bin/material/del_material'
        params = {
            "access_token": access_token,
        }
        body = {
            'media_id': media_id,
        }

        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    ### 草稿 ###

    def add_draft(self, access_token, articles: list):
        """新建草稿

        return:
        {
           "media_id":MEDIA_ID
        }

        ref: https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Add_draft.html
        """
        url = 'https://api.weixin.qq.com/cgi-bin/draft/add'
        params = {
            "access_token": access_token,
        }
        body = {
            "articles": articles
        }
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_draft(self, access_token, media_id):
        """获取草稿

        :param media_id: 要获取的草稿的media_id

        return:
        {
            "news_item": [
                {
                    "title":TITLE,
                    "author":AUTHOR,
                    "digest":DIGEST,
                    "content":CONTENT,
                    "content_source_url":CONTENT_SOURCE_URL,
                    "thumb_media_id":THUMB_MEDIA_ID,
                    "show_cover_pic":0,
                    "need_open_comment":0,
                    "only_fans_can_comment":0,
                    "url":URL
                }
                //多图文消息应有多段 news_item 结构
            ]
        }

        ref: https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Get_draft.html
        """
        url = 'https://api.weixin.qq.com/cgi-bin/draft/add'
        params = {
            "access_token": access_token,
        }
        body = {
            'media_id': media_id
        }
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def update_draft(self, access_token, media_id, index, article):
        """修改草稿

        参数	是否必须	说明
        media_id	是	要修改的图文消息的id
        index	是	要更新的文章在图文消息中的位置（多图文消息时，此字段才有意义），第一篇为0
        title	是	标题
        author	否	作者
        digest	否	图文消息的摘要，仅有单图文消息才有摘要，多图文此处为空。如果本字段为没有填写，则默认抓取正文前54个字。
        content	是	图文消息的具体内容，支持HTML标签，必须少于2万字符，小于1M，且此处会去除JS,涉及图片url必须来源 "上传图文消息内的图片获取URL"接口获取。外部图片url将被过滤。
        content_source_url	否	图文消息的原文地址，即点击“阅读原文”后的URL
        thumb_media_id	是	图文消息的封面图片素材id（必须是永久MediaID）
        need_open_comment	否	Uint32 是否打开评论，0不打开(默认)，1打开
        only_fans_can_comment	否	Uint32 是否粉丝才可评论，0所有人可评论(默认)，1粉丝才可评论

        """
        url = 'https://api.weixin.qq.com/cgi-bin/draft/update'
        params = {
            "access_token": access_token,
        }
        body = {
            "media_id": media_id,
            "index": index,
            "articles": article,
        }
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def del_draft(self, access_token, media_id):
        """删除草稿

        新增草稿后，开发者可以根据本接口来删除不再需要的草稿，节省空间。此操作无法撤销，请谨慎操作。

        """
        url = 'https://api.weixin.qq.com/cgi-bin/draft/delete'
        params = {
            "access_token": access_token,
        }
        body = {
            'media_id': media_id
        }
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_draft_list(self, access_token, offset=0, count=20, no_content=0):
        """获取草稿的列表

        return:

        {
            "total_count":TOTAL_COUNT,
            "item_count":ITEM_COUNT,
            "item":[
                {
                    "media_id":MEDIA_ID,
                    "content": {
                        "news_item" : [
                            {
                                "title":TITLE,
                                "author":AUTHOR,
                                "digest":DIGEST,
                                "content":CONTENT,
                                "content_source_url":CONTENT_SOURCE_URL,
                                "thumb_media_id":THUMB_MEDIA_ID,
                                "show_cover_pic":0,
                                "need_open_comment":0,
                                "only_fans_can_comment":0,
                                "url":URL
                            },
                            //多图文消息会在此处有多篇文章
                        ]
                    },
                    "update_time": UPDATE_TIME
                },
                //可能有多个图文消息item结构
            ]
        }


        ref: https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Get_draft_list.html
        """
        url = 'https://api.weixin.qq.com/cgi-bin/draft/batchget'
        params = {
            "access_token": access_token,
        }
        body = {
            "offset": offset,
            "count": count,
            "no_content": no_content
        }
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_draft_count(self, access_token):
        """获取草稿的总数"""
        url = 'https://api.weixin.qq.com/cgi-bin/draft/count'
        params = {
            "access_token": access_token,
        }
        resp = self.do_get(url, params=params)
        resp_json = self.handle_response(resp)
        return resp.json()

    ### 草稿 end ###

    def publish_article(self, access_token, media_id):
        """发布接口

        开发者需要先将图文素材以草稿的形式保存（见“草稿箱/新建草稿”，如需从已保存的草稿中选择，见“草稿箱/获取草稿列表”），选择要发布的草稿 media_id 进行发布

        ref: https://developers.weixin.qq.com/doc/offiaccount/Publish/Publish.html
        """
        url = 'https://api.weixin.qq.com/cgi-bin/freepublish/submit'
        params = {
            "access_token": access_token,
        }
        body = {
            "media_id": media_id,
        }
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_publish_list(self, access_token, offset=0, count=20, no_content=0):
        """获取成功发布列表

        return:

        {
            "total_count":TOTAL_COUNT,
            "item_count":ITEM_COUNT,
            "item":[
                {
                    "article_id":ARTICLE_ID,
                    "content": {
                        "news_item" : [
                            {
                                "title":TITLE,
                                "author":AUTHOR,
                                "digest":DIGEST,
                                "content":CONTENT,
                                "content_source_url":CONTENT_SOURCE_URL,
                                "thumb_media_id":THUMB_MEDIA_ID,
                                "show_cover_pic":1,
                                "need_open_comment":0,
                                "only_fans_can_comment":0,
                                "url":URL,
                                "is_deleted":false
                            }
                            //多图文消息会在此处有多篇文章
                        ]
                    },
                    "update_time": UPDATE_TIME
                },
                //可能有多个图文消息item结构
            ]
        }


        """
        url = 'https://api.weixin.qq.com/cgi-bin/freepublish/batchget'
        params = {
            "access_token": access_token,
        }
        body = {
            "offset": offset,
            "count": count,
            "no_content": no_content
        }
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def get_article(self, access_token, article_id):
        """通过 article_id 获取已发布的图文信息
        """
        url = 'https://api.weixin.qq.com/cgi-bin/freepublish/getarticle'
        params = {
            "access_token": access_token,
        }
        body = {
            "article_id": article_id,
        }
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def del_publish(self, access_token, article_id, index=1):
        """
        发布成功之后，随时可以通过该接口删除。此操作不可逆，请谨慎操作。

        参数	是否必须	说明
        access_token	是	调用接口凭证
        article_id	是	成功发布时返回的 article_id
        index	否	要删除的文章在图文消息中的位置，第一篇编号为1，该字段不填或填0会删除全部文章

        """
        url = 'https://api.weixin.qq.com/cgi-bin/freepublish/delete'
        params = {
            "access_token": access_token,
        }
        body = {
            "article_id": article_id,
            "index": index
        }
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def query_publish_status(self, access_token, publish_id):
        """发布状态轮询接口


        成功：

        {
            "publish_id":"100000001",
            "publish_status":0,
            "article_id":ARTICLE_ID,
            "article_detail":{
                "count":1,
                "item":[
                    {
                        "idx":1,
                        "article_url": ARTICLE_URL
                    }
                    //如果 count 大于 1，此处会有多篇文章
                ]
            },
            "fail_idx": []
        }

        发布中：

        {
            "publish_id":"100000001",
            "publish_status":1,
            "fail_idx": []
        }

        原创审核不通过：

        {
            "publish_id":"100000001",
            "publish_status":2,
            "fail_idx":[1,2]
        }


        ref: https://developers.weixin.qq.com/doc/offiaccount/Publish/Get_status.html

        """
        url = 'https://api.weixin.qq.com/cgi-bin/freepublish/get'
        params = {
            "access_token": access_token,
        }
        body = {
            "publish_id": publish_id,
        }
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()

    def preview(self, access_token, openid, msgtype, media_id):
        """


        ref: https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Batch_Sends_and_Originality_Checks.html#5
        """
        if msgtype not in ('mpnews', 'text', 'voice', 'image', 'mpvideo', 'wxcard'):
            raise ValueError('msgtype不合法')

        url = 'https://api.weixin.qq.com/cgi-bin/message/mass/preview'
        params = {
            "access_token": access_token,
        }
        body = {
            'touser': openid,
            'msgtype': msgtype,
            msgtype: {
                'media_id': media_id,
            }
        }
        resp = self.do_post(url, params=params, json=body)
        resp_json = self.handle_response(resp)
        return resp.json()
