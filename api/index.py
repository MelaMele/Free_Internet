import os
import json
import requests
from fastapi import FastAPI, Request

app = FastAPI()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

def load_video_data():
    """በGitHub Action ስክራፕ ተደርጎ የተቀመጠውን ዳታ ያነባል"""
    try:
        if os.path.exists("videos_data.json"):
            with open("videos_data.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading video data: {e}")
    return {}

def send_message(chat_id, text, reply_markup=None):
    """ወደ ቴሌግራም መልእክት መላኪያ ፈንክሽን"""
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
        
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending message: {e}")

@app.get("/")
def home():
    return {"status": "Educational Video Hub Bot is active on Vercel!"}

@app.post("/api/index")
@app.post("/api/webhook")
async def webhook_handler(request: Request):
    """ከቴሌግራም ቦት የሚመጡ ጥያቄዎችን ማስተናገጃ"""
    try:
        data = await request.json()
        
        # 1. መደበኛ የጽሁፍ መልእክቶችን ማስተናገጃ (/start)
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")
            
            if text.startswith("/start"):
                welcome_text = (
                    "👋 **እንኳን ወደ ሙያዊ የቪዲዮ ትምህርቶች ማዕከል በሰላም መጡ!**\n\n"
                    "ከታች ካሉት አማራጮች የሚፈልጉትን የሙያ ዘርፍ በመምረጥ "
                    "በስክራፒንግ የተሰበሰቡ ነፃ እና ጥራት ያላቸውን የቪዲዮ ትምህርቶች ማግኘት ይችላሉ፡"
                )
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "🚗 Automotive", "callback_data": "cat_automotive"},
                            {"text": "⚡ Electronics", "callback_data": "cat_electronics"}
                        ],
                        [
                            {"text": "💻 Coding", "callback_data": "cat_coding"},
                            {"text": "🤖 Automation", "callback_data": "cat_automation"}
                        ]
                    ]
                }
                send_message(chat_id, welcome_text, keyboard)
                
        # 2. የአዝራሮች (Inline Buttons) መጫንን ማስተናገጃ
        elif "callback_query" in data:
            query = data["callback_query"]
            chat_id = query["message"]["chat"]["id"]
            callback_data = query.get("data", "")
            
            if callback_data.startswith("cat_"):
                category = callback_data.replace("cat_", "")
                video_dataset = load_video_data()
                videos = video_dataset.get(category, [])
                
                cat_titles = {
                    "automotive": "🚗 Automotive & Mechanical",
                    "electronics": "⚡ Electronics & Circuits",
                    "coding": "💻 Programming & Software",
                    "automation": "🤖 Robotics & Automation"
                }
                
                display_title = cat_titles.get(category, category.capitalize())
                
                if not videos:
                    response_text = f"❌ በ **{display_title}** ዘርፍ እስካሁን የተሰበሰቡ ቪዲዮዎች የሉም። እባክዎን በኋላ ድጋሚ ይሞክሩ።"
                else:
                    response_text = f"📚 **የ{display_title} ትምህርታዊ ቪዲዮዎች ዝርዝር:**\n\n"
                    for idx, vid in enumerate(videos, 1):
                        response_text += f"{idx}. 🎬 [{vid['title']}]({vid['url']})\n\n"
                    
                    response_text += "💡 *ቪዲዮዎቹን ለመመልከት ሊንኮቹን ይጫኑ።*"
                
                # ወደ ተጠቃሚው መልስ መላክ
                send_message(chat_id, response_text)
                
    except Exception as e:
        print(f"Webhook processing error: {e}")
        
    return {"status": "ok"}
