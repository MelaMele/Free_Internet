import os
import random
import string
import datetime
import requests
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

# --- ነፃ የሚሰራ ፕሮክሲ ከ API ላይ መውሰጃ ---
def get_free_proxy():
    try:
        # በየሰከንዱ የሚታደስ ነፃ የፕሮክሲ ዝርዝር ኤፒአይ
        url = "https://pubproxy.com/api/proxy?limit=1&format=json&type=http"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            proxy_ip = data['data'][0]['ipPort']
            return f"http://{proxy_ip}"
    except:
        pass
    
    # ኤፒአዩ ካልሰራ እንደ አማራጭ የሚሆኑ ቋሚ ነፃ ፕሮክሲዎች
    fallback_proxies = [
        "http://45.77.56.114:8080",
        "http://198.199.86.11:80",
        "http://165.227.223.41:3128"
    ]
    return random.choice(fallback_proxies)

def run_warp_request(referrer_id):
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
    
    # አዲስ አይፒ መምረጥ
    proxy_url = get_free_proxy()
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    try:
        # ጥሪውን በፕሮክሲው በኩል ማሳለፍ (Timeout ገደቡ 4 ሰከንድ ነው)
        response = requests.post(url, json=body, headers=headers, proxies=proxies, timeout=4)
        return response.status_code
    except:
        # የመጀመሪያው ፕሮክሲ ከከሸፈ ያለ ፕሮክሲ በቀጥታ እንዲሞክር ማድረግ
        try:
            response = requests.post(url, json=body, headers=headers, timeout=3)
            return response.status_code
        except:
            return 500

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 *እንኳን በሰላም መጡ!*\n\n🚀 ለመጀመር የ 1.1.1.1 Account ID ዎን ይላኩ።")

@bot.message_handler(func=lambda message: True)
def handle_account_id(message):
    referrer_id = message.text.strip()
    if len(referrer_id) < 30 or "-" not in referrer_id:
        bot.reply_to(message, "❌ የ Account ID ስህተት ነው።")
        return
    
    status_msg = bot.reply_to(message, "⚡ *የማባዛት ሂደት ላይ ነው... ፕሮክሲ በመጠቀም ላይ...*")
    
    status = run_warp_request(referrer_id)
    
    if status == 200:
        final_text = (
            "🎉 *የዳታ ማባዛት ሂደት ተጠናቋል!*\n\n"
            "✅ *1 GB* ዳታ ወደ አካውንትዎ በተሳካ ሁኔታ ተጨምሯል!\n\n"
            "📱 እባክዎ የ 1.1.1.1 መተግበሪያዎን Refresh ያድርጉት።\n\n"
            "🔄 ተጨማሪ ለማግኘት ID ዎን ድጋሚ መላክ ይችላሉ!"
        )
    else:
        final_text = "❌ እገዳውን መስበር አልተቻለም። እባክዎ ከጥቂት ሰከንዶች በኋላ ድጋሚ ይሞክሩ (አዲስ አይፒ እየተፈለገ ነው)።"
        
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=final_text)
    except:
        pass

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
