import os
import datetime
import requests
from playwright.sync_api import sync_playwright

# === Telegram 配置 ===
tg_token = os.getenv("TELEGRAM_SIGNALO")
tg_chat_id = os.getenv("TELEGRAM_BABILO_ID")

# === 账号配置 ===
accounts_raw = os.getenv("ACCOUNTS")
if not accounts_raw:
    msg = "❌ 没有检测到账号配置（ACCOUNTS 未设置）。"
    print(msg)
    if tg_token and tg_chat_id:
        requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                      json={"chat_id": tg_chat_id, "text": msg})
    exit(1)

# ✅ 支持多种分隔（换行或逗号）
accounts = []
for line in accounts_raw.replace(",", "\n").splitlines():
    if ":" in line:
        accounts.append(tuple(line.strip().split(":", 1)))

if not accounts:
    msg = "⚠️ ACCOUNTS 格式错误，请用“账号:密码”一行一个。"
    print(msg)
    if tg_token and tg_chat_id:
        requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                      json={"chat_id": tg_chat_id, "text": msg})
    exit(1)

# === 时间计算 ===
now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)  # 北京时间
today = now.strftime("%Y-%m-%d %H:%M:%S")
day = now.day
# 计算当月天数
next_month = now.replace(day=28) + datetime.timedelta(days=4)
days_in_month = (next_month - datetime.timedelta(days=next_month.day)).day
days_left = days_in_month - day if day < days_in_month else 0

# === 登录函数 ===
def netlib_login(username, password):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.netlib.re/login")
            page.fill("input[name='username']", username)
            page.fill("input[name='password']", password)
            page.click("button[type='submit']")
            page.wait_for_timeout(5000)
            content = page.content()
            browser.close()
            if "Dashboard" in content or "登出" in content or "退出登录" in content:
                return True
            return False
    except Exception as e:
        print(f"Login error for {username}: {e}")
        return False

# === 执行逻辑 ===
text = f"🕒 Netlib KeepAlive 执行于 {today}\n"

if day == 1:
    success_list, fail_list = [], []
    for username, password in accounts:
        ok = netlib_login(username, password)
        if ok:
            success_list.append(username)
        else:
            fail_list.append(username)
    text += "✅ 每月 1 号自动登录任务完成。\n"
    if success_list:
        text += f"登录成功：{', '.join(success_list)}\n"
    if fail_list:
        text += f"登录失败：{', '.join(fail_list)}\n"
    text += f"📆 下次登录还有 {days_in_month - 1} 天。\n"
else:
    text += f"📆 今天非登录日，距离下次登录还有 {days_left} 天。"

# === Telegram 通知 ===
if tg_token and tg_chat_id:
    r = requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                      json={"chat_id": tg_chat_id, "text": text})
    print("Telegram response:", r.status_code, r.text)
else:
    print("未配置 Telegram，跳过通知。")

print("任务完成。")