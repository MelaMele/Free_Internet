import os
import json
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, ContextTypes

app = FastAPI()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# የተሰበሰበውን የቪዲዮ ዳታ ማንበቢያ
def load_video_data():
    if os.path.exists("videos_data.json"):
        with open("videos_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@app.get("/")
def home():
    return {"status": "Video Hub Bot is running on Vercel!"}

@app.post("/api/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    
    # የTelegram Update ማቀናበሪያ logic
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        
        if text == "/start":
            keyboard = [
                [InlineKeyboardButton("🚗 Automotive", callback_data="cat_automotive"),
                 InlineKeyboardButton("⚡ Electronics", callback_data="cat_electronics")],
                [InlineKeyboardButton("💻 Coding", callback_data="cat_coding"),
                 InlineKeyboardButton("🤖 Automation", callback_data="cat_automation")]
            ]
            reply_markup = {"inline_keyboard": keyboard}
            
            payload = {
                "chat_id": chat_id,
                "text": "እንኳን ወደ ሙያዊ የቪዲዮ ትምህርቶች ማዕከል በሰላም መጡ! የሚፈልጉትን የሙያ ዘርፍ ይምረጡ፡",
                "reply_markup": reply_markup
            }
            # በRequests መልስ መላክ ይቻላል
            import requests
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json=payload)
            
    elif "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        category = query["data"].replace("cat_", "")
        
        videos = load_video_data().get(category, [])
        
        if not videos:
            msg_text = f"ለእነዚህ `{category}` ዘርፍ እስካሁን የተሰበሰቡ ቪዲዮዎች የሉም።"
        else:
            msg_text = f"📹 **የ{category.capitalize()} ትምህርታዊ ቪዲዮዎች:**\n\n"
            for v in videos[:5]: # የመጀመሪያዎቹን 5 ቪዲዮዎች ለማሳየት
                msg_text += f"🔹 [{v['title']}]({v['url']})\n"
        
        import requests
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
            "chat_id": chat_id,
            "text": msg_text,
            "parse_mode": "Markdown"
        })

    return {"status": "ok"}
