import os

from DrissionPage import ChromiumOptions, ChromiumPage

from utils import code_input, login, pushplus

path = r"/usr/bin/chromium-browser"  # 请改为你电脑内 Chrome 可执行文件路径
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

# 账号输入
count_input = driver.ele("@type=text")
count_input.input("8212210728")

# 密码输入
pwd_input = driver.ele("@type=password")
pwd_input.input("121517")

code_input(driver)
login(driver)


card_body = driver.ele("css:#cardService > div > div:nth-child(1) > div > div > div")
card_body.click()
remain = driver.ele(".value font-size-18")
cost = remain.text[1:]
print(remain.text[1:])
driver.quit()
pushplus(float(cost), COUNT, GITHUB_TRIGGERING_ACTOR, PUSH_PLUS_TOKEN)
