"""Venturerize Lite: a minimal personal AI assistant on Telegram, for one owner, on your own server.

The basics only: chat with web search, a small memory, and reminders. Everything else is up to you:
edit SYSTEM below and add your own actions in handle().

Brain: the Claude Code CLI (`claude -p`), using your Claude plan login or ANTHROPIC_API_KEY.
Config: .env next to this file (see .env.example). Run: python3 lite.py   (or python3 lite.py --cli to test)."""
import datetime, json, os, secrets, socket, subprocess, sys, threading, time, urllib.parse, urllib.request

_gai = socket.getaddrinfo   # prefer IPv4: some servers have no working IPv6 route and Telegram calls hang
socket.getaddrinfo = lambda *a, **k: [r for r in _gai(*a, **k) if r[0] == socket.AF_INET] or _gai(*a, **k)

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
ENV_F = os.path.join(HERE, ".env")
MEM = os.path.join(HERE, "memory")
os.makedirs(MEM, exist_ok=True)


def env():
    return dict(l.rstrip("\n").split("=", 1) for l in open(ENV_F) if "=" in l and not l.startswith("#"))


def set_env(k, v):
    lines = [l for l in open(ENV_F) if not l.startswith(k + "=")] + [f"{k}={v}\n"]
    open(ENV_F, "w").writelines(lines)
    os.chmod(ENV_F, 0o600)


E = env()
TZ = datetime.timezone(datetime.timedelta(minutes=int(E.get("TZ_OFFSET_MIN", "0"))))
MODEL = E.get("MODEL", "claude-sonnet-5-5")
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


# Edit this to make the assistant yours. Keep the JSON reply format, or change handle() to match.
SYSTEM = """You are a helpful personal assistant chatting on Telegram. Be brief and friendly.
Known facts about the user: {memory}
Recent chat: {history}
Now: {now}
Reply ONLY with JSON: {{"reply": "text to send", "remember": "a lasting fact or null",
"remind_at": "YYYY-MM-DDTHH:MM or null", "remind_text": "reminder text or null"}}"""


def think(msg):
    prompt = SYSTEM.format(memory="; ".join(jload("memory.json", [])[-30:]) or "none",
                           history=" | ".join(jload("history.json", [])[-10:]),
                           now=datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M %A")) + "\n\nUser: " + msg
    out = subprocess.run(["claude", "-p", "--model", MODEL, "--tools", "WebSearch,WebFetch", "--allowedTools", "WebSearch,WebFetch"],
                         input=prompt, capture_output=True, text=True, timeout=300, cwd="/tmp").stdout
    try:
        return json.loads(out[out.find("{"):out.rfind("}") + 1])
    except Exception:
        return {"reply": out.strip() or "Sorry, try again?"}


def handle(msg):
    a = think(msg)
    h = jload("history.json", [])
    jsave("history.json", (h + [f"user: {msg[:300]}", f"assistant: {str(a.get('reply'))[:300]}"])[-20:])
    if a.get("remember"):
        jsave("memory.json", jload("memory.json", []) + [a["remember"][:200]])
    if a.get("remind_at") and a.get("remind_text"):
        try:
            at = datetime.datetime.fromisoformat(a["remind_at"][:16]).replace(tzinfo=TZ).timestamp()
            jsave("reminders.json", jload("reminders.json", []) + [{"at": at, "text": a["remind_text"]}])
        except ValueError:
            pass
    send(a.get("reply") or "OK")


def reminders():
    while True:
        rs = jload("reminders.json", [])
        due = [r for r in rs if r["at"] <= time.time()]
        if due:
            jsave("reminders.json", [r for r in rs if r["at"] > time.time()])
            for r in due:
                send("⏰ " + r["text"])
        time.sleep(30)


def main():
    if "--cli" in sys.argv:
        global send
        send = lambda text: print("BOT:", text)
        for line in sys.stdin:
            handle(line.strip())
        return
    if not env().get("TG_OWNER") and not env().get("TG_PAIR"):
        set_env("TG_PAIR", secrets.token_hex(3))
    print("pair code: send /start", env().get("TG_PAIR"), "to your bot", flush=True)
    threading.Thread(target=reminders, daemon=True).start()
    offset = 0
    while True:
        for u in tg("getUpdates", offset=offset, timeout=50).get("result", []):
            offset = u["update_id"] + 1
            m = u.get("message") or {}
            if not m.get("chat"):
                continue
            chat, txt, e = str(m["chat"]["id"]), m.get("text", ""), env()
            if not e.get("TG_OWNER") and txt.strip() == f"/start {e.get('TG_PAIR')}":   # only the owner can use it
                set_env("TG_OWNER", chat); set_env("TG_PAIR", "used")
                tg("sendMessage", chat_id=chat, text="Paired. Say hi.")
                continue
            if chat != e.get("TG_OWNER"):
                tg("sendMessage", chat_id=chat, text="This is a private assistant.")
                continue
            if txt and not txt.startswith("/"):
                threading.Thread(target=handle, args=(txt,), daemon=True).start()


if __name__ == "__main__":
    main()
