import os
import requests
from flask import Flask, request
import telebot

# --- ማዋቀሪያዎች ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

def get_live_bank_rate():
    """የኢትዮጵያ ባንኮችን ይፋዊ የዶላር መሸጫ ዋጋ ከክፍት ኤፒአይ ያነባል"""
    # ሁሉንም የኢትዮጵያ ባንኮች ተመን ሰብስቦ የሚያሳይ ነፃ ኤፒአይ
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            res_data = response.json()
            # የኢትዮጵያ ብር (ETB) ይፋዊ ተመን
            official_rate = float(res_data['rates']['ETB'])
            return official_rate
    except Exception as e:
        print(f"Error fetching bank rate: {e}")
    
    return 124.50  # ኤፒአዩ ካልሰራ እንደ መነሻ የሚወሰድ የባንኮች አማካኝ ዋጋ

def get_live_black_market_rate():
    """የ Binance P2P API ን በመጥራት የጥቁር ገበያውን የዶላር/ETB መሸጫ ዋጋ ያነባል"""
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    data = {
        "asset": "USDT",
        "fiat": "ETB",
        "merchantCheck": False,
        "page": 1,
        "payTypes": [],
        "publisherType": None,
        "rows": 3,
        "tradeType": "BUY" # እኛ በጥቁር ገበያ የምንሸጥበት ዋጋ
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=5)
        if response.status_code == 200:
            res_data = response.json()
            price = float(res_data['data'][0]['adv']['price'])
            return price
    except Exception as e:
        print(f"Error fetching P2P rate: {e}")
    
    return 139.00  # ሰርቨሩ ካልሰራ እንደ መነሻ የሚወሰድ አማካኝ የጥቁር ገበያ ዋጋ

@bot.message_handler(commands=['start', 'compare'])
def compare_market(message):
    # 1. የሰዓቱን የባንክ እና የጥቁር ገበያ ዋጋ መሳብ
    bank_rate = get_live_bank_rate()
    black_market_rate = get_live_black_market_rate()
    
    # 2. በመሃል ያለውን የተጣራ የትርፍ ልዩነት ማሰላት
    net_spread = black_market_rate - bank_rate
    profit_percentage = (net_spread / bank_rate) * 100
    
    dashboard_text = (
        "🏦 *የባንክ እና የጥቁር ገበያ ማወዳደሪያ (VIP)*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏛️ *የባንክ መግዣ ዋጋ (በርካሽ)፦* `{bank_rate:.2f} ETB`\n"
        f"👤 *የጥቁር ገበያ መሸጫ (በውድ)፦* `{black_market_rate:.2f} ETB`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📈 **አሁን ከባንክ ገዝተህ በጥቁር ገበያ ብትሸጥ የምታገኘው ትርፍ፦**\n"
        f"💰 *+{net_spread:.2f} ETB በአንድ ዶላር!* (`{profit_percentage:.1f}%` ትርፍ)\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 *የቢዝነስ ስልት መመሪያ፦*\n"
        "እጅግ የሚያዋጣ ቀጠና ላይ ነህ። አሁን ያለህን የሀገር ውስጥ ብር ተጠቅመህ ከባንክ ዶላር መግዛት ከቻልክ፣ ወዲያውኑ ወደ ዲጂታል ዶላር (USDT) ቀይረህ በጥቁር ገበያ በመሸጥ ይህንን ትርፍ ሙሉ በሙሉ ማፈስ ትችላለህ።\n\n"
        "🔄 በየደቂቃው የዋጋ ልዩነቱን ለማየት /compare ይጫኑ።"
    )
    
    bot.reply_to(message, dashboard_text)

# --- የ Webhook መቀበያ መድረክ (Flask Route) ---
@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def webhook():
    return "Bank Arbitrage Bot is running perfectly!", 200
