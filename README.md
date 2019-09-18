# Boss直聘自动打招呼脚本

## 环境安装
    conda env create -f environment.yml

## 配置Config.ini
```text
[BASE]
Cookies =
;对哪个列表的人打招呼
;推荐牛人: 0,
;新牛人: 1,
;看过我: 2,
;对我感兴趣: 4
Status = 1
;针对的打招呼职位,根据具体职位来定
JobName = 全部
```

## 启动
```shell
>>> python run.py
```