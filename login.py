import os
import requests
from datetime import datetime, timedelta
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
        print("Telegram 发送状态:", r.status_code)
    except Exception as e:
        print("发送 Telegram 出错:", e)

# ====== 获取账号列表 ======
accounts = []

ACCOUNTS_SECRET = os.getenv("ACCOUNTS")
if ACCOUNTS_SECRET:
    for line in ACCOUNTS_SECRET.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        username, password = line.split(":", 1)
        accounts.append({"username": username, "password": password})

UZANTONOMO = os.getenv("UZANTONOMO")
PASVORTO = os.getenv("PASVORTO")
if not accounts and UZANTONOMO and PASVORTO:
    accounts.append({"username": UZANTONOMO, "password": PASVORTO})

if not accounts:
    send_telegram("Netlib KeepAlive: 没有检测到账号配置（ACCOUNTS 或 UZANTONOMO/PASVORTO）。")
    raise SystemExit("No accounts found")

# ====== 倒计时逻辑 ======
STATE_FILE = "last_login.txt"
INTERVAL_DAYS = 30  # 每30天登录一次
today = datetime.now().date()

# 读取上次登录日期
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        last_login_str = f.read().strip()
        try:
            last_login = datetime.strptime(last_login_str, "%Y-%m-%d").date()
        except:
            last_login = today - timedelta(days=INTERVAL_DAYS)
else:
    last_login = today - timedelta(days=INTERVAL_DAYS)

days_since = (today - last_login).days
days_left = max(INTERVAL_DAYS - days_since, 0)

# 如果倒计时 > 0，每天只发送倒计时提醒
if days_left > 0:
    send_telegram(f"Netlib KeepAlive: 距离下次登录还有 {days_left} 天 ⏳")
    print(f"距离下次登录还有 {days_left} 天")
    raise SystemExit("倒计时提醒完成，不执行登录")

# ====== 登录函数（示例） ======
def login(username, password):
    # TODO: 替换为真实登录逻辑
    print(f"正在登录账号: {username}")
    sleep(2)  # 模拟登录
    return True  # 模拟登录成功

# ====== 循环每个账号登录 ======
results = []
for acc in accounts:
    user = acc["username"]
    pwd = acc["password"]
    try:
        ok = login(user, pwd)
        if ok:
            msg = f"账号 {user} 登录成功 ✅"
        else:
            msg = f"账号 {user} 登录失败 ❌"
        print(msg)
        results.append(msg)
        sleep(1)
    except Exception as e:
        err_msg = f"账号 {user} 登录异常 ⚠️\n{e}"
        print(err_msg)
        results.append(err_msg)

# ====== 登录完成后发送 TG 消息 ======
send_telegram("Netlib KeepAlive: 执行完成\n" + "\n".join(results))

# ====== 更新最后登录日期 ======
with open(STATE_FILE, "w") as f:
    f.write(today.strftime("%Y-%m-%d"))

# ====== 登录成功后发送下一轮倒计时 ======
send_telegram(f"Netlib KeepAlive: 下一次登录还有 {INTERVAL_DAYS} 天 ⏳")