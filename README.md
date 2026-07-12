# Free Fire Like & Guest API — Telegram Bot

A Telegram bot wrapper around the
[freefire-like-and-guest-api](https://github.com/kaifcodec/freefire-like-and-guest-api)
toolkit. It sends likes to a Free Fire profile using bundled guest accounts,
through simple Telegram commands.

> Original toolkit by **kaifcodec** — licensed under the
> **Protective Source License v1.0 (PSL-1.0)**. Credits and license are retained;
> do not remove them.

## How it works

The bot reuses the original Python modules unchanged:

- `get_jwt.py` — guest auth → JWT
- `encrypt_like_body.py` — protobuf + AES like payload
- `count_likes.py` — account info / like count
- `send_like.py` — per-guest like worker + usage tracking
- `guests_manager/` — captured guest accounts

`bot.py` only provides the Telegram interface and calls into those modules.

## Commands

| Command | Description |
|---------|-------------|
| `/start` / `/help` | Show help |
| `/info <UID> <REGION>` | Show account + current like count |
| `/like <UID> <REGION> [COUNT] [CONCURRENCY]` | Send likes |
| `/guests` | How many guest accounts are loaded |
| `/regions` | List supported regions |

Example:

```
/like 123456789 IND 50 20
```

Sends 50 likes to UID `123456789` on the IND server, 20 concurrent requests.

## Setup

```bash
pip install -r requirements.txt
export FF_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
# optional: restrict to specific users
export FF_ADMIN_ONLY="1"
export FF_ADMINS="123456789,my_bot_owner"
python3 bot.py
```

Get a bot token from [@BotFather](https://t.me/BotFather).

## Notes

- Likes use the guest accounts bundled in `guests_manager/guests_converted.json`.
- One like per guest per target is enforced (24h, stored in `usage_history/`).
- Capturing *new* guest accounts requires a physical Android device + Frida
  (see the original repo). This bot only *sends* likes with existing guests.
- Deploy on any host with Python 3.10+ (Fly.io, a VPS, your Kali box, etc.).
