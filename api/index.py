import os
import asyncio
import aiohttp
import json
import datetime
import random
import string
import threading  # በጀርባ ረጅም ስራዎችን ያለ እገዳ ለማስኬድ
from flask import Flask, request
import telebot

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

async def run_warp_request(referrer_id):
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
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=body, headers=headers, timeout=8) as response:
                return response.status
    except:
        return 500

# ይህ ፈንክሽን በጀርባ (Thread) ስለሚሮጥ Vercel ን አይዘጋውም
def start_async_loop(chat_id, status_msg_id, referrer_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(generate_bulk_data(chat_id, status_msg_id, referrer_id))
    loop.close()

async def generate_bulk_data(chat_id, status_msg_id, referrer_id):
    success_count = 0
    # በሰርቨር አልባ ላይ በጥቂት ሰከንዶች 5GB ማስገባት እንዲችል ዙሩን ወደ 5 ዝቅ አድርገነዋል
    for i in range(5): 
        status = await run_warp_request(referrer_id)
        if status == 200:
            success_count += 1
        
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg_id,
                text=f"⚡ *የዳታ ማባዛት ሂደት ላይ ነው...*\n\n🔄 ዙር፦ `{i+1}/5`\n✅ የተሳካ፦ `{success_count} GB`"
            )
        except: pass
        await asyncio.sleep(5)
        
    final_text = f"🎉 *ሂደቱ ተጠናቋል!*\n\n✅ በድምሩ *{success_count} GB* ዳታ ወደ አካውንትዎ ተጨምሯል!"
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
    
    status_msg = bot.reply_to(message, "⏳ *ሂደቱ በጀርባ ተጀምሯል...*")
    
    # ⚠️ መፍትሄ፦ ስራውን ወደ ሌላ Thread በማዞር ለ Vercel ወዲያውኑ ምላሽ እንመልሳለን (Timeout እንዳይሆን)
    t = threading.Thread(target=start_async_loop, args=(message.chat.id, status_msg.message_id, referrer_id))
    t.start()

# --- የ Webhook መቀበያ መድረክ (Flask Route) ---
@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200  # ለቴሌግራም እና ለቬርሴል ፈጣን ምላሽ (200 OK) መስጠት

@app.route('/')
def webhook():
    return "Bot is running perfectly!", 200
