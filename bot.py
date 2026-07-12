#!/usr/bin/env python3
"""
Free Fire Like & Guest API — Telegram Bot wrapper
==================================================

This bot wraps the original Free Fire like-sending toolkit
(kaifcodec/freefire-like-and-guest-api) and exposes it through Telegram.

It reuses the original modules unchanged:
  - get_jwt.py          (guest auth -> JWT)
  - encrypt_like_body.py (protobuf + AES like payload)
  - count_likes.py       (account info / like count)
  - send_like.py         (per-guest like worker + usage tracking)
  - guests_manager/      (captured guest accounts)

The like-sending engine lives in `send_like.py`; this file only provides
the Telegram interface and calls into it.

Original toolkit:  https://github.com/kaifcodec/freefire-like-and-guest-api
License:           Protective Source License v1.0 (PSL-1.0) — credits retained.
"""

import asyncio
import os
import sys
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Make sure the original modules (in this same folder) are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import send_like as engine            # the original like engine
from count_likes import GetAccountInformation, SUPPORTED_REGIONS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("ff_bot")

BOT_TOKEN = os.environ.get("FF_BOT_TOKEN", "").strip()
ADMIN_ONLY = os.environ.get("FF_ADMIN_ONLY", "1").strip() == "1"
ADMINS = {u.strip() for u in os.environ.get("FF_ADMINS", "").split(",") if u.strip()}

# Per-chat "currently sending" lock so two /like calls don't overlap
_busy = {}

HELP = (
    "🔥 *Free Fire Like Bot*\n\n"
    "Commands:\n"
    "/start - welcome\n"
    "/help - this message\n"
    "/info <UID> <REGION> - show account + current like count\n"
    "   example: `/info 123456789 IND`\n"
    "/like <UID> <REGION> [COUNT] [CONCURRENCY] - send likes\n"
    "   example: `/like 123456789 IND 50 20`\n"
    "/guests - how many guest accounts are loaded\n"
    "/regions - list supported regions\n\n"
    "Supported regions: " + ", ".join(SUPPORTED_REGIONS) + "\n\n"
    "Note: likes use the guest accounts bundled in guests\\_manager/. "
    "One like per guest per target (24h)."
)


def _allowed(update: Update) -> bool:
    if not ADMIN_ONLY:
        return True
    if not ADMINS:
        return True  # no admins configured -> allow everyone
    user = update.effective_user
    return bool(user and str(user.id) in ADMINS) or bool(user and user.username in ADMINS)


async def _denied(update: Update) -> None:
    await update.message.reply_text("⛔ This bot is restricted to authorized users.")


async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update):
        return await _denied(update)
    await update.message.reply_text(HELP, parse_mode="Markdown")


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update):
        return await _denied(update)
    await update.message.reply_text(HELP, parse_mode="Markdown")


async def regions_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update):
        return await _denied(update)
    await update.message.reply_text("Supported regions:\n" + ", ".join(SUPPORTED_REGIONS))


async def guests_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update):
        return await _denied(update)
    try:
        from guests_manager.count_guest import count
        n = count()
    except Exception:
        n = "?"
    await update.message.reply_text(f"👥 Guest accounts loaded: {n}")


async def info_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update):
        return await _denied(update)
    args = ctx.args
    if len(args) < 2:
        return await update.message.reply_text("Usage: /info <UID> <REGION>\nExample: /info 123456789 IND")
    uid = args[0].strip()
    region = args[1].strip().upper()
    if region not in SUPPORTED_REGIONS:
        return await update.message.reply_text(f"Unsupported region. Use one of: {', '.join(SUPPORTED_REGIONS)}")
    await update.message.reply_text(f"🔎 Fetching info for {uid} ({region})...")
    try:
        info = await GetAccountInformation(uid, "0", region, engine.endpoint)
        if info.get("error"):
            return await update.message.reply_text(f"❌ {info.get('message')}")
        basic = info.get("basicInfo", {})
        name = basic.get("nickname", "Unknown")
        likes = basic.get("liked", 0)
        level = basic.get("level", 0)
        await update.message.reply_text(
            f"👤 *{name}*\nUID: `{uid}`\nRegion: {region}\nLevel: {level}\n❤️ Likes: {likes}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def like_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update):
        return await _denied(update)

    chat_id = update.effective_chat.id
    if _busy.get(chat_id):
        return await update.message.reply_text("⏳ A like job is already running in this chat. Please wait.")
    _busy[chat_id] = True

    try:
        args = ctx.args
        if len(args) < 2:
            return await update.message.reply_text(
                "Usage: /like <UID> <REGION> [COUNT] [CONCURRENCY]\nExample: /like 123456789 IND 50 20"
            )
        uid = args[0].strip()
        region = args[1].strip().upper()
        count_req = int(args[2]) if len(args) > 2 else 100
        concurrency = int(args[3]) if len(args) > 3 else 20

        if region not in SUPPORTED_REGIONS:
            return await update.message.reply_text(
                f"Unsupported region. Use one of: {', '.join(SUPPORTED_REGIONS)}"
            )

        await update.message.reply_text(
            f"🔥 Preparing to like `{uid}` ({region}) — {count_req} likes @ concurrency {concurrency}...",
            parse_mode="Markdown",
        )

        # Reuse the original engine's worker + helpers directly.
        BASE_URL = engine.get_base_url(region)
        engine.ensure_target(uid)
        with open(engine.guests_file, "r") as f:
            guests = __import__("json").load(f)

        available = [g for g in guests if not engine.guest_used_for_target(uid, str(g["uid"]))]
        if not available:
            return await update.message.reply_text("⚠️ No unused guest accounts left for this target.")

        planned = min(max(0, count_req), len(available))
        sem = asyncio.Semaphore(max(1, concurrency))

        # Optional: show before count
        try:
            before = await GetAccountInformation(uid, "0", region, engine.endpoint)
            before_likes = before.get("basicInfo", {}).get("liked", 0)
        except Exception:
            before_likes = None

        await update.message.reply_text(
            f"🚀 Sending {planned} likes using {planned} guest accounts..."
        )

        tasks = [engine.like_with_guest(g, uid, BASE_URL, sem) for g in available[:planned]]
        results = await asyncio.gather(*tasks)
        engine.save_usage()

        success = sum(1 for r in results if r)

        after_msg = ""
        try:
            after = await GetAccountInformation(uid, "0", region, engine.endpoint)
            after_likes = after.get("basicInfo", {}).get("liked", 0)
            after_msg = f"\n❤️ Likes now: {after_likes}"
            if before_likes is not None:
                after_msg += f" ( +{after_likes - before_likes} )"
        except Exception:
            pass

        await update.message.reply_text(
            f"✅ Done! Success: {success}/{planned}{after_msg}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        _busy[chat_id] = False


def main() -> None:
    if not BOT_TOKEN:
        sys.exit("❌ Set the FF_BOT_TOKEN environment variable (your Telegram bot token).")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("regions", regions_cmd))
    app.add_handler(CommandHandler("guests", guests_cmd))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("like", like_cmd))
    log.info("Free Fire Like Telegram bot started.")
    app.run_polling()


if __name__ == "__main__":
    main()
