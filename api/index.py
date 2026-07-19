import os
import asyncio
import aiohttp
import json
import datetime
import random
import string
from flask import Flask, request
import telebot
from threading import Thread

# --- ማዋቀሪያዎች ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

def genString(stringLength):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(stringLength))

def digitString(stringLength):
    digit = string.digits
    return ''.join(random.choice(digit) for _ in range(stringLength))

def run_warp_request_sync(referrer_id):
    url = f'https://api.cloudflareclient.com/v0a{digitString(3)}/reg'
    install_id = genString(22)
    body = {
        "key": "{}=".format(genString(43)),
        "install_id": install_id,
        "fcm_token": "{}:APA91b{}".format(install_id, genString(134)),
        "referrer": referrer_id,
        "warp_enabled": False,
        "tos": datetime.datetime.now().isoformat() + 'Z',
        "type": "Android",
        "locale": "en_US"
    }
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Host': 'api.cloudflareclient.com',
        'User-Agent': 'okhttp/3.12.1'
    }
    try:
        # ለቪኤስኤል ፍጥነት ሲባል ጥሪው በ 3 ሰከንድ ውስጥ ካልመለሰ እንዲያልፍ ይደረጋል
        import requests
        response = requests.post(url, json=body, headers=headers, timeout=3)
        return response.status_code
    except:
        return 500

def background_warp_runner(chat_id, status_msg_id, referrer_id):
    # ቪኤስኤል ሳይዘጋው በፍጥነት 3 ጥሪዎችን ብቻ በተከታታይ እንመታለን
    success_count = 0
    total_rounds = 3
    
    for i in range(total_rounds):
        status = run_warp_request_sync(referrer_id)
        if status == 200:
            success_count += 1
            
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg_id,
                text=f"⚡ *የዳታ ማባዛት ሂደት ላይ ነው...*\n\n🔄 ዙር፦ `{i+1}/{total_rounds}`\n✅ የተሳካ፦ `{success_count} GB`"
            )
        except: pass
        
    final_text = (
        f"🎉 *የዳታ ማባዛት ሂደት ተጠናቋል!*\n\n"
        f"✅ በዚህ ዙር *{success_count} GB* ዳታ ወደ አካውንትዎ በተሳካ ሁኔታ ተጨምሯል!\n\n"
        f"📱 እባክዎ የ 1.1.1.1 መተግበሪያዎን Refresh ያድርጉት።\n\n"
        f"🔄 ተጨማሪ ዳታ ለመጨመር የ Account ID ዎን ድጋሚ መላክ ይችላሉ።"
    )
    try: bot.edit_message_text(chat_id=chat_id, message_id=status_msg_id, text=final_text)
    except: pass

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 *እንኳን በሰላም መጡ!*\n\n🚀 ለመጀመር የ 1.1.1.1 Account ID ዎን ይላኩ።")

@bot.message_handler(func=lambda message: True)
def handle_account_id(message):
    referrer_id = message.text.strip()
    if len(referrer_id) < 30 or "-" not in referrer_id:
        bot.reply_to(message, "❌ የ Account ID ስህተት ነው።")
        return
    
    status_msg = bot.reply_to(message, "⚡ *የዳታ ማባዛት ሂደት ተጀምሯል... እባክዎ ይጠብቁ...*")
    
    # ቪኤስኤል ሳይዘጋው ስራውን በጀርባ እንዲሰራ በ Thread እንከፍተዋለን
    t = Thread(target=background_warp_runner, args=(message.chat.id, status_msg.message_id, referrer_id))
    t.start()

# --- የ Webhook መቀበያ መድረክ (Flask Route) ---
@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def webhook():
    return "Bot is running perfectly!", 200
