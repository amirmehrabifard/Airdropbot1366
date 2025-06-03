import os
import json
from flask import Flask, request
import telebot
from telebot import types
from web3 import Web3
from languages import get_text

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PRIVATE_KEY = os.environ.get("PRIVATE_KEY")
RPC_URL = os.environ.get("RPC_URL")
PORT = int(os.environ.get("PORT", 8000))

CHANNEL_USERNAME = "benjaminfranklintoken"
CONTRACT_ADDRESS = Web3.to_checksum_address("0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181")
AIRDROP_WALLET = Web3.to_checksum_address("0x6CE41726a93445750788f7e65A2bc81E95B700aE")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
with open("abi.json") as f:
    abi = json.load(f)
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# اطلاعات کاربران به صورت فایل
DATA_FILE = "users.json"

def load_users():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

users = load_users()

@app.route("/")
def index():
    return "✅ Bot is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_json())
    bot.process_new_updates([update])
    return "ok", 200

@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = str(message.from_user.id)
    lang = message.from_user.language_code or "en"
    ref = message.text.split(" ")[-1] if len(message.text.split(" ")) > 1 else None

    if user_id not in users:
        users[user_id] = {"joined": False, "wallet": None, "invited_by": ref, "referrals": []}
        save_users(users)

    text = get_text("welcome", lang).format(channel=CHANNEL_USERNAME)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(get_text("joined_btn", lang), url=f"https://t.me/{CHANNEL_USERNAME}"))
    markup.add(types.InlineKeyboardButton(get_text("check_btn", lang), callback_data="check"))
    bot.send_message(user_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "check")
def check_joined(call):
    user_id = str(call.from_user.id)
    lang = call.from_user.language_code or "en"
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", call.from_user.id)
        if member.status in ["member", "administrator", "creator"]:
            if not users[user_id]["joined"]:
                users[user_id]["joined"] = True
                reward_tokens(user_id, 500)

                inviter = users[user_id].get("invited_by")
                if inviter and inviter in users:
                    users[inviter]["referrals"].append(user_id)
                    reward_tokens(inviter, 100)

                save_users(users)
                bot.send_message(user_id, get_text("joined_success", lang))
                bot.send_message(user_id, get_text("ask_wallet", lang))
        else:
            bot.send_message(user_id, get_text("not_joined", lang))
    except Exception as e:
        print(f"❌ Error checking join status: {e}")
        bot.send_message(user_id, "خطا در بررسی عضویت.")

@bot.message_handler(func=lambda m: Web3.is_checksum_address(m.text))
def save_wallet(message):
    user_id = str(message.from_user.id)
    lang = message.from_user.language_code or "en"

    if users[user_id].get("wallet") is None:
        users[user_id]["wallet"] = Web3.to_checksum_address(message.text)
        save_users(users)
        bot.send_message(user_id, get_text("wallet_saved", lang))

@bot.message_handler(commands=["link"])
def referral_link(message):
    user_id = str(message.from_user.id)
    lang = message.from_user.language_code or "en"
    link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(user_id, get_text("referral_link", lang) + link)

def reward_tokens(user_id, amount):
    try:
        to_address = users[user_id].get("wallet")
        if not to_address:
            return

        nonce = w3.eth.get_transaction_count(AIRDROP_WALLET)
        tx = contract.functions.transfer(
            to_address,
            amount * (10 ** contract.functions.decimals().call())
        ).build_transaction({
            'from': AIRDROP_WALLET,
            'nonce': nonce,
            'gas': 150000,
            'gasPrice': w3.to_wei('5', 'gwei')
        })
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"✅ Sent {amount} tokens to {to_address}: {tx_hash.hex()}")
    except Exception as e:
        print(f"❌ Reward Error: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
