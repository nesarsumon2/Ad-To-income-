from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 ইনকাম শুরু করুন", web_app=WebAppInfo(url="https://your-app.lovable.app"))]])
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 ইনকাম শুরু করুন", web_app=WebAppInfo(url="https://your-app.lovable.app"))]])
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 ইনকাম শুরু করুন", web_app=WebAppInfo(url="https://ad-to-income-bot.lovable.app/"))]])
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 ইনকাম শুরু করুন", web_app=WebAppInfo(url="https://ad-to-income-bot.lovable.app/"))]])
# -*- coding: utf-8 -*-
"""
Ad To Income - Telegram Earning Bot
------------------------------------
Features:
- Referral system (?start=<user_id>)
- Watch Ads to earn (configurable reward)
- Daily Bonus
- Withdraw system (admin approves)
- Required Join Channels
- Full Admin Panel:
    * Change ad reward (বাড়ানো / কমানো)
    * Change referral bonus
    * Change daily bonus
    * Change minimum withdraw
    * Add / Remove forced-join channels
    * Add / Remove admin
    * Broadcast message
    * Stats
    * Approve / Reject withdraw

Requirements:
    pip install python-telegram-bot==20.7

Run:
    python bot.py
"""

import json
import os
import logging
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ============== CONFIG ==============
BOT_TOKEN = "8904470310:AAGRzkrgOQ28lMF-uqfBaMMq6BL5yJZ0TYI"   # @BotFather থেকে নাও
OWNER_ID = 6958723400                    # তোমার Telegram user id (main admin)
BOT_NAME = "Ad To Income"
CURRENCY = "৳"
DATA_FILE = "data.json"
# ====================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(BOT_NAME)


# -------- Storage --------
DEFAULT_DATA = {
    "settings": {
        "ad_reward": 0.50,
        "referral_bonus": 2.00,
        "daily_bonus": 1.00,
        "min_withdraw": 100.00,
        "force_channels": [],   # ["@channelusername", ...]
    },
    "admins": [],               # extra admins (OWNER_ID always admin)
    "users": {},                # uid -> {balance, refs, ref_by, joined, last_daily, last_ad}
    "withdraws": [],            # list of withdraw requests
}


def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return json.loads(json.dumps(DEFAULT_DATA))
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    # backfill defaults
    for k, v in DEFAULT_DATA.items():
        if k not in d:
            d[k] = v
        elif isinstance(v, dict):
            for kk, vv in v.items():
                d[k].setdefault(kk, vv)
    return d


def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


DATA = load_data()


def is_admin(uid: int) -> bool:
    return uid == OWNER_ID or uid in DATA["admins"]


def get_user(uid: int):
    u = DATA["users"].get(str(uid))
    if not u:
        u = {
            "balance": 0.0,
            "refs": 0,
            "ref_by": None,
            "joined": datetime.utcnow().isoformat(),
            "last_daily": None,
            "last_ad": None,
        }
        DATA["users"][str(uid)] = u
        save_data(DATA)
    return u


# -------- Keyboards --------
def main_menu():
    kb = [
        ["📺 Watch Ad", "💰 Balance"],
        ["👥 Refer & Earn", "🎁 Daily Bonus"],
        ["🏧 Withdraw", "📊 Stats"],
        ["ℹ️ Help"],
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


def admin_menu():
    kb = [
        ["💵 Set Ad Reward", "🎁 Set Daily Bonus"],
        ["👥 Set Referral Bonus", "🏧 Set Min Withdraw"],
        ["➕ Add Channel", "➖ Remove Channel"],
        ["📜 Withdraw Requests", "📢 Broadcast"],
        ["👮 Add Admin", "🚫 Remove Admin"],
        ["📈 Bot Stats", "🔙 Main Menu"],
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


# -------- Force Join --------
async def check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chans = DATA["settings"]["force_channels"]
    if not chans:
        return True
    uid = update.effective_user.id
    not_joined = []
    for ch in chans:
        try:
            m = await context.bot.get_chat_member(ch, uid)
            if m.status in ("left", "kicked"):
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)
    if not_joined:
        btns = [
            [InlineKeyboardButton(f"Join {c}", url=f"https://t.me/{c.lstrip('@')}")]
            for c in not_joined
        ]
        btns.append([InlineKeyboardButton("✅ Joined", callback_data="check_join")])
        await update.effective_message.reply_text(
            "👉 প্রথমে নিচের চ্যানেলগুলোতে জয়েন করো:",
            reply_markup=InlineKeyboardMarkup(btns),
        )
        return False
    return True


# -------- Handlers --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)
    args = context.args
    # referral
    if args and user["ref_by"] is None:
        try:
            ref_id = int(args[0])
            if ref_id != uid and str(ref_id) in DATA["users"]:
                user["ref_by"] = ref_id
                referrer = DATA["users"][str(ref_id)]
                referrer["refs"] += 1
                referrer["balance"] += DATA["settings"]["referral_bonus"]
                save_data(DATA)
                try:
                    await context.bot.send_message(
                        ref_id,
                        f"🎉 নতুন রেফার! +{CURRENCY}{DATA['settings']['referral_bonus']:.2f}",
                    )
                except Exception:
                    pass
        except Exception:
            pass

    if not await check_joined(update, context):
        return

    text = (
        f"🤖 *{BOT_NAME}* এ স্বাগতম!\n\n"
        f"📺 অ্যাড দেখে আয় করো\n"
        f"👥 রেফার করে বোনাস নাও\n"
        f"🎁 ডেইলি বোনাস কালেক্ট করো\n\n"
        f"💵 প্রতি অ্যাড: {CURRENCY}{DATA['settings']['ad_reward']:.2f}\n"
        f"👥 রেফার বোনাস: {CURRENCY}{DATA['settings']['referral_bonus']:.2f}\n"
        f"🏧 মিনিমাম উইথড্র: {CURRENCY}{DATA['settings']['min_withdraw']:.2f}"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())


async def check_join_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if await check_joined(update, context):
        await q.message.reply_text("✅ ধন্যবাদ! এখন বট ব্যবহার করতে পারবে।", reply_markup=main_menu())


async def watch_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_joined(update, context):
        return
    uid = update.effective_user.id
    user = get_user(uid)
    now = datetime.utcnow()
    if user["last_ad"]:
        last = datetime.fromisoformat(user["last_ad"])
        if now - last < timedelta(seconds=30):
            wait = 30 - int((now - last).total_seconds())
            await update.message.reply_text(f"⏳ আরো {wait} সেকেন্ড অপেক্ষা করো।")
            return
    # placeholder ad link – replace with your ad network URL
    ad_url = "https://example.com/ad"
    btn = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📺 Open Ad", url=ad_url)],
            [InlineKeyboardButton("✅ I Watched", callback_data="ad_done")],
        ]
    )
    await update.message.reply_text(
        f"📺 অ্যাড দেখো এবং কনফার্ম করো।\n💵 রিওয়ার্ড: {CURRENCY}{DATA['settings']['ad_reward']:.2f}",
        reply_markup=btn,
    )


async def ad_done_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    user = get_user(uid)
    user["balance"] += DATA["settings"]["ad_reward"]
    user["last_ad"] = datetime.utcnow().isoformat()
    save_data(DATA)
    await q.edit_message_text(
        f"✅ +{CURRENCY}{DATA['settings']['ad_reward']:.2f} যোগ হয়েছে!\n"
        f"💰 ব্যালেন্স: {CURRENCY}{user['balance']:.2f}"
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    await update.message.reply_text(
        f"💰 ব্যালেন্স: {CURRENCY}{user['balance']:.2f}\n👥 রেফার: {user['refs']}"
    )


async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)
    me = await context.bot.get_me()
    link = f"https://t.me/{me.username}?start={uid}"
    await update.message.reply_text(
        f"👥 *Refer & Earn*\n\n"
        f"প্রতি রেফারে: {CURRENCY}{DATA['settings']['referral_bonus']:.2f}\n"
        f"তোমার রেফার: {user['refs']}\n\n"
        f"🔗 তোমার লিংক:\n{link}",
        parse_mode="Markdown",
    )


async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    now = datetime.utcnow()
    if user["last_daily"]:
        last = datetime.fromisoformat(user["last_daily"])
        if now - last < timedelta(hours=24):
            left = timedelta(hours=24) - (now - last)
            h = left.seconds // 3600
            m = (left.seconds % 3600) // 60
            await update.message.reply_text(f"⏳ পরবর্তী ডেইলি বোনাস: {h}h {m}m পরে")
            return
    user["balance"] += DATA["settings"]["daily_bonus"]
    user["last_daily"] = now.isoformat()
    save_data(DATA)
    await update.message.reply_text(
        f"🎁 ডেইলি বোনাস +{CURRENCY}{DATA['settings']['daily_bonus']:.2f}!\n"
        f"💰 ব্যালেন্স: {CURRENCY}{user['balance']:.2f}"
    )


async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    minw = DATA["settings"]["min_withdraw"]
    if user["balance"] < minw:
        await update.message.reply_text(
            f"❌ মিনিমাম উইথড্র {CURRENCY}{minw:.2f}\nতোমার ব্যালেন্স: {CURRENCY}{user['balance']:.2f}"
        )
        return
    context.user_data["state"] = "wd_method"
    await update.message.reply_text(
        "🏧 পেমেন্ট মেথড লিখো (Bkash / Nagad / Rocket):"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    await update.message.reply_text(
        f"📊 *তোমার পরিসংখ্যান*\n\n"
        f"💰 ব্যালেন্স: {CURRENCY}{user['balance']:.2f}\n"
        f"👥 রেফার: {user['refs']}\n"
        f"📅 জয়েন: {user['joined'][:10]}",
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Help*\n\n"
        "• 📺 Watch Ad – অ্যাড দেখে আয় করো\n"
        "• 👥 Refer – বন্ধুদের ইনভাইট করো\n"
        "• 🎁 Daily – প্রতিদিন বোনাস\n"
        "• 🏧 Withdraw – টাকা তুলে নাও\n\n"
        "Admin: /admin",
        parse_mode="Markdown",
    )


# -------- Admin --------
async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("🛠 Admin Panel", reply_markup=admin_menu())


async def admin_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin button presses + state-based input + user withdraw flow."""
    uid = update.effective_user.id
    text = (update.message.text or "").strip()
    state = context.user_data.get("state")

    # ---------- user withdraw flow ----------
    if state == "wd_method":
        context.user_data["wd_method"] = text
        context.user_data["state"] = "wd_number"
        await update.message.reply_text("📱 অ্যাকাউন্ট নাম্বার দাও:")
        return
    if state == "wd_number":
        context.user_data["wd_number"] = text
        context.user_data["state"] = "wd_amount"
        await update.message.reply_text(
            f"💵 কত টাকা তুলতে চাও? (min {CURRENCY}{DATA['settings']['min_withdraw']:.2f})"
        )
        return
    if state == "wd_amount":
        try:
            amt = float(text)
        except ValueError:
            await update.message.reply_text("❌ সঠিক সংখ্যা দাও")
            return
        user = get_user(uid)
        if amt < DATA["settings"]["min_withdraw"] or amt > user["balance"]:
            await update.message.reply_text("❌ ইনভ্যালিড অ্যামাউন্ট")
            context.user_data.clear()
            return
        user["balance"] -= amt
        req = {
            "id": len(DATA["withdraws"]) + 1,
            "uid": uid,
            "method": context.user_data["wd_method"],
            "number": context.user_data["wd_number"],
            "amount": amt,
            "status": "pending",
            "time": datetime.utcnow().isoformat(),
        }
        DATA["withdraws"].append(req)
        save_data(DATA)
        context.user_data.clear()
        await update.message.reply_text(
            f"✅ রিকোয়েস্ট পাঠানো হয়েছে! ID #{req['id']}\nএডমিন এপ্রুভ করলে পেয়ে যাবে।"
        )
        # notify admins
        msg = (
            f"🆕 Withdraw #{req['id']}\n"
            f"User: `{uid}`\n"
            f"Method: {req['method']}\n"
            f"Number: {req['number']}\n"
            f"Amount: {CURRENCY}{amt:.2f}"
        )
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"wd_ok_{req['id']}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"wd_no_{req['id']}"),
                ]
            ]
        )
        for a in [OWNER_ID, *DATA["admins"]]:
            try:
                await context.bot.send_message(a, msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                pass
        return

    # ---------- admin states ----------
    if not is_admin(uid):
        return

    if state == "set_ad":
        DATA["settings"]["ad_reward"] = float(text); save_data(DATA)
        context.user_data.clear()
        await update.message.reply_text(f"✅ Ad reward = {CURRENCY}{float(text):.2f}", reply_markup=admin_menu()); return
    if state == "set_daily":
        DATA["settings"]["daily_bonus"] = float(text); save_data(DATA)
        context.user_data.clear()
        await update.message.reply_text(f"✅ Daily bonus = {CURRENCY}{float(text):.2f}", reply_markup=admin_menu()); return
    if state == "set_ref":
        DATA["settings"]["referral_bonus"] = float(text); save_data(DATA)
        context.user_data.clear()
        await update.message.reply_text(f"✅ Referral bonus = {CURRENCY}{float(text):.2f}", reply_markup=admin_menu()); return
    if state == "set_min":
        DATA["settings"]["min_withdraw"] = float(text); save_data(DATA)
        context.user_data.clear()
        await update.message.reply_text(f"✅ Min withdraw = {CURRENCY}{float(text):.2f}", reply_markup=admin_menu()); return
    if state == "add_ch":
        ch = text if text.startswith("@") else "@" + text
        if ch not in DATA["settings"]["force_channels"]:
            DATA["settings"]["force_channels"].append(ch); save_data(DATA)
        context.user_data.clear()
        await update.message.reply_text(f"✅ Channel added: {ch}", reply_markup=admin_menu()); return
    if state == "rm_ch":
        ch = text if text.startswith("@") else "@" + text
        if ch in DATA["settings"]["force_channels"]:
            DATA["settings"]["force_channels"].remove(ch); save_data(DATA)
        context.user_data.clear()
        await update.message.reply_text(f"✅ Channel removed: {ch}", reply_markup=admin_menu()); return
    if state == "add_admin":
        try:
            nid = int(text)
            if nid not in DATA["admins"]:
                DATA["admins"].append(nid); save_data(DATA)
            await update.message.reply_text(f"✅ Admin added: {nid}", reply_markup=admin_menu())
        except ValueError:
            await update.message.reply_text("❌ Invalid id")
        context.user_data.clear(); return
    if state == "rm_admin":
        try:
            nid = int(text)
            if nid in DATA["admins"]:
                DATA["admins"].remove(nid); save_data(DATA)
            await update.message.reply_text(f"✅ Admin removed: {nid}", reply_markup=admin_menu())
        except ValueError:
            await update.message.reply_text("❌ Invalid id")
        context.user_data.clear(); return
    if state == "broadcast":
        sent = 0
        for u in list(DATA["users"].keys()):
            try:
                await context.bot.send_message(int(u), text)
                sent += 1
            except Exception:
                pass
        context.user_data.clear()
        await update.message.reply_text(f"📢 Sent to {sent} users", reply_markup=admin_menu()); return

    # ---------- admin button presses ----------
    if text == "💵 Set Ad Reward":
        context.user_data["state"] = "set_ad"
        await update.message.reply_text("নতুন অ্যাড রিওয়ার্ড লিখো (e.g. 0.5):"); return
    if text == "🎁 Set Daily Bonus":
        context.user_data["state"] = "set_daily"
        await update.message.reply_text("নতুন ডেইলি বোনাস:"); return
    if text == "👥 Set Referral Bonus":
        context.user_data["state"] = "set_ref"
        await update.message.reply_text("নতুন রেফার বোনাস:"); return
    if text == "🏧 Set Min Withdraw":
        context.user_data["state"] = "set_min"
        await update.message.reply_text("নতুন মিনিমাম উইথড্র:"); return
    if text == "➕ Add Channel":
        context.user_data["state"] = "add_ch"
        await update.message.reply_text("চ্যানেল ইউজারনেম (@channel):"); return
    if text == "➖ Remove Channel":
        context.user_data["state"] = "rm_ch"
        await update.message.reply_text("কোন চ্যানেল রিমুভ করবে? (@channel):"); return
    if text == "👮 Add Admin":
        context.user_data["state"] = "add_admin"
        await update.message.reply_text("নতুন এডমিন user id:"); return
    if text == "🚫 Remove Admin":
        context.user_data["state"] = "rm_admin"
        await update.message.reply_text("কোন এডমিন রিমুভ করবে? user id:"); return
    if text == "📢 Broadcast":
        context.user_data["state"] = "broadcast"
        await update.message.reply_text("ব্রডকাস্ট মেসেজ লিখো:"); return
    if text == "📜 Withdraw Requests":
        pend = [w for w in DATA["withdraws"] if w["status"] == "pending"]
        if not pend:
            await update.message.reply_text("কোনো পেন্ডিং রিকোয়েস্ট নেই।"); return
        for w in pend[-10:]:
            kb = InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("✅", callback_data=f"wd_ok_{w['id']}"),
                    InlineKeyboardButton("❌", callback_data=f"wd_no_{w['id']}"),
                ]]
            )
            await update.message.reply_text(
                f"#{w['id']} | {w['method']} | {w['number']}\n"
                f"User: {w['uid']} | {CURRENCY}{w['amount']:.2f}",
                reply_markup=kb,
            )
        return
    if text == "📈 Bot Stats":
        total = len(DATA["users"])
        bal = sum(u["balance"] for u in DATA["users"].values())
        wd = len([w for w in DATA["withdraws"] if w["status"] == "paid"])
        await update.message.reply_text(
            f"📈 *Stats*\n\n"
            f"👤 Users: {total}\n"
            f"💰 Total balance: {CURRENCY}{bal:.2f}\n"
            f"✅ Paid withdraws: {wd}\n"
            f"📺 Ad reward: {CURRENCY}{DATA['settings']['ad_reward']:.2f}\n"
            f"👥 Ref bonus: {CURRENCY}{DATA['settings']['referral_bonus']:.2f}\n"
            f"🎁 Daily: {CURRENCY}{DATA['settings']['daily_bonus']:.2f}\n"
            f"🏧 Min WD: {CURRENCY}{DATA['settings']['min_withdraw']:.2f}\n"
            f"📢 Channels: {', '.join(DATA['settings']['force_channels']) or 'None'}",
            parse_mode="Markdown",
        ); return
    if text == "🔙 Main Menu":
        await update.message.reply_text("Main menu", reply_markup=main_menu()); return


async def wd_action_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not is_admin(q.from_user.id):
        await q.answer("Not admin", show_alert=True); return
    await q.answer()
    _, action, wid = q.data.split("_")
    wid = int(wid)
    req = next((w for w in DATA["withdraws"] if w["id"] == wid), None)
    if not req or req["status"] != "pending":
        await q.edit_message_text("Already processed."); return
    if action == "ok":
        req["status"] = "paid"
        try:
            await context.bot.send_message(
                req["uid"],
                f"✅ Withdraw #{wid} approved!\n{CURRENCY}{req['amount']:.2f} পাঠানো হয়েছে {req['method']} ({req['number']})",
            )
        except Exception:
            pass
        await q.edit_message_text(f"✅ Approved #{wid}")
    else:
        req["status"] = "rejected"
        # refund
        u = DATA["users"].get(str(req["uid"]))
        if u:
            u["balance"] += req["amount"]
        try:
            await context.bot.send_message(
                req["uid"], f"❌ Withdraw #{wid} রিজেক্ট করা হয়েছে। টাকা ফেরত দেয়া হয়েছে।"
            )
        except Exception:
            pass
        await q.edit_message_text(f"❌ Rejected #{wid}")
    save_data(DATA)


# -------- Text router --------
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    mapping = {
        "📺 Watch Ad": watch_ad,
        "💰 Balance": balance,
        "👥 Refer & Earn": refer,
        "🎁 Daily Bonus": daily,
        "🏧 Withdraw": withdraw,
        "📊 Stats": stats,
        "ℹ️ Help": help_cmd,
    }
    if text in mapping:
        await mapping[text](update, context); return
    # fallback to admin/state router
    await admin_text_router(update, context)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("refer", refer))
    app.add_handler(CallbackQueryHandler(check_join_cb, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(ad_done_cb, pattern="^ad_done$"))
    app.add_handler(CallbackQueryHandler(wd_action_cb, pattern="^wd_(ok|no)_\\d+$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    log.info("%s started.", BOT_NAME)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
