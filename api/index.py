import os
import requests
from flask import Flask, request
import telebot

# --- ማዋቀሪያዎች ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

def get_live_bank_rate():
    """የኢትዮጵያ ባንኮችን ይፋዊ የዶላር መሸጫ ዋጋ ያነባል (ከፍተኛ ፍጥነት ባለው የ1.5 ሰከንድ ገደብ)"""
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        # ሰርቨሩ እንዳይዘገይ Timeout ወደ 1.5 ሰከንድ ዝቅ ተደርጓል
        response = requests.get(url, timeout=1.5)
        if response.status_code == 200:
            res_data = response.json()
            official_rate = float(res_data['rates']['ETB'])
            return official_rate
    except:
        pass
    return 126.00  # ኤፒአዩ ካልደረሰ በቀጥታ የሚተካ የቅርብ ጊዜ አማካኝ ዋጋ

def get_live_black_market_rate():
    """የ Binance P2P API ን በመጥራት የጥቁር ገበያውን ዋጋ ያነባል"""
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
        "rows": 1,
        "tradeType": "BUY"
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=1.5)
        if response.status_code == 200:
            res_data = response.json()
            price = float(res_data['data'][0]['adv']['price'])
            return price
    except:
        pass
    return 140.00  # ሰርቨሩ ካልሰራ የሚተካ አማካኝ የጥቁር ገበያ ዋጋ

@bot.message_handler(commands=['start', 'compare'])
def compare_market(message):
    # መጀመሪያ ቦቱ መስራት መጀመሩን ለተጠቃሚው እንዲያሳይ ፈጣን ሜሴጅ እንልካለን
    status_msg = bot.reply_to(message, "⏳ *የባንክ እና የጥቁር ገበያ ዋጋዎችን እያነጻጸርኩ ነው...*")
    
    # ዋጋዎቹን መሳብ
    bank_rate = get_live_bank_rate()
    black_market_rate = get_live_black_market_rate()
    
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
        "💡 *የማንቂያ ፍንጭ፦*\n"
        "በሁለቱ መካከል ያለው ሰፊ ልዩነት ከፍተኛ ትርፍ የሚያስገኝበት ቀጠና ላይ መሆንህን ያሳያል።\n\n"
        "🔄 በየደቂቃው ለማዘመን /compare ይጫኑ።"
    )
    
    try:
        # የላክነውን የ "⏳" ምልክት በአዲሱ የዳሽቦርድ መረጃ መተካት
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=dashboard_text)
    except Exception as e:
        bot.reply_to(message, dashboard_text)

@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def webhook():
    return "Fix Deployed Successfully", 200
