"""
     zhipin-auto.test_zhipin
    ~~~~~~~~~~~~~
 
    Author: JoJoWu
    IDE:  PyCharm
    Version: 0.1
    Date: 2018/12/20
"""
import time
import pytest
from zhipin_auto.zhipin import Zhiping


@pytest.fixture
def zhipin():
    yield Zhiping("username", "password")


def test_job_id_list(zhipin):
    assert zhipin.job_id_list


@pytest.fixture
def job_id(zhipin):
    yield zhipin.job_id_list[1]


def test_get_recommend_list(zhipin, job_id):
    assert zhipin.get_recommend_list(job_id, 2, 1)


def test_greeting(zhipin, job_id):
    for i in range(10):
        recommend = zhipin.get_recommend_list(job_id, 2, i)
        for j in recommend:
            if j["canGreeting"]:
                zhipin.check_resume(j["href"])
                zhipin.greeting(j)
                time.sleep(30)


def test_greeting_times(zhipin):
    assert zhipin.greeting_times == 70


def test_qr_code(zhipin):
    assert zhipin.qr_code()
