import datetime
import json
import logging
from configparser import ConfigParser
from contextlib import suppress
from pathlib import Path

import ddddocr
import requests

date = datetime.date.today().strftime("%y-%m-%d")


def code_recog(code: str):
    ocr = ddddocr.DdddOcr()
    with open(code, "rb") as f:
        image = f.read()
    catch = ocr.classification(image)
    return catch


def code_input(driver):
    code_img = driver.ele(
        "css:#pane-sno > div.el-form-item.captcha > div > div.el-image > img"
    )
    code_img.get_screenshot(name="code.png")

    code_input = driver.ele(
        "css:#pane-sno > div.el-form-item.captcha > div > div.el-input.el-input--suffix > input"
    )
    # 验证码扫描
    catch = code_recog("code.png")
    code_input.input(catch)


def login(driver):
    login_button = driver.ele("@type=button")
    login_button.click()


def add_data(cost):
    origindata = "[]"
    data = []
    with suppress(FileNotFoundError):
        with open("data.js", "r") as f:
            origindata = f.read().lstrip("data=")
    try:
        data: list = json.loads(origindata)
    except json.decoder.JSONDecodeError:
        logging.error("json 格式错误，请检查")
        exit(1)

    if data and (date in data[-1].values()):
        data[-1]["val"] = cost
    else:
        data.append({"datetime": date, "val": cost})

    origindata = json.dumps(data, indent=2, ensure_ascii=False)
    Path("data.js").write_text("data=" + origindata, encoding="utf-8")
    return data


def pushplus(cost, COUNT, GITHUB_TRIGGERING_ACTOR, PUSH_PLUS_TOKEN):
    config = ConfigParser()
    config.read("config.ini", encoding="utf-8")
    tablehead = "|序号 | 时间 | 校卡余额|\n|:---:|:---:|:---:|\n"
    text = tablehead
    stime = date
    days_to_show = config.getint("pushplus", "days_to_show", fallback=10)
    data = add_data(cost)
    last_few_items = data[-days_to_show:]
    last_remain = last_few_items[-1]["val"]
    if config.getint("pushplus", "warning", fallback=10) > last_remain:
        text = f"""# <text style="color:red;">警告：校卡余额低于阈值 ({last_remain}元)</text>\n"""
    else:
        if config.getboolean("pushplus", "push_warning_only", fallback=False):
            logging.info("sufficient cost, ignoring pushing...")
            # return
        text = ""
    index = 1
    for item in reversed(last_few_items):
        tablehead += f'| {index} | {item["datetime"]} | {item["val"]}元 |\n'
        index += 1
    text += f"## 当前余额：{cost}元\n个人信息：卡号{COUNT}\n\n统计时间：{stime}\n\n### 最近{days_to_show}天数据\n{tablehead}\n"
    if (
        config.getboolean("pushplus", "detail", fallback=True)
        and GITHUB_TRIGGERING_ACTOR
    ):
        website = f"https://{GITHUB_TRIGGERING_ACTOR}.github.io/CSU_statistics"
        text += f"[图表显示更多数据]({website})\n"
        logging.info("show more details")
    with suppress():
        sendMsgToWechat(PUSH_PLUS_TOKEN, f"{stime}CSU 校卡余额统计", text, "markdown")
        logging.info("push plus executed successfully")


def sendMsgToWechat(token: str, title: str, text: str, template: str) -> None:
    """
    token:PushPlus token
    title:text's title
    text:text's body
    template:html,txt,json,markdown
    Send message to Wechat(SMS,E-mail,Dingtalk...) via PushPlus.
    default channel is wechat
    """
    url = "http://www.pushplus.plus/send"
    data = {"token": token, "title": title, "content": text, "template": template}
    a = requests.post(
        url=url, data=(json.dumps(data).encode(encoding="utf-8")), timeout=20
    )
    print(a.ok)
