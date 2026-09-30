<div align="center">

<img width="100%" alt="header" src="https://capsule-render.vercel.app/api?type=waving&height=210&text=TAC%20AirDrop%20Bot&fontAlign=50&fontAlignY=36&fontSize=56&desc=Mining%7CTasks%7CReferral%7CMulti%20Account%7CCountdown"/>

<img alt="typing" src="https://readme-typing-svg.demolab.com?font=Inter&size=18&duration=3000&pause=650&center=true&vCenter=true&width=900&lines=Full%20daily%20cycle%20automation%20for%20the%20TAC%20AirDrop%20Miniapp;The%20account%20state%20is%20read%20first%20so%20every%20line%20comes%20from%20the%20server;Mining%20is%20started%20and%20the%20accrued%20reward%20is%20claimed%20on%20every%20cycle;Tasks%20and%20referral%20rewards%20are%20processed%20in%20the%20same%20run;Multi%20account%20with%20proxy%20support%20and%20a%20live%20countdown%20between%20cycles"/>

<p>
  <img alt="python" src="https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white"/>
  <img alt="platform" src="https://img.shields.io/badge/Platform-TAC%20AirDrop%20Miniapp-111111"/>
  <img alt="multi-account" src="https://img.shields.io/badge/Multi--Account-Supported-111111"/>
  <img alt="proxy" src="https://img.shields.io/badge/Proxy-Supported-111111"/>
  <img alt="author" src="https://img.shields.io/badge/by-Yuurisandesu-111111"/>
</p>

<p>
  <b>TAC AirDrop Bot</b> is a full automation bot for the TAC AirDrop Telegram Miniapp.<br/>
  It runs the complete free daily cycle: the account state is read first, the account is verified, a mining session is started and the accrued reward is claimed, every open task is completed and the referral and team rewards are claimed. Every credited amount is printed only after the server confirms it, and all accounts run one after another with proxy support and a live countdown between cycles.<br/>
  Built and distributed by <b>Yuurisandesu</b>.
</p>

</div>

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Bot](#running-the-bot)
- [Features](#features)
- [File Structure](#file-structure)
- [Disclaimer](#disclaimer)

---

## Requirements

- Python `3.8+`
- Git

---

## Installation

**Clone the repository:**

```bash
git clone https://github.com/Yuurisan-N1/Tac-Miniapp.git
cd Tac-Miniapp
```

**Install dependencies:**

```bash
pip install aiohttp yuurisan
```

---

## Configuration

### 1. Accounts (data.txt)

Fill `data.txt` with one account per line. Each line is the full initData string of the account:

```
query_id=AAH...&user=%7B%22id%22%3A7113873680...&auth_date=1759...&hash=9f2c...
query_id=AAH...&user=%7B%22id%22%3A6004380466...&auth_date=1759...&hash=c41a...
```

> The initData string is taken from the Miniapp itself; the bot reads the Telegram user id out of it. The Telegram user id is not typed in by hand.

### 2. Proxy (proxy.txt)

Fill `proxy.txt` with proxies, one per line (optional, leave empty to run without proxy):

```
host:port
host:port:user:pass
http://user:pass@host:port
```

Proxies are assigned to accounts by index in round-robin order.

### 3. Bot Settings (config.json)

`sleep_seconds` controls how many seconds the bot waits between cycles. If `config.json` is missing, it is created automatically with a default of `3600` seconds.

---

## Running the Bot

```bash
python bot.py
```

Press `Ctrl+C` at any time to stop the bot cleanly.

---

## Features

### Account State

Every credential line is sent on the account state call, and the bot prints the account name, its level, and its total mined amount exactly as the server returns them. A line that holds no valid initData is reported in red, and an account the server marks as restricted is skipped for that cycle.

### Account Verification

The verification call is made on every cycle and the answer from the server is reported. A refused answer is printed in yellow with the reason string the server sent back.

### Mining

A mining session is started on every cycle and the accrued reward is claimed right after it. The claimed amount is printed only when the server answers with the credited value, and any other answer is reported with the reason string the server sent back.

### Tasks

Every active task that is still open on the account is completed in the same run. A task that is credited is printed in green with its reward, a task that still needs a channel join is reported in yellow, and any other answer is reported with the reason string the server sent back.

### Referral And Team Rewards

The referral reward claim and the team earning claim are both called on every cycle. A claim that is credited is printed in green, and an account with nothing to claim is reported in yellow with the reason string the server sent back.

### Account Summary

After the calls, the account state is read one more time and the closing line prints the total mined amount and the current level of the account.

### Multi Account

All accounts in `data.txt` are processed one after another in the order they are listed within every cycle. The cycle number is logged at the start of each round.

### Proxy Support

Proxies are loaded from `proxy.txt` and assigned to accounts by position in round-robin order. Proxy credentials are masked in log output. Running without proxies is fully supported.

### Auto Countdown

After all accounts complete a cycle, the bot displays a live `HH:MM:SS` countdown until the next cycle starts.

---

## File Structure

```text
TACAirDrop-Miniapp/
├── bot.py          # Main bot, full daily cycle automation
├── config.json     # Sleep duration between cycles
├── data.txt        # Account initData strings, one per line
├── proxy.txt       # Proxy list, one per line (optional)
├── LICENSE         # License file
├── README.md       # This documentation
└── utils/
    └── banner.py   # Banner using yuurisan module
```

---

## Disclaimer

This tool is built for educational and technical exploration purposes. Use it wisely and at your own responsibility.

---

<div align="center">
<img width="100%" alt="footer" src="https://capsule-render.vercel.app/api?type=waving&height=120&section=footer"/>
</div>
