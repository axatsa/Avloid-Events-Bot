# Avloid Events Bot

Telegram bot for managing events and registrations for the Avloid community.

## Features
- User registration and profile management
- Event announcements and sign-ups
- Moderation panel (admin / moderator / user roles)
- Google Sheets integration for data export

## Tech Stack
- Python 3.11+
- aiogram 3.x
- SQLite
- Google Sheets API

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env  # add BOT_TOKEN
python main.py
```