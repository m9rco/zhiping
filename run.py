"""
     zhipin-auto.run
    ~~~~~~~~~~~~~
    启动文件
    Author: JoJoWu
    IDE:  PyCharm
    Version: 0.1
    Date: 2018/12/21
"""
import time
from datetime import datetime
from zhipin_auto.config import GetConfig
from zhipin_auto.zhipin import Zhiping


def run():
    """
    启动入口
    Returns:

    """
    config = GetConfig()
    zhipin = Zhiping()

    page = 0
    while True:
        times = zhipin.greeting_times
        zhipin.log.info(f"目前可打招呼次数{times}次")

        if times <= 0:
            zhipin.log.error("打招呼次数不足，明天早上9点重启")
            diff_time = datetime(datetime.now().year, datetime.now().month,
                                 datetime.now().day + 1, 9) - datetime.now()
            time.sleep(diff_time.seconds)

        page += 1
        recommend = zhipin.get_recommend_list(config.recommend_status, page,
                                              config.job_name)
        time.sleep(1)  # 防止多页已经打过招呼，访问过快引起封禁

        for j in recommend:
            if j["canGreeting"]:
                zhipin.check_resume(j["href"])
                zhipin.greeting(j)
                times -= 1
                if times - 1 <= 0:
                    break
                zhipin.log.info("休息10s")
                zhipin.log.info(f"剩余打招呼次数{times}次")
                time.sleep(10)


if __name__ == '__main__':
    run()
