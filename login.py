import os
import requests
from time import sleep

# ====== Telegram 配置 ======
TG_TOKEN = os.getenv("TELEGRAM_SIGNALO")
TG_CHAT_ID = os.getenv("TELEGRAM_BABILO_ID")

def send_telegram(message: str):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("Telegram 配置未找到，跳过发送消息")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT_ID, "text": message}
    try:
        r = requests.post(url, data=data)
        print("Telegram 发送状态:", r.status_code, r.json())
    except Exception as e:
        print("发送 Telegram 出错:", e)

# ====== 获取账号列表 ======
accounts = []

# 优先读取多账号 ACCOUNTS
ACCOUNTS_SECRET = os.getenv("ACCOUNTS")
if ACCOUNTS_SECRET:
    for line in ACCOUNTS_SECRET.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        username, password = line.split(":", 1)
        accounts.append({"username": username, "password": password})

# 如果多账号没设置，再尝试单账号
UZANTONOMO = os.getenv("UZANTONOMO")
PASVORTO = os.getenv("PASVORTO")
if not accounts and UZANTONOMO and PASVORTO:
    accounts.append({"username": UZANTONOMO, "password": PASVORTO})

if not accounts:
    send_telegram("Netlib KeepAlive: 没有检测到账号配置（ACCOUNTS 或 UZANTONOMO/PASVORTO）。")
    raise SystemExit("No accounts found")

# ====== 模拟登录逻辑 ======
def login(username, password):
    # TODO: 替换成你原来的登录代码
    print(f"正在登录账号: {username}")
    sleep(2)  # 模拟登录等待
    success = True  # 模拟登录成功
    return success

# ====== 循环每个账号 ======
for acc in accounts:
    user = acc["username"]
    pwd = acc["password"]
    try:
        ok = login(user, pwd)
        if ok:
            msg = f"Netlib KeepAlive: 账号 {user} 登录成功 ✅"
        else:
            msg = f"Netlib KeepAlive: 账号 {user} 登录失败 ❌"
        print(msg)
        send_telegram(msg)
        sleep(1)  # 每个账号间隔 1 秒
    except Exception as e:
        err_msg = f"Netlib KeepAlive: 账号 {user} 登录异常 ⚠️\n{e}"
        print(err_msg)
        send_telegram(err_msg)