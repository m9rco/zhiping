"""
     zhipin-auto.config
    ~~~~~~~~~~~~~
    配置文件获取
    Author: JoJoWu
    IDE:  PyCharm
    Version: 0.1
    Date: 2018/12/21
"""
import os
from configparser import ConfigParser


class GetConfig(object):
    """
    从Config.ini 获取基础配置
    """

    def __init__(self):
        self._pwd = os.path.split(os.path.realpath(__file__))[0]
        self._config_path = os.path.join(os.path.split(self._pwd)[0],
                                         'Config.ini')
        self._config_file = ConfigParser()
        self._config_file.read(self._config_path,
                               encoding="utf-8")  # 配置文件中有中文，需要设置读取编码

    @property
    def cookies(self):
        """
        获取Boss直聘Cookies
        Returns:

        """
        return self._config_file.get("BASE", "Cookies")

    @cookies.setter
    def cookies(self, string):
        self._config_file.set("BASE", "Cookies", string)

    @property
    def recommend_status(self):
        """
        推荐列表ID
        Returns:

        """
        return int(self._config_file.get("BASE", "Status"))

    @property
    def job_name(self):
        """
        职位名称
        Returns:

        """
        return self._config_file.get("BASE", "JobName")
