"""Venturerize Lite: a minimal personal AI assistant on Telegram, for one owner, on your own server.

The basics only: chat with web search, a small memory, and reminders. Everything else is up to you:
edit SYSTEM below and add your own actions in handle(). Need more without building it? See venturerize.com.

Brain: the Claude Code CLI (`claude -p`), using your Claude plan login or ANTHROPIC_API_KEY.
Config: .env next to this file (see .env.example). Run: python3 lite.py   (or python3 lite.py --cli to test)."""
import datetime, json, os, secrets, shutil, socket, subprocess, sys, threading, time, urllib.parse, urllib.request

_gai = socket.getaddrinfo   # prefer IPv4: some servers have no working IPv6 route and Telegram calls hang
socket.getaddrinfo = lambda *a, **k: [r for r in _gai(*a, **k) if r[0] == socket.AF_INET] or _gai(*a, **k)

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
ENV_F = os.path.join(HERE, ".env")
MEM = os.path.join(HERE, "memory")
os.makedirs(MEM, exist_ok=True)
LOCK = threading.Lock()   # one writer at a time for the memory files

WELCOME = """👋 Hi! I'm your Venturerize Lite assistant.

I can:
• chat and answer questions (I can search the web)
• remember things you tell me ("remember I'm vegetarian")
• remind you ("remind me at 6 pm to call mom")

That's it on purpose: Lite is the basics. Want email, calendar, a morning brief or anything else?
Build it yourself (it's open source), or get the full assistant set up for you at venturerize.com.

Say hi to start."""


def env():
    if not os.path.exists(ENV_F):
        sys.exit("No .env file. Run: cp .env.example .env   then put your Telegram bot token in it.")
    return dict(l.rstrip("\n").split("=", 1) for l in open(ENV_F) if "=" in l and not l.startswith("#"))


def set_env(k, v):
    lines = [l for l in open(ENV_F) if not l.startswith(k + "=")] + [f"{k}={v}\n"]
    open(ENV_F, "w").writelines(lines)
    os.chmod(ENV_F, 0o600)


E = env()
TZ = datetime.timezone(datetime.timedelta(minutes=int(E.get("TZ_OFFSET_MIN", "0") or 0)))
MODEL = E.get("MODEL") or "claude-sonnet-5-5"
API = f"https://api.telegram.org/bot{E.get('TG_TOKEN', '')}"


def jload(name, default):
    try:
        return json.load(open(os.path.join(MEM, name)))
    except Exception:
        return default


def jsave(name, obj):
    json.dump(obj, open(os.path.join(MEM, name), "w"), indent=1)


def tg(method, **params):
    try:
        req = urllib.request.Request(f"{API}/{method}", data=urllib.parse.urlencode(params).encode())
        return json.load(urllib.request.urlopen(req, timeout=70))
    except Exception as e:
        print("telegram error:", method, e, flush=True)
        return {}


def send(text):
    owner = env().get("TG_OWNER")
    if owner:
        for i in range(0, len(text), 4000):
            tg("sendMessage", chat_id=owner, text=text[i:i + 4000])


# Edit this to make the assistant yours. Keep the JSON reply format, or change handle() to read your new format.
SYSTEM = """You are a helpful personal assistant chatting on Telegram. Be brief and friendly.
You only chat, search the web, remember facts and set reminders. If asked for anything else (email, calendar,
files, posting, etc.), say Lite doesn't do that: they can add it to the code themselves or get the full version at venturerize.com.
Known facts about the user: {memory}
Recent chat: {history}
Now: {now}
Reply ONLY with JSON: {{"reply": "text to send", "remember": "a lasting fact or null",
"remind_at": "YYYY-MM-DDTHH:MM or null", "remind_text": "reminder text or null"}}"""


def think(msg):
    prompt = SYSTEM.format(memory="; ".join(jload("memory.json", [])[-30:]) or "none",
                           history=" | ".join(jload("history.json", [])[-10:]) or "none",
                           now=datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M %A")) + "\n\nUser: " + msg
    try:
        out = subprocess.run(["claude", "-p", "--model", MODEL, "--tools", "WebSearch,WebFetch",
                              "--allowedTools", "WebSearch,WebFetch"],
                             input=prompt, capture_output=True, text=True, timeout=300, cwd=HERE).stdout
    except FileNotFoundError:
        return {"reply": "The Claude CLI isn't installed on the server. See the README, step 2."}
    except subprocess.TimeoutExpired:
        return {"reply": "That took too long. Try again?"}
    try:
        return json.loads(out[out.find("{"):out.rfind("}") + 1])
    except Exception:
        return {"reply": out.strip() or "No answer from Claude. Is the CLI signed in? (README, step 2)"}


def handle(msg):
    a = think(msg)
    with LOCK:
        jsave("history.json", (jload("history.json", []) + [f"user: {msg[:300]}", f"assistant: {str(a.get('reply'))[:300]}"])[-20:])
        if a.get("remember"):
            jsave("memory.json", (jload("memory.json", []) + [str(a["remember"])[:200]])[-100:])
        if a.get("remind_at") and a.get("remind_text"):
            try:
                at = datetime.datetime.fromisoformat(str(a["remind_at"])[:16]).replace(tzinfo=TZ).timestamp()
                jsave("reminders.json", jload("reminders.json", []) + [{"at": at, "text": str(a["remind_text"])}])
            except ValueError:
                pass
    send(str(a.get("reply") or "OK"))


def reminders():
    while True:
        with LOCK:
            rs = jload("reminders.json", [])
            due = [r for r in rs if r["at"] <= time.time()]
            if due:
                jsave("reminders.json", [r for r in rs if r["at"] > time.time()])
        for r in due:
            send("⏰ " + r["text"])
        time.sleep(30)


def main():
    if "--cli" in sys.argv:   # test mode for you (or an AI helping you): no Telegram, no welcome message
        global send
        send = lambda text: print("BOT:", text, flush=True)
        print("Lite test mode. Type a message, Ctrl+D to quit.", flush=True)
        for line in sys.stdin:
            if line.strip():
                handle(line.strip())
        return
    if not E.get("TG_TOKEN"):
        sys.exit("TG_TOKEN is empty in .env. Get one from @BotFather on Telegram (README, step 3).")
    if not shutil.which("claude"):
        print("Warning: the Claude CLI isn't on PATH; replies will fail until it is (README, step 2).", flush=True)
    if not env().get("TG_OWNER") and not env().get("TG_PAIR"):
        set_env("TG_PAIR", secrets.token_hex(3))
    if not env().get("TG_OWNER"):
        print(f"Open your bot in Telegram and send:  /start {env().get('TG_PAIR')}", flush=True)
    threading.Thread(target=reminders, daemon=True).start()
    offset = 0
    while True:
        for u in tg("getUpdates", offset=offset, timeout=50).get("result", []):
            offset = u["update_id"] + 1
            m = u.get("message") or {}
            if not m.get("chat"):
                continue   # edited messages, channel posts etc.
            chat, txt, e = str(m["chat"]["id"]), m.get("text", ""), env()
            if not e.get("TG_OWNER") and txt.strip() == f"/start {e.get('TG_PAIR')}":   # only the owner can use it
                set_env("TG_OWNER", chat); set_env("TG_PAIR", "used")
                tg("sendMessage", chat_id=chat, text=WELCOME)   # first real message from a person: introduce
                continue
            if chat != e.get("TG_OWNER"):
                tg("sendMessage", chat_id=chat, text="This is a private assistant.")
                continue
            if not txt:
                send("Lite reads text messages only. (Voice notes, photos and files are in the full version at venturerize.com, or add them yourself.)")
            elif txt.strip() in ("/start", "/help"):
                send(WELCOME)
            elif not txt.startswith("/"):
                threading.Thread(target=handle, args=(txt,), daemon=True).start()


if __name__ == "__main__":
    main()
