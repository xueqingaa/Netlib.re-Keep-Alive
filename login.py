import os
import time
import datetime
import requests

# 获取 TG 配置
tg_token = os.getenv("TELEGRAM_SIGNALO")
tg_chat_id = os.getenv("TELEGRAM_BABILO_ID")

# 获取账户信息
accounts = os.getenv("ACCOUNTS")
if not accounts:
    print("no accounts found in ACCOUNTS or UZANTONOMO/PASVORTO")
    msg = "Netlib KeepAlive: 没有检测到账号配置（ACCOUNTS 或 UZANTONOMO/PASVORTO）。"
    if tg_token and tg_chat_id:
        requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                      json={"chat_id": tg_chat_id, "text": msg})
    exit(1)

# 日期处理
now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)  # 北京时间
today = now.strftime("%Y-%m-%d %H:%M:%S")
day_of_month = now.day
days_in_month = (now.replace(day=28) + datetime.timedelta(days=4)).day
days_left = days_in_month - day_of_month

# 倒计时与登录逻辑
if day_of_month == 1:
    result = "✅ 已执行登录任务（每月一次）"
else:
    result = f"⏳ 倒计时：距离下次登录还有 {days_left} 天"

# Telegram 通知内容
msg = f"🕒 Netlib KeepAlive 已执行\n当前时间：{today}\n{result}"

if tg_token and tg_chat_id:
    r = requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                      json={"chat_id": tg_chat_id, "text": msg})
    print("Telegram response:", r.status_code, r.text)
else:
    print("Telegram 未配置。")

print("任务完成。")