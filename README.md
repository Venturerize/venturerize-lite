# Venturerize Lite

A minimal personal AI assistant on Telegram, running on your own computer or server. Free and open source (MIT).

> **Don't want to read this?** Open [`AI_SETUP.md`](AI_SETUP.md), copy all of it into ChatGPT, Claude or any AI chat,
> and it will walk you through the setup step by step.

## What it does
- Chats with you and answers questions, with live web search
- Remembers facts you tell it ("remember I'm vegetarian")
- Sends reminders ("remind me at 6 pm to call mom")
- Only your own Telegram account can use it

## What it doesn't do (on purpose)
Lite is the basics. Email, calendar, a morning brief, check-ins, voice notes, photos, files, posting to social media,
documents, websites and everything else are **not included**. If you need any of them you can:
1. **Build it yourself.** It's one small Python file. Edit `SYSTEM` (the instructions) and `handle()` (the actions) in `lite.py`.
   Your instructions and your code must match: `handle()` reads the JSON format that `SYSTEM` asks for, so if you add a
   field to one, add it to the other.
2. **Get the full version.** Venturerize sets up the complete personal assistant for you: [venturerize.com](https://venturerize.com)

## Download and run

**You need:** Python 3.9+, a Telegram account, and either a Claude plan (Pro/Max) or an Anthropic API key. No other packages.

1. **Download**
   ```bash
   git clone https://github.com/Aaravprabh/venturerize-lite.git
   cd venturerize-lite
   ```
   (or click **Code → Download ZIP** on GitHub and unzip it)

2. **Install the Claude CLI** (the assistant's brain)
   - macOS / Linux: `curl -fsSL https://claude.ai/install.sh | bash`
   - Windows (PowerShell): `irm https://claude.ai/install.ps1 | iex`
   - Then run `claude` once, sign in with your Claude account, and type `/exit`.
   - Or skip signing in and put `ANTHROPIC_API_KEY=your-key` in `.env` (step 4).

3. **Create your Telegram bot:** in Telegram open **@BotFather**, send `/newbot`, choose a name and a username ending in
   `bot`, and copy the token it gives you.

4. **Settings:** copy `.env.example` to `.env` and fill it in:
   ```
   TG_TOKEN=123456:ABC...        # from BotFather
   TZ_OFFSET_MIN=330             # your time zone in minutes (India 330, UK 0, New York -300)
   ```

5. **Test it without Telegram (optional):**
   ```bash
   python3 lite.py --cli
   ```
   Type a message, see the reply. Ctrl+D (Ctrl+Z then Enter on Windows) to quit.

6. **Run it:**
   ```bash
   python3 lite.py
   ```
   It prints `/start <code>`. Send exactly that to your bot in Telegram. The bot pairs with your account, says hello and
   from then on answers only you.

## Keep it running (Linux server, optional)
```bash
sudo tee /etc/systemd/system/lite.service >/dev/null <<EOF
[Unit]
Description=Venturerize Lite
After=network-online.target
[Service]
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/lite.py
Environment=PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
Restart=always
User=$USER
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable --now lite
```

## Files
| File | What it is |
|---|---|
| `lite.py` | the whole assistant |
| `.env.example` | settings template (copy to `.env`) |
| `AI_SETUP.md` | paste into an AI chat for guided setup |
| `memory/` | created on first run: what it remembers, reminders, recent chat. Delete it to reset. |

## Troubleshooting
- **No reply in Telegram:** is `python3 lite.py` still running? Did you send the exact `/start <code>`?
- **"Claude CLI isn't installed / signed in":** redo step 2.
- **To move the bot to a different Telegram account:** remove the `TG_OWNER=` line from `.env` and restart; it prints a new code.

## Support
Provided as is, without support. Changes you make are yours to maintain.
Want it done for you, or the full assistant? **[venturerize.com](https://venturerize.com)**

## License
MIT. See `LICENSE`.
