main.py 

import os import json from flask import Flask, request import telebot from telebot import types from web3 import Web3 from languages import get_text

کنفیگ 

BOT_TOKEN = os.environ.get("BOT_TOKEN") PRIVATE_KEY = os.environ.get("PRIVATE_KEY") RPC_URL = os.environ.get("RPC_URL") CHANNEL_USERNAME = "benjaminfranklintoken" CONTRACT_ADDRESS = Web3.to_checksum_address("0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181") AIRDROP_WALLET = Web3.to_checksum_address("0x6CE41726a93445750788f7e65A2bc81E95B700aE")

اتصال به بلاک‌چین 

w3 = Web3(Web3.HTTPProvider(RPC_URL)) with open("abi.json") as f: abi = json.load(f) contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

ربات 

bot = telebot.TeleBot(BOT_TOKEN) app = Flask(name)

users = {} # user_id: {wallet, invited_by, joined, referrals}

@app.route("/") def index(): return "Bot is running."

@app.route("/webhook", methods=["POST"]) def webhook(): update = telebot.types.Update.de_json(request.get_json()) bot.process_new_updates([update]) return "ok"

@bot.message_handler(commands=['start']) def handle_start(message): user_id = str(message.from_user.id) lang = message.from_user.language_code or 'en' ref = message.text.split(" ")[-1] if len(message.text.split(" ")) > 1 else None

if user_id not in users: users[user_id] = {"joined": False, "wallet": None, "invited_by": ref, "referrals": []} text = get_text('welcome', lang).format(channel=CHANNEL_USERNAME) markup = types.InlineKeyboardMarkup() markup.add(types.InlineKeyboardButton(get_text('joined_btn', lang), url=f"https://t.me/{CHANNEL_USERNAME}")) markup.add(types.InlineKeyboardButton(get_text('check_btn', lang), callback_data="check")) bot.send_message(user_id, text, reply_markup=markup) 

@bot.callback_query_handler(func=lambda c: c.data == 'check') def check_joined(call): user_id = str(call.from_user.id) lang = call.from_user.language_code or 'en' member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", call.from_user.id) if member.status in ["member", "administrator", "creator"]: if not users[user_id]["joined"]: users[user_id]["joined"] = True reward_tokens(user_id, 500) inviter = users[user_id].get("invited_by") if inviter and inviter in users: users[inviter]["referrals"].append(user_id) reward_tokens(inviter, 100) bot.send_message(user_id, get_text('joined_success', lang)) bot.send_message(user_id, get_text('ask_wallet', lang)) else: bot.send_message(user_id, get_text('not_joined', lang))

@bot.message_handler(func=lambda m: Web3.is_address(m.text)) def save_wallet(message): user_id = str(message.from_user.id) lang = message.from_user.language_code or 'en' if users[user_id].get("wallet") is None: users[user_id]["wallet"] = Web3.to_checksum_address(message.text) bot.send_message(user_id, get_text('wallet_saved', lang))

@bot.message_handler(commands=['link']) def referral_link(message): user_id = str(message.from_user.id) lang = message.from_user.language_code or 'en' link = f"https://t.me/{bot.get_me().username}?start={user_id}" bot.send_message(user_id, get_text('referral_link', lang) + link)

def reward_tokens(user_id, amount): try: to_address = users[user_id].get("wallet") if not to_address: return nonce = w3.eth.get_transaction_count(AIRDROP_WALLET) tx = contract.functions.transfer(to_address, amount * (10 ** contract.functions.decimals().call())).build_transaction({ 'from': AIRDROP_WALLET, 'nonce': nonce, 'gas': 150000, 'gasPrice': w3.to_wei('5', 'gwei') }) signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY) w3.eth.send_raw_transaction(signed_tx.rawTransaction) except Exception as e: print(f"[TRANSFER ERROR] {e}")

if name == 'main': app.run(debug=True)

