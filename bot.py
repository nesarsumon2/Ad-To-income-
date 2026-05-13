"""
Ad To Income Bot
----------------
Telegram bot - /start কমান্ডে স্বাগতম মেসেজ পাঠায়,
পেমেন্ট প্রুফ চ্যানেলের লিঙ্ক ও "ইনকাম শুরু" বাটন দেখায়।

চালানোর আগে:
    pip install python-telegram-bot==21.6

তারপর BOT_TOKEN বসিয়ে:
    python bot.py
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ====== কনফিগারেশন ======
BOT_TOKEN = os.getenv("8778206171:AAH6yoC89bXhmuofyeM-LYk8VXROxff-lnQ", "এখানে_আপনার_BOT_TOKEN_বসান")

CHANNEL_URL = "https://t.me/Ad_To_Income"           # পেমেন্ট প্রুফ / মেইন চ্যানেল
WEBAPP_URL = "https://ad-to-income-bot.lovable.app/"  # ইনকাম শুরু (আপনার অ্যাপ)
ADMIN_IDS = [int(x) for x in os.getenv("6958723400", "").split(",") if x.strip().isdigit()]

WELCOME_TEXT = (
    "👋 *আমাদের ইনকাম Ad To Income Bot এ আপনাকে স্বাগতম!*\n\n"
    "💰 আপনি প্রতিদিন এখান থেকে এড দেখে ইনকাম করতে পারবেন।\n\n"
    "📢 নিচে আমাদের *পেমেন্ট প্রুফ চ্যানেল* আছে — দেখে আসতে পারেন।\n\n"
    "🚀 ইনকাম শুরু করতে নিচের *ইনকাম শুরু* বাটনে ক্লিক করুন।"
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ====== /start হ্যান্ডলার ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    # ইনভাইট/রেফারাল কোড (যদি /start <code> দিয়ে আসে)
    ref_code = context.args[0] if context.args else None
    if ref_code:
        logger.info(f"User {user.id} এসেছে রেফার কোড দিয়ে: {ref_code}")

    keyboard = [
        [InlineKeyboardButton("🚀 ইনকাম শুরু করুন", url=WEBAPP_URL)],
        [InlineKeyboardButton("📢 পেমেন্ট প্রুফ চ্যানেল", url=CHANNEL_URL)],
        [
            InlineKeyboardButton("👤 আমার একাউন্ট", callback_data="account"),
            InlineKeyboardButton("ℹ️ সাহায্য", callback_data="help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=reply_markup,
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


# ====== বাটন ক্লিক হ্যান্ডলার ======
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "account":
        user = query.from_user
        text = (
            f"👤 *আপনার একাউন্ট তথ্য*\n\n"
            f"🆔 ID: `{user.id}`\n"
            f"👤 নাম: {user.full_name}\n"
            f"🔗 ইউজারনেম: @{user.username if user.username else 'নাই'}\n\n"
            f"ইনকাম ড্যাশবোর্ড দেখতে নিচের বাটনে ক্লিক করুন 👇"
        )
        keyboard = [[InlineKeyboardButton("🚀 ড্যাশবোর্ডে যান", url=WEBAPP_URL)]]
        await query.edit_message_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "help":
        text = (
            "ℹ️ *সাহায্য*\n\n"
            "১. 'ইনকাম শুরু করুন' বাটনে ক্লিক করুন\n"
            "২. এড দেখুন এবং পয়েন্ট কামান\n"
            "৩. সর্বনিম্ন উইথড্র হলে পেমেন্ট নিন\n\n"
            "📢 আপডেটের জন্য আমাদের চ্যানেলে যুক্ত থাকুন।"
        )
        keyboard = [[InlineKeyboardButton("📢 চ্যানেলে যান", url=CHANNEL_URL)]]
        await query.edit_message_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# ====== /admin (শুধু এডমিনদের জন্য) ======
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ আপনি এডমিন না।")
        return
    await update.message.reply_text(
        "🛠 *এডমিন প্যানেল*\n\n"
        "আপনার ওয়েব এডমিন প্যানেল:\n"
        f"{WEBAPP_URL}admin",
        parse_mode="Markdown",
    )


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot চালু হয়েছে... ✅")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
