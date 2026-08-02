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
    """ወደ ቴሌግራም ጽሁፍ መልእክት መላኪያ"""
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
    return {"status": "Enhanced Educational Video Hub Bot is active!"}

@app.post("/api/index")
@app.post("/api/webhook")
async def webhook_handler(request: Request):
    try:
        data = await request.json()
        
        # 1. የጽሁፍ መልእክት ሲመጣ
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip()
            
            if text.startswith("/start"):
                welcome_text = (
                    "👋 **እንኳን ወደ ሙያዊ የቪዲዮ እና የPDF ትምህርቶች ማዕከል በሰላም መጡ!**\n\n"
                    "መጀመሪያ **በአማርኛ የተተረጎመውን ማጠቃለያ** በማንበብ ዋና ሀሳቡን ይረዱ፤ "
                    "በመቀጠል **ቪዲዮውን** በመመልከት የተግባር እውቀትዎን ያዳብሩ።\n\n"
                    "💡 *ፍለጋ ለመጠቀም:* የፈለጉትን ቃል ቀጥታ ጽፈው ይላኩ (ምሳሌ፦ `python`፣ `engine`፣ `arduino`)\n\n"
                    "እባክዎን የሚፈልጉትን የሙያ ዘርፍ ይምረጡ፦"
                )
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "🚗 Automotive", "callback_data": "cat_automotive_0"},
                            {"text": "⚡ Electronics", "callback_data": "cat_electronics_0"}
                        ],
                        [
                            {"text": "💻 Coding", "callback_data": "cat_coding_0"},
                            {"text": "🤖 Automation", "callback_data": "cat_automation_0"}
                        ]
                    ]
                }
                send_message(chat_id, welcome_text, keyboard)
                
            elif text.startswith("/stats"):
                dataset = load_video_data()
                total_vids = sum(len(vids) for vids in dataset.values())
                stats_msg = f"📊 **የቦቱ አጠቃላይ መረጃ**\n\n🔹 የተመዘገቡ የትምህርት ዘርፎች፦ {len(dataset)}\n🔹 አጠቃላይ ዝግጁ ትምህርቶች፦ {total_vids}"
                send_message(chat_id, stats_msg)
                
            else:
                # የፍለጋ (Search) አገልግሎት
                dataset = load_video_data()
                results = []
                query = text.lower()
                
                for cat, vids in dataset.items():
                    for vid in vids:
                        if query in vid["title"].lower() or query in vid.get("amharic_text", "").lower() or query in cat:
                            results.append(vid)
                            
                if not results:
                    send_message(chat_id, f"🔍 ከ '`{text}`' ጋር የተያያዘ የትምህርት ቪዲዮ አልተገኘም። እባክዎን ሌላ ቃል ይሞክሩ ወይም ከሜኑ ውስጥ ይምረጡ።")
                else:
                    send_message(chat_id, f"🎯 **ለ '{text}' የተገኙ {len(results)} ትምህርቶች፦**")
                    for vid in results[:3]: # የመጀመሪያዎቹን 3 ማሳየት
                        msg = f"📝 **ማጠቃለያ፦**\n{vid.get('amharic_text', '')}\n\n🎬 **ቪዲዮ፦** [{vid['title']}]({vid['url']})"
                        send_message(chat_id, msg)

        # 2. ተጠቃሚው አዝራር ሲጫን (Pagination 포함)
        elif "callback_query" in data:
            query = data["callback_query"]
            chat_id = query["message"]["chat"]["id"]
            callback_data = query.get("data", "")
            
            if callback_data.startswith("cat_"):
                parts = callback_data.split("_")
                category = parts[1]
                page = int(parts[2]) if len(parts) > 2 else 0
                
                dataset = load_video_data()
                videos = dataset.get(category, [])
                
                cat_titles = {
                    "automotive": "🚗 Automotive & Mechanical",
                    "electronics": "⚡ Electronics & Circuits",
                    "coding": "💻 Programming & Software",
                    "automation": "🤖 Robotics & Automation"
                }
                
                display_title = cat_titles.get(category, category.capitalize())
                
                if not videos:
                    send_message(chat_id, f"❌ በ **{display_title}** ዘርፍ እስካሁን የተሰበሰቡ ትምህርቶች የሉም።")
                else:
                    vid = videos[page]
                    total = len(videos)
                    
                    msg = (
                        f"📚 **{display_title} ({page + 1}/{total})**\n\n"
                        f"📝 **የአማርኛ ማጠቃለያ፦**\n"
                        f"{vid.get('amharic_text', 'ማጠቃለያ አልተዘጋጀም።')}\n\n"
                        f"🎬 **ተግባራዊ ቪዲዮ ለመመልከት፦**\n"
                        f"👉 [{vid['title']}]({vid['url']})"
                    )
                    
                    buttons = []
                    if page > 0:
                        buttons.append({"text": "⬅️ የቀደመው", "callback_data": f"cat_{category}_{page - 1}"})
                    if page < total - 1:
                        buttons.append({"text": "የሚቀጥለው ➡️", "callback_data": f"cat_{category}_{page + 1}"})
                        
                    keyboard = {"inline_keyboard": [buttons]} if buttons else None
                    send_message(chat_id, msg, keyboard)
                
    except Exception as e:
        print(f"Webhook error: {e}")
        
    return {"status": "ok"}
