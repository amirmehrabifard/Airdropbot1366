# Benjamin Franklin Token Telegram Bot

## Setup

1. Clone repo
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables:
   - BOT_TOKEN (Telegram bot token)
   - PRIVATE_KEY (Private key of owner wallet for sending tokens)
   - OWNER_WALLET (Address of the owner wallet)
4. Run `python main.py`

## Features

- Users register with /start
- Provide BSC wallet address
- Receive 500 BJF tokens on registration
- Referral system: inviter receives 100 BJF tokens per valid invite
- Invite links shared for tracking
- Runs with webhook on Railway deployment

---

Base URL (for webhook & invite links):

https://airdropbot1366-production.up.railway.app
