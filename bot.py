import os
import sys
import json
import time
import signal
import asyncio
import aiohttp

from utils.banner import show_banner

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"

MY_PROJECT = "Tac Miniapp"
BASE_URL   = "https://tacairdrop.xyz"
REF_CODE   = "6004380466"


def log_green(msg):
    print(f"{GREEN}{BOLD}{msg}{RESET}", flush=True)


def log_yellow(msg):
    print(f"{YELLOW}{BOLD}{msg}{RESET}", flush=True)


def log_red(msg):
    print(f"{RED}{BOLD}{msg}{RESET}", flush=True)


def signal_handler(sig, frame):
    print()
    log_red("Script stopped by user.")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def normalize_proxy(proxy_line):
    if not proxy_line:
        return None
    value = proxy_line.strip()
    if "://" in value:
        return value
    parts = value.split(":")
    if len(parts) == 4:
        host, port, user, password = parts
        return f"http://{user}:{password}@{host}:{port}"
    if len(parts) == 3:
        host, port, user = parts
        return f"http://{user}@{host}:{port}"
    return f"http://{value}"


def mask_proxy(proxy_url):
    try:
        after_at = proxy_url.split("@")[-1]
        ip_part = after_at.split(":")[0]
        port_part = after_at.split(":")[1] if ":" in after_at else ""
        octets = ip_part.split(".")
        if len(octets) == 4:
            masked_ip = f"{octets[0]}*****{octets[3]}"
            return f"http://user:pass@{masked_ip}:{port_part}"
    except Exception:
        pass
    return "http://user:pass@***:***"


def countdown(seconds, label):
    start = time.time()
    while True:
        remaining = seconds - (time.time() - start)
        if remaining <= 0:
            print(f"\r{' ' * 70}\r", end="", flush=True)
            break
        h = int(remaining // 3600)
        m = int((remaining % 3600) // 60)
        s = int(remaining % 60)
        print(f"\r{YELLOW}{BOLD}{label} {h:02d}:{m:02d}:{s:02d}{RESET}", end="", flush=True)
        time.sleep(1)


def load_config():
    defaults = {"settings": {"sleep_seconds": 3600, "upgrade": True}}
    if not os.path.exists("config.json"):
        return defaults
    try:
        with open("config.json") as f:
            return json.load(f)
    except Exception:
        return defaults


def config_flag(config, key, fallback):
    value = config.get("settings", {}).get(key, fallback)
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "yes", "on", "1"):
        return True
    if text in ("false", "no", "off", "0"):
        return False
    return fallback


def load_accounts():
    if not os.path.exists("data.txt"):
        log_red("File data.txt was not found.")
        sys.exit(1)
    lines = [l.strip() for l in open("data.txt").readlines() if l.strip()]
    if not lines:
        log_red("File data.txt is empty.")
        sys.exit(1)
    return lines


def load_proxies():
    if not os.path.exists("proxy.txt"):
        return []
    try:
        return [l.strip() for l in open("proxy.txt").readlines() if l.strip()]
    except Exception:
        return []


def get_proxy(proxies, idx):
    if not proxies:
        return None
    return proxies[idx % len(proxies)]


def parse_account(line):
    parts = line.strip().split("|")
    init_data = parts[0].strip()
    address = parts[1].strip() if len(parts) > 1 else ""
    user_id = ""
    username = ""
    try:
        from urllib.parse import parse_qs
        raw = (parse_qs(init_data).get("user") or [""])[0]
        if raw:
            info = json.loads(raw)
            user_id = str(info.get("id") or "")
            username = info.get("username") or ""
    except Exception:
        pass
    return init_data, address, user_id, username


def build_headers(init_data):
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "x-telegram-init-data": init_data,
        "origin": BASE_URL,
        "referer": BASE_URL + "/",
        "user-agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36",
    }


async def api_get(session, path, init_data, proxy=None):
    try:
        async with session.get(
            BASE_URL + path,
            headers=build_headers(init_data),
            proxy=proxy,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as r:
            raw = await r.read()
            return r.status, json.loads(raw)
    except Exception as e:
        log_red(f"Request to the server failed: {type(e).__name__}.")
        return None, None


async def api_post(session, path, payload, init_data, proxy=None):
    try:
        async with session.post(
            BASE_URL + path,
            headers=build_headers(init_data),
            json=payload,
            proxy=proxy,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as r:
            raw = await r.read()
            return r.status, json.loads(raw)
    except Exception as e:
        log_red(f"Request to the server failed: {type(e).__name__}.")
        return None, None


def error_text(data):
    if isinstance(data, dict):
        return str(data.get("error") or "")
    return ""


async def read_state(session, init_data, user_id, username, proxy):
    from urllib.parse import urlencode
    query = {"userId": user_id, "ref": REF_CODE}
    if username:
        query["username"] = username
    return await api_get(session, "/api/state?" + urlencode(query), init_data, proxy)


async def verify_user(session, init_data, user_id, proxy):
    status, data = await api_post(session, "/api/user/verify", {"userId": user_id}, init_data, proxy)
    if data and data.get("success"):
        log_green("Account verification is confirmed by the server.")
        return
    reason = error_text(data)
    if reason:
        log_yellow(f"Account verification says: {reason}.")
    else:
        log_yellow("Account verification was refused by the server.")


async def start_mining(session, init_data, user_id, proxy):
    status, data = await api_post(session, "/api/mining/start", {"userId": user_id}, init_data, proxy)
    if data and data.get("success"):
        log_green("Mining session started on this account.")
        return
    reason = error_text(data)
    if reason:
        log_yellow(f"Mining start says: {reason}.")
    else:
        log_yellow("Mining session could not be started.")


async def claim_mining(session, init_data, user_id, proxy):
    status, data = await api_post(session, "/api/mining/claim", {"userId": user_id}, init_data, proxy)
    if data and data.get("success"):
        amount = data.get("claimedAmount")
        log_green(f"Mining reward claimed {amount} TAC.")
        return
    reason = error_text(data)
    if reason:
        log_yellow(f"Mining claim says: {reason}.")
    else:
        log_yellow("Mining reward is not claimable yet.")


async def complete_tasks(session, init_data, user_id, tasks, completed_ids, proxy):
    pending = [t for t in tasks if t.get("active") and t.get("id") not in completed_ids]
    if not pending:
        log_yellow("No task is left to complete on this account.")
        return
    for task in pending:
        title = task.get("title") or "task"
        reward = task.get("rewardAtf") or 0
        status, data = await api_post(
            session,
            "/api/tasks/complete",
            {"userId": user_id, "taskId": task.get("id")},
            init_data,
            proxy,
        )
        if status == 200 and data and data.get("success"):
            log_green(f"Task {title} completed for {reward} TAC.")
            continue
        if status == 403:
            log_yellow(f"Task {title} needs the channel join first.")
            continue
        reason = error_text(data)
        if reason:
            log_yellow(f"Task {title} says: {reason}.")
        else:
            log_red(f"Task {title} could not be completed.")


AD_WINDOW_SECONDS = 21600
AD_WINDOW_MS = AD_WINDOW_SECONDS * 1000
AD_LIMIT_FALLBACK = 5


def plural(count):
    return "view" if int(count) == 1 else "views"


async def watch_ads(session, init_data, user_id, user, settings, proxy):
    limit = max(1, int(settings.get("adsDailyLimit") or AD_LIMIT_FALLBACK))
    watched = int(user.get("adsWatchedToday") or 0)
    window_started = int(user.get("adsWindowStartedAt") or 0)
    if not window_started or int(time.time() * 1000) - window_started >= AD_WINDOW_MS:
        watched = 0
    remaining = max(0, limit - watched)
    if remaining <= 0:
        log_yellow("Every rewarded ad view for this window was already watched.")
        return
    for index in range(remaining):
        status, data = await api_post(session, "/api/ads/watch", {}, init_data, proxy)
        if status == 200 and data and data.get("reward") is not None:
            left = data.get("adsRemaining")
            if left is None:
                left = remaining - index - 1
            log_green(f"Rewarded ad view credited {data.get('reward')} TAC with {left} {plural(left)} left.")
            continue
        reason = error_text(data)
        if reason:
            log_yellow(f"Rewarded ad view says: {reason}.")
        else:
            log_yellow("Rewarded ad view was refused by the server.")
        return


async def claim_referral(session, init_data, user_id, proxy):
    status, data = await api_post(session, "/api/referrals/claim", {"userId": user_id}, init_data, proxy)
    if data and data.get("success"):
        amount = data.get("claimedAmount")
        if amount:
            log_green(f"Referral rewards claimed {amount} TAC.")
        else:
            log_green("Referral rewards claimed on this account.")
        return
    reason = error_text(data)
    if reason:
        log_yellow(f"Referral rewards say: {reason}.")
    else:
        log_yellow("Referral rewards are not claimable on this account.")


async def claim_team(session, init_data, user_id, proxy):
    status, data = await api_post(session, "/api/referrals/claim-team", {"userId": user_id}, init_data, proxy)
    if data and data.get("success"):
        amount = data.get("claimedAmount")
        if amount:
            log_green(f"Team earnings claimed {amount} TAC.")
        else:
            log_green("Team earnings claimed on this account.")
        return
    reason = error_text(data)
    if reason:
        log_yellow(f"Team earnings say: {reason}.")
    else:
        log_yellow("Team earnings are not claimable on this account.")


async def connect_wallet(session, init_data, user_id, address, proxy):
    payload = {"userId": user_id, "address": address, "walletType": "tonconnect"}
    status, data = await api_post(session, "/api/user/connect-wallet", payload, init_data, proxy)
    if data and data.get("success"):
        log_green(f"Wallet {address} is connected to this account.")
        return
    reason = error_text(data)
    if reason:
        log_yellow(f"Wallet connection says: {reason}.")
    else:
        log_yellow("Wallet could not be connected on this account.")


async def upgrade_miner(session, init_data, user_id, level, proxy):
    for _ in range(100):
        status, data = await api_post(
            session,
            "/api/miners/upgrade",
            {"userId": user_id, "targetLevel": level + 1},
            init_data,
            proxy,
        )
        if not (data and data.get("success")):
            reason = error_text(data)
            if reason:
                log_yellow(f"Miner upgrade was refused by the server: {reason}.")
            else:
                log_yellow("Miner upgrade is not available for this account.")
            return
        level = (data.get("user") or {}).get("currentLevel") or level + 1
        log_green(f"Miner level {level} was unlocked on this account.")


async def process_account(init_data, address, user_id, username, proxy, upgrade):
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        status, state = await read_state(session, init_data, user_id, username, proxy)
        if not state or not state.get("currentUser"):
            log_red("Failed to retrieve account state.")
            return

        user = state.get("currentUser", {})
        if user.get("isBanned"):
            log_red("Account is not allowed to run.")
            return

        name = user.get("username") or username or "Unknown"
        log_green(f"Account {name} logged in at level {user.get('currentLevel', 1)}.")
        log_green(f"Account totals {user.get('totalMinedAtf', 0)} TAC mined.")

        if address:
            await connect_wallet(session, init_data, user_id, address, proxy)

        await verify_user(session, init_data, user_id, proxy)
        await start_mining(session, init_data, user_id, proxy)
        await claim_mining(session, init_data, user_id, proxy)
        await complete_tasks(
            session,
            init_data,
            user_id,
            state.get("tasks", []),
            set(user.get("completedTaskIds") or []),
            proxy,
        )
        await watch_ads(
            session,
            init_data,
            user_id,
            user,
            state.get("settings") or {},
            proxy,
        )
        await claim_referral(session, init_data, user_id, proxy)
        await claim_team(session, init_data, user_id, proxy)
        if upgrade:
            await upgrade_miner(
                session, init_data, user_id, user.get("currentLevel", 1), proxy
            )

        status, state = await read_state(session, init_data, user_id, username, proxy)
        user = state.get("currentUser", user) if state else user
        log_green(
            f"Account totals {user.get('totalMinedAtf', 0)} TAC mined "
            f"at level {user.get('currentLevel', 1)}."
        )


async def main_async(accounts, proxies, sleep_secs, upgrade):
    cycle = 1
    while True:
        log_yellow(f"Starting automation cycle number {cycle}.")
        if not upgrade:
            log_yellow("Miner upgrade is switched off in config.json")

        for idx, line in enumerate(accounts):
            if idx > 0:
                print()

            init_data, address, user_id, username = parse_account(line)
            if not init_data or not user_id:
                log_red(f"Credential line {idx + 1} is not valid initData.")
                continue

            proxy_url = normalize_proxy(get_proxy(proxies, idx))
            if proxy_url:
                log_yellow(f"Using proxy {mask_proxy(proxy_url)}.")

            await process_account(
                init_data, address, user_id, username, proxy_url, upgrade
            )

        log_yellow(f"All accounts processed for cycle number {cycle}.")
        countdown(sleep_secs, "Next cycle starts in")
        cycle += 1
        show_banner(MY_PROJECT)


def main():
    show_banner(MY_PROJECT)

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    config = load_config()
    sleep_secs = config.get("settings", {}).get("sleep_seconds", 3600)
    upgrade = config_flag(config, "upgrade", True)
    accounts = load_accounts()
    proxies = load_proxies()
    asyncio.run(main_async(accounts, proxies, sleep_secs, upgrade))


if __name__ == "__main__":
    main()
