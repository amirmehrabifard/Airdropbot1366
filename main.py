import os import logging from aiogram import Bot, Dispatcher, types from aiogram.types import ParseMode from aiogram.utils import executor from aiogram.dispatcher.middlewares import BaseMiddleware from aiogram.dispatcher.handler import CancelHandler from aiogram.dispatcher import FSMContext from aiogram.contrib.fsm_storage.memory import MemoryStorage from aiogram.dispatcher.filters.state import State, StatesGroup from web3 import Web3 from uuid import uuid4 from dotenv import load_dotenv from db import setup_db, add_user, get_user_by_id, get_user_by_invite_code, save_wallet_address, get_wallet_address, is_invite_rewarded, mark_invite_rewarded

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN") PRIVATE_KEY = os.getenv("PRIVATE_KEY") AIR_DROP_WALLET = "0xd5F168CFa6a68C21d7849171D6Aa5DDc9307E544" TOKEN_CONTRACT = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181" DECIMALS = 18 BASE_URL = "https://airdropbot1366-production.up.railway.app" NETWORK_URL = "https://bsc-dataseed.binance.org/"

bot = Bot(token=API_TOKEN) dp = Dispatcher(bot, storage=MemoryStorage()) web3 = Web3(Web3.HTTPProvider(NETWORK_URL)) contract_abi = [...] # Paste your full ABI list here contract = web3.eth.contract(address=Web3.to_checksum_address(TOKEN_CONTRACT), abi=contract_abi)

State machine 

class WalletStates(StatesGroup): waiting_for_wallet = State()

Middleware to ensure user is member of the channel 

class CheckSubscriptionMiddleware(BaseMiddleware): async def on_pre_process_update(self, update: types.Update, data: dict): if update.message: user_id = update.message.from_user.id try: member = await bot.get_chat_member(chat_id='@benjaminfranklintoken', user_id=user_id) if member.status not in ['member', 'creator', 'administrator']: await update.message.answer("Please join our channel first: https://t.me/benjaminfranklintoken") raise CancelHandler() except: await update.message.answer("Please join our channel first: https://t.me/benjaminfranklintoken") raise CancelHandler()

dp.middleware.setup(CheckSubscriptionMiddleware())

Command: /start 

@dp.message_handler(commands=['start']) async def send_welcome(message: types.Message): setup_db() user_id = message.from_user.id args = message.get_args() inviter_id = None if args: inviter = get_user_by_invite_code(args) if inviter: inviter_id = inviter[0]

user_data = get_user_by_id(user_id) if not user_data: invite_code = str(uuid4())[:8] add_user(user_id, invite_code, inviter_id) await message.answer("Welcome! Please send me your BNB Smart Chain wallet address to receive 500 BJF tokens.") await WalletStates.waiting_for_wallet.set() else: await message.answer("You are already registered.") Handle wallet submission 

@dp.message_handler(state=WalletStates.waiting_for_wallet) async def handle_wallet(message: types.Message, state: FSMContext): user_id = message.from_user.id wallet = message.text.strip()

if not web3.is_address(wallet): await message.answer("Invalid wallet address. Please send a valid BNB address.") return save_wallet_address(user_id, wallet) await state.finish() await send_tokens(wallet, 500) await message.answer("✅ 500 BJF tokens sent to your wallet!\nYour invite link: {}?start={}".format(BASE_URL, get_user_by_id(user_id)[1])) inviter_id = get_user_by_id(user_id)[2] if inviter_id and not is_invite_rewarded(inviter_id, user_id): inviter_wallet = get_wallet_address(inviter_id) if inviter_wallet: await send_tokens(inviter_wallet, 100) mark_invite_rewarded(inviter_id, user_id) await bot.send_message(inviter_id, f"🎉 You invited someone and earned 100 BJF tokens!") Token transfer function 

async def send_tokens(to_address, amount): try: nonce = web3.eth.get_transaction_count(AIR_DROP_WALLET) txn = contract.functions.transfer( Web3.to_checksum_address(to_address), int(amount * (10 ** DECIMALS)) ).build_transaction({ 'chainId': 56, 'gas': 200000, 'gasPrice': web3.to_wei('5', 'gwei'), 'nonce': nonce }) signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY) tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction) return web3.to_hex(tx_hash) except Exception as e: logging.error(f"Error sending tokens: {e}") return None

if name == 'main': from aiogram import executor executor.start_polling(dp, skip_updates=True)

