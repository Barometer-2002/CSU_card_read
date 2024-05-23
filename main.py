import base64
import logging as log
import os
import platform
import time

import ddddocr
from DrissionPage import ChromiumOptions, ChromiumPage

from utils import is_debug, pushplus

log.basicConfig(level=log.DEBUG if os.getenv("debug") is not None else log.INFO)


def code_input(driver: ChromiumPage):
    """
    Clears the input field for the captcha code on a webpage and fills it with the result of OCR on the captcha image.

    :param driver: An instance of the ChromiumPage class from the DrissionPage library.
    :type driver: ChromiumPage

    :raises AssertionError: If the captcha image source is not found.

    :return: None
    :rtype: None
    """
    code_input = driver.ele(
        "css:#pane-sno > div.el-form-item.captcha > div > div.el-input.el-input--suffix > input"
    )
    code_input.clear()
    code_src = driver.ele(
        "css:#pane-sno > div.el-form-item.captcha > div > div.el-image > img"
    ).attr("src")
    assert code_src, "未找到验证码"
    code_src = code_src.removeprefix("data:image/png;base64,")
    log.debug(f"{code_src=}")
    code_src = base64.b64decode(code_src)
    ocr_result = ddddocr.DdddOcr().classification(code_src)
    log.info(f"验证码识别结果：{ocr_result}")
    code_input.input(ocr_result)


# 从环境变量读取账号密码
COUNT = os.environ["COUNT"]
PWD = os.environ["PWD"]
PUSH_PLUS_TOKEN = os.environ.get("PUSH_PLUS_TOKEN")
GITHUB_TRIGGERING_ACTOR = os.environ.get("GITHUB_TRIGGERING_ACTOR")
log.debug(f"{COUNT=}, {PWD=}, {PUSH_PLUS_TOKEN=}, {GITHUB_TRIGGERING_ACTOR=}")


# browser init
if platform.system() == "Windows":
    browser_path = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
else:
    browser_path = r"/usr/bin/chromium-browser"
assert os.path.exists(browser_path), "未找到 Chromium 浏览器"
co = ChromiumOptions()
co.set_browser_path(browser_path)
if not is_debug():
    co.set_argument("--headless")
co.set_argument("--no-sandbox")
driver = ChromiumPage(co)
driver.get("https://ecard.csu.edu.cn/plat-pc/login")

# 尝试登录
for _ in range(3):
    time.sleep(1)
    count_input = driver.ele("@type=text")
    count_input.clear()
    count_input.input(COUNT)
    pwd_input = driver.ele("@type=password")
    pwd_input.clear()
    pwd_input.input(PWD)
    code_input(driver)
    login_button = driver.ele("@type=button")
    if is_debug():
        time.sleep(4)
    login_button.click()

    error_message = driver.ele(".el-message__content")
    if not error_message:
        log.info("登录成功")
        break
else:
    raise Exception("登录失败")

# 获取数据
card_body = driver.ele("css:#cardService > div > div:nth-child(1) > div > div > div")
card_body.click()
remain = driver.ele(".value font-size-18").text[1:]

try:
    cost = float(remain)
except ValueError:
    log.error(f"余额不是数字: {remain}")
    exit(1)

log.info(cost)
driver.quit()
pushplus(cost, COUNT, GITHUB_TRIGGERING_ACTOR, PUSH_PLUS_TOKEN)
