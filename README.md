# Venturerize Lite

A minimal personal AI assistant on Telegram, running on your own server. Free and open source (MIT).

**What it does:** chats with web search, remembers a few facts about you, and sends reminders. Only your Telegram account can use it.

**What it doesn't do:** everything else. Lite is the basics on purpose. Want email, calendar, briefings or anything
specific to you? Build it yourself: edit `SYSTEM` and `handle()` in `lite.py`. Make sure your instructions and your code
match (the reply format in `SYSTEM` is what `handle()` reads).

## Run it
1. Ubuntu server (or any Linux/Mac) with Python 3 and the Claude CLI (`curl -fsSL https://claude.ai/install.sh | bash`, then sign in with `claude`), or set `ANTHROPIC_API_KEY`.
2. Telegram: talk to **@BotFather**, `/newbot`, copy the token.
3. `cp .env.example .env`, paste the token, set your time zone offset.
4. `python3 lite.py`, then send your bot the `/start <code>` it prints.

Test without Telegram: `echo "hi" | python3 lite.py --cli`

## No support
Provided as is, with no setup help or support. Changes you make are yours to maintain.

Want the full assistant (email, calendar, daily brief, check-ins and more), set up for you? **venturerize.com**
