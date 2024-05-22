import os
import time

from DrissionPage import ChromiumOptions, ChromiumPage

from utils import code_clear, code_input, login, pushplus

# path = r"/usr/bin/chromium-browser"  # 请改为你电脑内 Chrome 可执行文件路径
path = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
co = ChromiumOptions()
co.set_browser_path(path)
co.set_argument("--headless=new")
co.set_argument("--no-sandbox")
# 创建 driver
driver = ChromiumPage(co)
driver.get("https://ecard.csu.edu.cn/plat-pc/login")

# 从环境变量读取账号密码
COUNT = os.environ["COUNT"]
PWD = os.environ["PWD"]
PUSH_PLUS_TOKEN = os.environ["PUSH_PLUS_TOKEN"]
GITHUB_TRIGGERING_ACTOR = os.environ["GITHUB_TRIGGERING_ACTOR"]
print(COUNT)
print(PWD)
# 账号输入
count_input = driver.ele("@type=text")
count_input.input(COUNT)
# 密码输入
pwd_input = driver.ele("@type=password")
pwd_input.input(PWD)
code_input(driver)
login(driver)

while True:
    time.sleep(1)
    error_message = driver.ele(".el-message__content")
    if error_message:
        code_clear(driver)
        code_input(driver)
        login(driver)
    else:
        break

card_body = driver.ele("css:#cardService > div > div:nth-child(1) > div > div > div")
card_body.click()
remain = driver.ele(".value font-size-18")
cost = remain.text[1:]
print(remain.text[1:])
driver.quit()
pushplus(float(cost), COUNT, GITHUB_TRIGGERING_ACTOR, PUSH_PLUS_TOKEN)
