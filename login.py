#!/usr/bin/env python3
# coding: utf-8
"""
Multi-account keep-alive for netlib.re
Supports ACCOUNTS env var:
- Plain text multiline: username:password per line
- OR JSON array: [{"username":"u1","password":"p1"}, {"username":"u2","password":"p2"}]
Keeps same timing and success/fail detection as original project.
"""

import os
import time
import json
import sys
import traceback
from urllib.parse import quote_plus
# try to import playwright as the original script likely does
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
except Exception as e:
    print("please install playwright and run `playwright install` if needed. error:", e)
    raise

# configuration (same timings as README)
OPEN_WAIT = 5
STEP_WAIT = 2
SUCCESS_STAY = 5

TELEGRAM_TOKEN = os.getenv("TELEGRAM_SIGNALO")  # bot token
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_BABILO_ID")  # chat id to send messages

NETLIB_LOGIN_URL = "https://www.netlib.re/auth/login"

def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured, skipping send:", message)
        return
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        r = requests.post(url, data=payload, timeout=15)
        print("telegram:", r.status_code, r.text)
    except Exception as e:
        print("failed to send telegram:", e)

def parse_accounts_env():
    """
    Parse ACCOUNTS env var.
    Supports:
      1) Multiline plain: each line "username:password"
      2) JSON array: [{"username":"u","password":"p"}, ...]
    Returns list of (username, password)
    """
    acc = os.getenv("ACCOUNTS", "").strip()
    if not acc:
        # fallback to original single-account secrets for compatibility
        u = os.getenv("UZANTONOMO")
        p = os.getenv("PASVORTO")
        if u and p:
            return [(u, p)]
        return []

    # try JSON parse
    try:
        parsed = json.loads(acc)
        if isinstance(parsed, list):
            out = []
            for item in parsed:
                if isinstance(item, dict) and "username" in item and "password" in item:
                    out.append((item["username"], item["password"]))
            if out:
                return out
    except Exception:
        pass

    # treat as multiline username:password
    lines = [ln.strip() for ln in acc.splitlines() if ln.strip()]
    out = []
    for ln in lines:
        if ":" in ln:
            u, p = ln.split(":", 1)
            out.append((u.strip(), p.strip()))
    return out

def login_account(username, password, browser):
    page = None
    try:
        context = browser.new_context()
        page = context.new_page()
        page.goto(NETLIB_LOGIN_URL)
        time.sleep(OPEN_WAIT)

        # assume original page has input names / ids similar to netlib (try common selectors)
        # keep same steps/delays as original script (open->wait->type->click->wait)
        # Try multiple selectors to be robust
        # username input
        try:
            if page.query_selector('input[name="login"]'):
                usr_sel = 'input[name="login"]'
            elif page.query_selector('input[name="username"]'):
                usr_sel = 'input[name="username"]'
            else:
                usr_sel = 'input[type="text"]'
        except Exception:
            usr_sel = 'input[type="text"]'

        # password input
        try:
            if page.query_selector('input[name="password"]'):
                pwd_sel = 'input[name="password"]'
            else:
                pwd_sel = 'input[type="password"]'
        except Exception:
            pwd_sel = 'input[type="password"]'

        # fill and submit
        page.fill(usr_sel, username)
        time.sleep(STEP_WAIT)
        page.fill(pwd_sel, password)
        time.sleep(STEP_WAIT)

        # click login button — try several common selectors
        clicked = False
        for sel in ['button[type="submit"]', 'button#login-button', 'input[type="submit"]', 'button']:
            try:
                btn = page.query_selector(sel)
                if btn:
                    btn.click()
                    clicked = True
                    break
            except Exception:
                continue
        if not clicked:
            # fallback: press Enter in password field
            try:
                page.press(pwd_sel, "Enter")
            except Exception:
                pass

        # wait for navigation / response
        time.sleep(OPEN_WAIT)

        # success criteria (from original README)
        content = page.content()
        if "You are the exclusive owner of the following domains." in content:
            # success
            time.sleep(SUCCESS_STAY)
            return True, "Login successful"
        # detect known failure messages
        for fail_msg in ["Invalid credentials.", "Not connected to server.", "Error with the login: login size should be between 2 and 50 (currently: 1)"]:
            if fail_msg in content:
                return False, f"Login failed: {fail_msg}"
        # otherwise treat as failure, but capture some snippet for debug
        snippet = content[:800].replace("\n", " ")
        return False, f"Login result unclear. Page snippet: {snippet}"
    except PlaywrightTimeoutError as te:
        return False, f"Playwright timeout: {te}"
    except Exception as e:
        return False, f"Exception during login: {e}\n{traceback.format_exc()}"
    finally:
        try:
            if page:
                page.close()
            # context auto closed when browser closed by calling code
        except Exception:
            pass

def main():
    accounts = parse_accounts_env()
    if not accounts:
        print("no accounts found in ACCOUNTS or UZANTONOMO/PASVORTO")
        send_telegram("Netlib KeepAlive: 没有检测到账号配置（ACCOUNTS 或 UZANTONOMO/PASVORTO）。")
        sys.exit(1)

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        for username, password in accounts:
            print(f"=== processing account: {username} ===")
            try:
                ok, msg = login_account(username, password, browser)
            except Exception as e:
                ok = False
                msg = f"Unhandled exception: {e}\n{traceback.format_exc()}"
            status = "SUCCESS" if ok else "FAIL"
            summary = f"Account <{username}> => {status}: {msg}"
            print(summary)
            results.append(summary)
            # send per-account telegram notification (keeps parity with original behavior)
            send_telegram(summary)
            # small gap before next account
            time.sleep(STEP_WAIT)
        try:
            browser.close()
        except Exception:
            pass

    # final summary
    final_msg = "Netlib KeepAlive - summary:\n" + "\n".join(results)
    print(final_msg)
    send_telegram(final_msg)

if __name__ == "__main__":
    main()