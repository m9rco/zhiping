"""
     zhipin-auto.zhipin
    ~~~~~~~~~~~~~
    Boss直聘
    Author: JoJoWu
    IDE:  PyCharm
    Version: 0.1
    Date: 2018/12/20
"""
import sys
import time
from functools import wraps
from urllib import parse
from bs4 import BeautifulSoup
from pyqrcode import QRCode
from requests_html import HTMLSession
from zhipin_auto.log_handler import LogHandler
from zhipin_auto.config import GetConfig


def lazy_property(func):
    """
    懒加载
    Args:
        func:

    Returns:

    """
    attr = '_lazy__' + func.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr):
            setattr(self, attr, func(self))
        return getattr(self, attr)

    return _lazy_property


def login_wrapper(func):
    """
    登陆验证
    Args:
        func: 装饰的函数

    Returns: 装饰的函数返回值

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """
        装饰器
        Args:
            self:
            *args:
            **kwargs:

        Returns:

        """
        cookies = GetConfig().cookies
        if cookies:
            self.session.cookies.set("t", cookies)
            self.session.cookies.set("wt", cookies)
            return func(self, *args, **kwargs)
        if self.login():
            GetConfig().cookies = self.session.cookies["t"]
            return func(self, *args, **kwargs)
        raise ZhipinError("登陆发生未知错误")

    return wrapper


class Zhiping(object):
    """
    Boss直聘
    """

    def __init__(self):
        """
        Boss直聘账号
        """
        self.log = LogHandler("ZhiPing")
        self.session = HTMLSession()
        self.g_headers = {
            "Host": "www.zhipin.com",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                          " AppleWebKit/537.36 (KHTML, like Gecko)"
                          " Chrome/71.0.3578.98 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,"
                      "application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        self.p_headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                          " AppleWebKit/537.36 (KHTML, like Gecko)"
                          " Chrome/71.0.3578.98 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        self.login()

    @lazy_property
    def job_id_list(self):
        """
        获取职位名和ID记入Redis
        Returns:
            job_id_list(List):
        """
        rep = self.get_req("https://www.zhipin.com/chat/im",
                           headers=self.g_headers, timeout=20)
        job_id_list = []
        job_id_dom = rep.html.find(".top-recommend .dropdown-menu",
                                   first=True).find("li")
        for i in job_id_dom:
            job_id_list.append({
                f"{i.text}": i.attrs["data-jobid"]
            })
        return job_id_list

    def get_recommend_list(self, status, page, job_name=None):
        """
        获取推荐列表
        Args:
            job_name: 职位ID
            page: 获取的页数
            status: 查看推荐列表的类型
                推荐牛人: 0,
                新牛人: 1,
                看过我: 2,
                对我感兴趣: 4

        Returns:
            recommend_list(List): 推荐者列表
                Examples: [{
                    "name": 推荐的求职者名字,
                    "uid": 求职者uid,
                    "eid": 求职者eid,
                    "expect": 求职者expect_id,
                    "jid": 求职者jid,
                    "lid": 求职者lid,
                    "canGreeting": 是否可以打招呼,
                    "href": 打招呼请求的网址
                    },{...}...]
                以上的参都为String
        """
        head = "https://www.zhipin.com/boss/recommend/geeks.json"

        job_id = -1
        if job_name:
            for i in self.job_id_list:
                for key, val in i.items():
                    job_id = val if job_name in key else job_id

        params = {
            "page": page,
            "status": status,
            "jobid": job_id,
            "salary": "0",
            "experience": "0",
            "degree": "0"
        }
        rep = self.get_req(f"{head}?{parse.urlencode(params)}",
                           headers=self.g_headers, timeout=20)
        if rep.json().get("rescode") != 1:
            self.log.error(rep.json()["resmsg"])
            raise BanError(rep.json()["resmsg"])

        recommend_list = []

        html = BeautifulSoup(rep.json()["htmlList"], "lxml")
        for i in html.select("a"):
            greeting_status = i.findPreviousSibling().find("button").text
            data = {
                "name": i.select_one(".geek-name").text,
                "uid": i.attrs["data-uid"],
                "eid": i.attrs["data-eid"],
                "expect": i.attrs["data-expect"],
                "jid": i.attrs["data-jid"],
                "lid": i.attrs["data-lid"],
                "canGreeting": True if greeting_status == "打招呼" else False,
                "href": i.attrs["href"]
            }
            recommend_list.append(data)
        return recommend_list

    def greeting(self, applicant):
        """
        对求职者进行打招呼
        Args:
            applicant(Dict): 求职者
                Examples:{
                            "name": 推荐的求职者名字,
                            "uid": 求职者uid,
                            "eid": 求职者eid,
                            "expect": 求职者expect_id,
                            "jid": 求职者jid,
                            "lid": 求职者lid,
                            "canGreeting": 是否可以打招呼,
                            "href": 打招呼请求的网址
                        }
        Returns:

        """
        self.log.info(f"开始对{applicant['name']}打招呼")
        url = "https://www.zhipin.com/chat/batchAddRelation.json"
        params = {
            "gids": applicant["uid"],
            "jids": applicant["jid"],
            "expectIds": applicant["expect"],
            "lids": applicant["lid"]
        }
        rep = self.session.post(url, data=parse.urlencode(params),
                                headers=self.p_headers)
        self.log.debug(rep.text)
        if rep.status_code != 200:
            self.log.error("打招呼失败")
            raise ZhipinError("打招呼失败")
        if rep.json()["data"][0]["stateDes"] == "您今日在非火爆职位中的总沟通人数已达上限，请明日再试":
            self.log.error("打招呼人数已达到上限")
            raise ZhipinError("打招呼人数已达到上限")
        self.log.info("打招呼成功")
        return True

    def check_resume(self, href):
        """
        访问简历
        Args:
            href:简历所在地址

        Returns:

        """
        rep = self.get_req(f"https://www.zhipin.com{href}")
        if "resume-item-pop-box" not in rep.text:
            self.log.error("简历访问失败")
            self.log.debug(rep.text)
            raise ZhipinError("简历访问失败")
        self.log.info("简历查看成功")
        return True

    def get_req(self, url, **kwargs):
        """
        Get请求
        Args:
            url:
            **kwargs:

        Returns:

        """
        kwargs.setdefault("headers", self.g_headers)
        kwargs.setdefault("timeout", 10)
        rep = self.session.get(url, **kwargs)
        if rep.status_code != 200:
            self.log.debug(rep.text)
            raise RequestError(url + "访问失败")
        return rep

    @property
    def greeting_times(self):
        """
        打招呼次数
        Returns:

        """
        url = "https://www.zhipin.com/privilege/my/detail.json"
        rep = self.get_req(url)

        if rep.json().get("rescode") != 1:
            self.log.error(rep.json()["resmsg"])
            raise BanError(rep.json()["resmsg"])

        account_items = rep.json()["data"]["accountPrivilegeItem"]
        used_items = rep.json()["data"]["dayUsedPrivilegeItem"]
        max_times, used_times = 100, 0

        for i in account_items["privilegeUsedItemList"]:
            if i["headTitle"] == "每日使用权益总量":
                for j in i["privilegeUsedList"]:
                    if j["privilegeUsedDesc"] == "每日沟通总量":
                        max_times = j["privilegeCount"]
        for i in used_items["privilegeUsedList"]:
            if i["privilegeUsedDesc"] == "今日沟通牛人":
                used_times = i["privilegeCount"]

        remain_times = max_times - used_times
        return remain_times

    def login(self):
        """
        使用二维码登陆
        Returns:

        """
        cookies = GetConfig().cookies
        if cookies:
            self.session.cookies.set("t", "ShW8q7dIkhxfhZbs")
            self.session.cookies.set("wt", "ShW8q7dIkhxfhZbs")
            return True
        self.log.info("请扫描二维码登陆")
        url = "https://www.zhipin.com/wapi/zppassport/captcha/randkey"
        rep = self.session.post(url, data="pk=cpc_user_sign_up",
                                headers=self.p_headers)

        if rep.status_code != 200:
            self.log.debug(rep.text)
            raise RequestError("访问异常")
        if rep.json()["code"] != 0:
            self.log.debug(rep.text)
            raise ZhipinError("二维码请求失败")

        qr_id = rep.json()["zpData"]["qrId"]
        self.show_qr_code(qr_id)

        headers = {
            "Host": "www.zhipin.com",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                          " AppleWebKit/537.36 (KHTML, like Gecko)"
                          " Chrome/71.0.3578.98 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,"
                      "application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Referer": "https://login.zhipin.com/?ka=header-login",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "sec-fetch-mode": "cors",

        }
        for i in range(30):
            url = "https://www.zhipin.com/scan/uuid={qr_id}"
            rep = self.get_req(url, headers=headers)
            if rep.url == 'https://www.zhipin.com/geek/new/index/resume':
                self.log.info("登陆成功")
                GetConfig().cookies = self.session.cookies["t"]
                return True
            time.sleep(1)
        return False

    @staticmethod
    def show_qr_code(qr_id):
        """
        在控制台上打印二维码
        代码取之于WxBot项目中
        link:https://github.com/Urinx/WeixinBot/blob/master/wxbot_demo_py3/weixin.py
        Args:
            qr_id: 二维码ID

        Returns:

        """
        qr_data = QRCode(qr_id).text(1)
        try:
            black = u'\u2588'
            sys.stdout.write(black + '\r')
            sys.stdout.flush()
        except UnicodeEncodeError:
            white = 'MM'
        else:
            white = black
        black = '  '
        block_count = 2
        if abs(block_count) == 0:
            block_count = 1
        white *= abs(block_count)
        if block_count < 0:
            white, black = black, white
        sys.stdout.write(' ' * 50 + '\r')
        sys.stdout.flush()
        qr_code = qr_data.replace('0', white).replace('1', black)
        sys.stdout.write(qr_code)
        sys.stdout.flush()


class RequestError(Exception):
    """
    请求异常
    """
    pass


class BanError(Exception):
    """
    访问频次异常
    """
    pass


class ZhipinError(Exception):
    """
    BOSS直聘异常捕捉
    """
    pass
