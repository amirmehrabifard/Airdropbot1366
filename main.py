import os
import json
import secrets
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from web3 import Web3
from db import setup_db, add_user, get_user_by_id, get_user_by_invite_code, save_wallet_address, get_wallet_address, is_invite_rewarded, mark_invite_rewarded

# Environment variables (set these in Railway or your env, DO NOT hardcode private keys here)
BOT_TOKEN = "7279696446:AAEMrXD2-3PwP3eeMph_alwd5UniUKW_NC0"  # Replace this with your bot token or env variable
PRIVATE_KEY = os.getenv("PRIVATE_KEY")  # Your wallet private key (set safely)
BSC_RPC = "https://bsc-dataseed.binance.org/"  # BNB Smart Chain mainnet RPC
TOKEN_ADDRESS = Web3.to_checksum_address("0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181")  # BJF token contract address
OWNER_ADDRESS = Web3.to_checksum_address("0xd5F168CFa6a68C21d7849171D6Aa5DDc9307E544")  # Your airdrop wallet address

# Load token ABI
with open("token_abi.json") as f:
    TOKEN_ABI = json.load(f)

# Setup bot and web3
bot = telebot.TeleBot(BOT_TOKEN)
w3 = Web3(Web3.HTTPProvider(BSC_RPC))

if not w3.is_connected():
    print("Failed to connect to BSC RPC")
    exit(1)

contract = w3.eth.contract(address=TOKEN_ADDRESS, abi=TOKEN_ABI)

setup_db()

def generate_invite_code():
    return secrets.token_hex(4)

def send_welcome_message(user_id):
    text = ("Welcome to BenjaminFranklinToken Bot!\n"
            "Use /start to get your unique invite link.\n"
            "Join and invite friends to earn BJF tokens.\n\n"
            "To participate, you must provide your BEP20 wallet address.")
    bot.send_message(user_id, text)

def build_invite_link(invite_code):
    # Format your bot link + start parameter
    return f"https://t.me/BenjaminFranklinTokenBot?start={invite_code}"

def send_wallet_request(user_id):
    text = "Please send your BNB Smart Chain wallet address (BEP20) to receive your tokens."
    bot.send_message(user_id, text)

def send_error(user_id, message):
    bot.send_message(user_id, f"Error: {message}")

def send_success(user_id, message):
    bot.send_message(user_id, message)

def transfer_tokens(to_address, amount_wei):
    nonce = w3.eth.get_transaction_count(OWNER_ADDRESS)
    tx = contract.functions.transfer(to_address, amount_wei).build_transaction({
        'chainId': 56,
        'gas': 150000,
        'gasPrice': w3.to_wei('5', 'gwei'),
        'nonce': nonce,
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash.hex()

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) > 1:
        # User started with a referral code: /start invitecode
        invite_code = args[1]
        inviter = get_user_by_invite_code(invite_code)
        if inviter and inviter[0] != user_id:
            # Create user if new
            if not get_user_by_id(user_id):
                new_code = generate_invite_code()
                add_user(user_id=user_id, invite_code=new_code, inviter_id=inviter[0])
            else:
                new_code = get_user_by_id(user_id)[1]

            send_success(user_id, f"Your invite link: {build_invite_link(new_code)}")
            send_wallet_request(user_id)
            # Give inviter reward if not already rewarded
            if not is_invite_rewarded(inviter[0], user_id):
                try:
                    amount = 100 * 10**18  # 100 BJF tokens with decimals=18
                    tx_hash = transfer_tokens(get_wallet_address(inviter[0]) or "", amount)
                    if tx_hash:
                        mark_invite_rewarded(inviter[0], user_id)
                        send_success(inviter[0], f"You got 100 BJF tokens for inviting a friend!")
                except Exception as e:
                    send_error(user_id, f"Failed to send invite reward: {str(e)}")

        else:
            # Invalid or no inviter, just add user normally
            if not get_user_by_id(user_id):
                new_code = generate_invite_code()
                add_user(user_id=user_id, invite_code=new_code)
            else:
                new_code = get_user_by_id(user_id)[1]

            send_success(user_id, f"Your invite link: {build_invite_link(new_code)}")
            send_wallet_request(user_id)
    else:
        # Normal start without referral
        if not get_user_by_id(user_id):
            new_code = generate_invite_code()
            add_user(user_id=user_id, invite_code=new_code)
        else:
            new_code = get_user_by_id(user_id)[1]

        send_success(user_id, f"Your invite link: {build_invite_link(new_code)}")
        send_wallet_request(user_id)

@bot.message_handler(func=lambda m: True)
def handle_wallet_address(message):
    user_id = message.from_user.id
    wallet = message.text.strip()

    if not wallet.startswith("0x") or len(wallet) != 42:
        send_error(user_id, "Invalid wallet address. Please send a valid BSC wallet address.")
        return

    # Save wallet address
    save_wallet_address(user_id, wallet)

    # Send initial airdrop 500 tokens if not rewarded
    user = get_user_by_id(user_id)
    if user and user[4] == 0:
        try:
            amount = 500 * 10**18
            tx_hash = transfer_tokens(wallet, amount)
            if tx_hash:
                # Mark rewarded to prevent re-airdrops
                conn = sqlite3.connect("bot_db.sqlite3")
                c = conn.cursor()
                c.execute("UPDATE users SET rewarded=1 WHERE user_id=?", (user_id,))
                conn.commit()
                conn.close()
                send_success(user_id, f"500 BJF tokens airdropped to your wallet!\nTx: {tx_hash}")
            else:
                send_error(user_id, "Failed to send initial tokens.")
        except Exception as e:
            send_error(user_id, f"Error sending tokens: {str(e)}")
    else:
        send_success(user_id, "Your wallet address is updated. Thanks!")

if __name__ == "__main__":
    print("Bot is running...")
    bot.remove_webhook()
    # Set webhook URL on railway or your server here, example:
    WEBHOOK_URL = "https://airdropbot1366-production.up.railway.app/"  # Replace with your real URL
    bot.set_webhook(url=WEBHOOK_URL)

    import flask
    from flask import request

    app = flask.Flask(__name__)

    @app.route("/", methods=["POST"])
    def webhook():
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return ""

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
