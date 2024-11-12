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
    code_input = driver.ele("@placeholder=请输入验证码")
    code_input.clear()
    code_src = driver.ele(
        locator=".van-image__img"
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
    browser_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
else:
    browser_path = r"/usr/bin/chromium-browser"
assert os.path.exists(browser_path), "未找到 Chromium 浏览器"
co = ChromiumOptions()
co.set_browser_path(browser_path)

# 添加微信浏览器的 User-Agent
co.set_user_agent("Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16A366 MicroMessenger/7.0.5(0x17000521) NetType/WIFI Language/zh_CN")
co.set_argument("--headless")
# co.set_argument("--no-sandbox")

driver = ChromiumPage(co)
driver.get("https://ecard.csu.edu.cn/plat/login?synAccessSource=h5&loginFrom=h5&type=login")


# 尝试登录
for _ in range(3):
    time.sleep(1)
    morelogin_button = driver.ele("@type=flex")
    morelogin_button.click()
    time.sleep(5)
    cardlogin_button = driver.ele("@type=button", index=3)
    cardlogin_button.click()
    time.sleep(1)
    if is_debug():
        time.sleep(4)
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
time.sleep(5)
driver.get_screenshot(name="login.png")
all_body = driver.ele("@src=https://ecard.csu.edu.cn/minio/theme/76a207a88839430103a509aa3882bde4/images/plat/white/appView/all.png")
all_body.click()
time.sleep(5)
last_body = driver.ele("@src=https://ecard.csu.edu.cn/minio/theme/76a207a88839430103a509aa3882bde4/images/plat/white/appView/electricity.png")
last_body.click()
time.sleep(5)
# 查找class=text-gary的第二个元素提取为文本
remain_class = driver.ele("@class=text-gary", index=2).text
print(remain_class)
# 从"剩余电量: 55.073"字符中保留数字部分
remain = remain_class.split(":")[-1].strip()

try:
    cost = float(remain)
except ValueError:
    log.error(f"余额不是数字: {remain}")
    exit(1)

log.info(cost)
driver.quit()
pushplus(cost, COUNT, GITHUB_TRIGGERING_ACTOR, PUSH_PLUS_TOKEN)
