import os
import logging
from uuid import uuid4
import re

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from translations import translations
from models import setup_db, add_user, get_user_by_id, get_user_by_invite_code, record_invite, is_invite_rewarded, mark_invite_rewarded, save_wallet_address, get_wallet_address
from token_transfer import send_tokens

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
OWNER_WALLET = os.getenv("OWNER_WALLET")

BASE_URL = "https://airdropbot1366-production.up.railway.app"

LANG = "en"
T = translations[LANG]

WALLET_REGEX = r"^0x[a-fA-F0-9]{40}$"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    user = get_user_by_id(user_id)
    if user:
        await context.bot.send_message(chat_id=chat_id, text=T["already_registered"])
        invite_link = f"{BASE_URL}/start?ref={user[1]}"
        await context.bot.send_message(chat_id=chat_id, text=T["usage_info"].format(link=invite_link))
        return

    args = context.args
    inviter_id = None
    if args:
        ref_code = args[0]
        inviter = get_user_by_invite_code(ref_code)
        if inviter and inviter[0] != user_id:
            inviter_id = inviter[0]
        else:
            await context.bot.send_message(chat_id=chat_id, text=T["invalid_invite"])
            inviter_id = None

    new_invite_code = str(uuid4())[:8]

    add_user(user_id, new_invite_code, inviter_id)

    # درخواست آدرس کیف پول از کاربر
    await context.bot.send_message(chat_id=chat_id, text=T["ask_wallet_address"])

async def handle_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if not re.match(WALLET_REGEX, text):
        await context.bot.send_message(chat_id=chat_id, text=T["invalid_wallet"])
        return

    # ذخیره آدرس کیف پول
    save_wallet_address(user_id, text)

    try:
        tx_hash = send_tokens(OWNER_WALLET, text, 500)
        logger.info(f"Sent 500 BJF to {text} for user {user_id}: {tx_hash}")
    except Exception as e:
        logger.error(f"Error sending tokens: {e}")
        await context.bot.send_message(chat_id=chat_id, text=T["send_error"])
        return

    # پاداش دعوت
    user = get_user_by_id(user_id)
    inviter_id = user[2]
    if inviter_id and not is_invite_rewarded(inviter_id, user_id):
        inviter_wallet = get_wallet_address(inviter_id)
        if inviter_wallet:
            try:
                tx_hash = send_tokens(OWNER_WALLET, inviter_wallet, 100)
                mark_invite_rewarded(inviter_id, user_id)
                logger.info(f"Sent 100 BJF invite reward to {inviter_wallet} for inviter {inviter_id}: {tx_hash}")
                await context.bot.send_message(chat_id=inviter_id, text=T["invite_reward"])
            except Exception as e:
                logger.error(f"Error sending invite reward: {e}")

    await context.bot.send_message(chat_id=chat_id, text=T["registration_success"])
    invite_link = f"{BASE_URL}/start?ref={user[1]}"
    await context.bot.send_message(chat_id=chat_id, text=T["usage_info"].format(link=invite_link))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(T["help"])

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sorry, I didn't understand that command.")

def main():
    setup_db()
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_address))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    PORT = int(os.environ.get('PORT', 8443))
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{BASE_URL}/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
