import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from web3 import Web3
from uuid import uuid4
from dotenv import load_dotenv

from db import (
    setup_db,
    add_user,
    get_user_by_id,
    get_user_by_invite_code,
    save_wallet_address,
    get_wallet_address,
    is_invite_rewarded,
    mark_invite_rewarded,
)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = Web3.to_checksum_address("0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181")
AIRDROP_WALLET = Web3.to_checksum_address("0xd5F168CFa6a68C21d7849171D6Aa5DDc9307E544")
NETWORK_URL = "https://bsc-dataseed.binance.org/"
DECIMALS = 18

# Initialize bot, storage, web3
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
w3 = Web3(Web3.HTTPProvider(NETWORK_URL))

with open("abi.json") as f:
    contract_abi = f.read()

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

logging.basicConfig(level=logging.INFO)
setup_db()

# States
class WalletState(StatesGroup):
    waiting_for_wallet = State()

# Middleware to check if user exists
class CheckUserMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        user = get_user_by_id(message.from_user.id)
        if not user:
            invite_code = str(uuid4())[:8]
            inviter_id = None
            if message.get_args():
                inviter_data = get_user_by_invite_code(message.get_args())
                if inviter_data:
                    inviter_id = inviter_data[0]
            add_user(message.from_user.id, invite_code, inviter_id)

dp.middleware.setup(CheckUserMiddleware())

# Start handler
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    invite_code = get_user_by_id(message.from_user.id)[1]
    link = f"https://t.me/benjaminfranklintoken_bot?start={invite_code}"

    text = (
        f"👋 Welcome!\n\n"
        f"🔹 You received 500 BJF for joining!\n"
        f"🔗 Your referral link:\n{link}\n\n"
        f"🪙 Earn 100 BJF per valid invite.\n"
        f"💼 Please send your BEP20 wallet address:"
    )
    await WalletState.waiting_for_wallet.set()
    await message.answer(text)

# Handle wallet address
@dp.message_handler(state=WalletState.waiting_for_wallet)
async def wallet_handler(message: types.Message, state: FSMContext):
    address = message.text.strip()
    if not w3.is_address(address):
        await message.answer("❌ Invalid wallet address. Please send a correct BEP20 address.")
        return
    address = Web3.to_checksum_address(address)
    save_wallet_address(message.from_user.id, address)
    await state.finish()

    await send_token(message.from_user.id, 500)

    user = get_user_by_id(message.from_user.id)
    if user[2] and not is_invite_rewarded(user[2], user[0]):
        mark_invite_rewarded(user[2], user[0])
        await send_token(user[2], 100)

    await message.answer("✅ Wallet saved and tokens sent!")

# Token sending function
async def send_token(user_id: int, amount: int):
    wallet = get_wallet_address(user_id)
    if not wallet:
        return
    nonce = w3.eth.get_transaction_count(AIRDROP_WALLET)
    tx = contract.functions.transfer(wallet, int(amount * (10 ** DECIMALS))).build_transaction({
        'from': AIRDROP_WALLET,
        'nonce': nonce,
        'gas': 200000,
        'gasPrice': w3.to_wei('5', 'gwei')
    })
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Sent {amount} BJF to {wallet}, tx: {tx_hash.hex()}")

# Webhook setup
async def on_startup(dp):
    webhook_url = "https://airdropbot1366-production.up.railway.app/webhook"
    await bot.set_webhook(webhook_url)
    print(f"✅ Webhook set to: {webhook_url}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
