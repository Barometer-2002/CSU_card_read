import re
import os
import ddddocr
import time
from playwright.sync_api import Playwright, sync_playwright

from utils import pushplus



# 使用playwright登录并获取数据,并推送消息
def run(playwright: Playwright) -> None:
    # 从环境变量读取账号密码
    COUNT = os.environ["COUNT"]
    PWD = os.environ["PWD"]
    PUSH_PLUS_TOKEN = os.environ.get("PUSH_PLUS_TOKEN")
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16A366 MicroMessenger/7.0.5(0x17000521) NetType/WIFI Language/zh_CN", viewport={"width":390,"height":844})
    page = context.new_page()
    page.goto("https://ecard.csu.edu.cn/plat/login?synAccessSource=h5&loginFrom=h5&type=login")
    page.get_by_text("更多登录方式").click()
    page.get_by_role("button", name="校园卡账号登录").click()
    page.get_by_placeholder("请输入校园卡账号").fill(COUNT)
    page.get_by_placeholder("请输入一卡通查询密码").fill(PWD)
    # 保存验证码图片
    page.locator('.van-image__img').screenshot(path="code.png")
    # 使用ddddorc识别保存的图片
    ocr = ddddocr.DdddOcr(show_ad=False)
    with open("code.png", "rb") as f:
        code = ocr.classification(f.read())
    print(f'识别到的验证码：{code}')
    # 输入验证码
    page.get_by_placeholder("请输入验证码").fill(code)
    page.get_by_role("button", name="登录").click()
    page.locator("div:nth-child(7) > .van-grid-item__content > .van-grid-item__icon-wrapper > .grid-icon-box > .s-icon > .van-image__img").click()
    time.sleep(1)
    page.locator("div").filter(has_text=re.compile(r"^代充值图书馆缴费校园卡资金转银行宿舍缴电费校本部和铁道10\.11舍宿舍缴费$")).get_by_role("img").nth(4).click()
    # 获取余额文本
    time.sleep(1)
    balance = page.locator('p.text-gary:has-text("剩余电量") span:nth-child(2)').inner_text()
    # 从字符中保留数据部分
    remain = balance.split(":")[-1].strip()
    print(f"余额：{remain}")
    cost = float(remain)
    # 通过pushplus推送消息
    pushplus(cost, COUNT, PUSH_PLUS_TOKEN)
    
    # ---------------------
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)





