import os
import requests
from flask import Flask, request

app = Flask(__name__)

UNIOM_KEY = os.environ["UNIOM_API_KEY"]
OPENROUTER_KEY = os.environ["OPENROUTER_API_KEY"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

UNIOM_BASE = f"https://api.uniom.ir/bot{UNIOM_KEY}"

# آیدی خودت
MY_ID = 161008717


def ask_ai(text):
    print("AI REQUEST:", text, flush=True)

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openrouter/free",
            "messages": [
                {
                    "role": "system",
                    "content": "به فارسی، طبیعی، کوتاه و خودمونی جواب بده."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        },
        timeout=60,
    )

    print("AI STATUS:", response.status_code, flush=True)

    response.raise_for_status()

    data = response.json()

    print("AI RESPONSE RECEIVED", flush=True)

    return data["choices"][0]["message"]["content"]


def send_message(chat_id, text):
    print("SENDING MESSAGE TO:", chat_id, flush=True)

    response = requests.post(
        f"{UNIOM_BASE}/sendMessage",
        headers={
            "Content-Type": "application/json"
        },
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=30,
    )

    print("SEND STATUS:", response.status_code, flush=True)
    print("SEND RESPONSE:", response.text, flush=True)

    response.raise_for_status()


@app.route("/", methods=["GET"])
def home():
    return "Rubika AI Chat Webhook is running!", 200


@app.route("/webhook", methods=["POST"])
def webhook():

    print("===== WEBHOOK RECEIVED =====", flush=True)

    token = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    )

    if token != WEBHOOK_SECRET:
        print("BAD WEBHOOK SECRET", flush=True)
        return "Unauthorized", 401

    update = request.get_json(silent=True) or {}

    print("WEBHOOK UPDATE:", update, flush=True)

    message = update.get("message")

    if not message:
        print("NO MESSAGE IN UPDATE", flush=True)
        return "OK", 200

    sender_id = message.get("from", {}).get("id")

    print("SENDER ID:", sender_id, flush=True)

    # پیام خودت را نادیده می‌گیریم
    if sender_id == MY_ID:
        print("MY MESSAGE - IGNORING", flush=True)
        return "OK", 200

    chat = message.get("chat", {})
    chat_type = chat.get("type")
    chat_id = chat.get("id")

    print("CHAT TYPE:", chat_type, flush=True)
    print("CHAT ID:", chat_id, flush=True)

    # فعلاً فقط PV
    if chat_type != "private":
        print("GROUP MESSAGE - IGNORING", flush=True)
        return "OK", 200

    text = message.get("text", "")

    print("TEXT:", text, flush=True)

    if not text or not chat_id:
        print("EMPTY TEXT OR CHAT ID", flush=True)
        return "OK", 200

    try:
        answer = ask_ai(text)

        print("AI ANSWER:", answer, flush=True)

        send_message(chat_id, answer)

        print("MESSAGE SENT SUCCESSFULLY", flush=True)

    except Exception as e:
        print("BOT ERROR:", repr(e), flush=True)

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port
    )
