"""
     ry-sale-ticket.tools.LogHandler
-------------------------------------------------
    日志操作模块
    Author: JHao
    IDE:  PyCharm
    Version: 0.1
    Date: 2017/3/6
-------------------------------------------------
   Change Activity:
               2017/3/6: log handler
               2017/9/21: 屏幕输出/文件输出 可选(默认屏幕和文件均输出)
"""

__author__ = 'JHao'

import os
import logging
from logging.handlers import TimedRotatingFileHandler

# 日志级别
CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.join(CURRENT_PATH, os.pardir)
LOG_PATH = os.path.join(ROOT_PATH, 'log')

F_STR = "%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s"


class LogHandler(logging.Logger):
    """
    LogHandler
    """

    def __init__(self, name, level=DEBUG, stream=True, file=True):
        self.name = name
        self.level = level
        logging.Logger.__init__(self, self.name, level=level)
        if stream:
            self.__set_stream_handler()
        if file:
            self.__set_file_handler()

    def __set_file_handler(self, level=None):
        """
        set file handler
        Args:
            level:

        Returns:

        """
        if not os.path.exists(LOG_PATH):
            os.mkdir(LOG_PATH)
        file_name = os.path.join(LOG_PATH, '{name}.log'.format(name=self.name))
        # 设置日志回滚, 保存在log目录, 一天保存一个文件, 保留15天
        file_handler = TimedRotatingFileHandler(filename=file_name, when='D',
                                                interval=1, backupCount=15,
                                                encoding='utf-8')
        file_handler.suffix = '%Y%m%d.log'
        if not level:
            file_handler.setLevel(self.level)
        else:
            file_handler.setLevel(level)
        formatter = logging.Formatter(F_STR)

        file_handler.setFormatter(formatter)
        self.file_handler = file_handler
        self.addHandler(file_handler)

    def __set_stream_handler(self, level=None):
        """
        set stream handler
        Args:
            level:

        Returns:

        """
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter(F_STR)
        stream_handler.setFormatter(formatter)
        if not level:
            stream_handler.setLevel(self.level)
        else:
            stream_handler.setLevel(level)
        self.addHandler(stream_handler)

    def reset_name(self, name):
        """
        reset name
        Args:
            name:

        Returns:

        """
        self.name = name
        self.removeHandler(self.file_handler)
        self.__set_file_handler()
