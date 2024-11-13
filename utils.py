import datetime
import json
import logging as log
from configparser import ConfigParser
from contextlib import suppress
from pathlib import Path

import requests

date = datetime.date.today().strftime("%y-%m-%d")


def is_debug():
    return log.root.level == log.DEBUG


def add_data(cost):
    origindata = "[]"
    data = []
    with suppress(FileNotFoundError):
        with open("data.js", "r") as f:
            origindata = f.read().lstrip("data=")

    try:
        data: list = json.loads(origindata)
    except json.decoder.JSONDecodeError:
        log.error("json 格式错误，请检查")
        exit(1)

    if data and (date in data[-1].values()):
        data[-1]["val"] = cost
    else:
        data.append({"datetime": date, "val": cost})

    origindata = json.dumps(data, indent=2, ensure_ascii=False)
    Path("data.js").write_text("data=" + origindata, encoding="utf-8")
    return data

def pushplus(cost, COUNT, PUSH_PLUS_TOKEN):
    config = ConfigParser()
    config.read("config.ini", encoding="utf-8")
    tablehead = "|序号 | 时间 | 剩余电量|\n|:---:|:---:|:---:|\n"
    text = tablehead
    stime = date
    days_to_show = config.getint("pushplus", "days_to_show", fallback=10)
    data = add_data(cost)
    last_few_items = data[-days_to_show:]
    last_remain = last_few_items[-1]["val"]
    if config.getint("pushplus", "warning", fallback=10) > last_remain:
        text = f"""# <text style="color:red;">警告：剩余电量低于阈值 ({last_remain}度)</text>\n"""
    else:
        if config.getboolean("pushplus", "push_warning_only", fallback=False):
            return
        text = ''
    index = 1
    for item in reversed(last_few_items):
        tablehead += f'| {index} | {item["datetime"]} | {item["val"]}度 |\n'
        index += 1
    text += f"## 当前余额：{cost}度\n个人信息：卡号{COUNT}\n\n统计时间：{stime}\n\n### 最近{days_to_show}天数据\n{tablehead}\n"
    with suppress():
        sendMsgToWechat(PUSH_PLUS_TOKEN, f"{stime}CSU 剩余电量统计", text, "markdown")
        log.info("push plus executed successfully")



def sendMsgToWechat(token: str, title: str, text: str, template: str) -> None:
    url = "http://www.pushplus.plus/send"
    data = {"token": token, "title": title, "content": text, "template": template}
    a = requests.post(
        url=url, data=(json.dumps(data).encode(encoding="utf-8")), timeout=20
    )
    print(a.ok)
