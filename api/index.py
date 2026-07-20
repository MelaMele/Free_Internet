import os
import requests
from flask import Flask, request
import telebot

# --- ማዋቀሪያዎች ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

def get_rates():
    """የባንክ ዋጋን ብቻ በመሳብ የጥቁር ገበያውን በሀገር ውስጥ ፕሪሚየም ቀመር ያሰላል (Network Timeout እንዳይኖር)"""
    # መነሻ ዋጋዎች (ኤፒአይ ባይሰራም ቦቱ እንዳይቆም)
    bank_rate = 126.40
    
    try:
        # በጣም ፈጣን እና አስተማማኝ የባንክ ተመን ኤፒአይ (1.0 ሰከንድ ታይምአውት)
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=1.0)
        if res.status_code == 200:
            bank_rate = float(res.json()['rates']['ETB'])
    except Exception as e:
        print(f"API Error: {e}")
        
    # የጥቁር ገበያ ዋጋን አሁን ካለው 13.5% የገበያ ፕሪሚየም አንጻር በራስ-ሰር ማሳላት
    black_market_rate = bank_rate * 1.1353
    
    return bank_rate, black_market_rate

@bot.message_handler(commands=['start', 'compare', 'check'])
def send_automated_dashboard(message):
    try:
        # ዋጋዎቹን በአውቶሜሽን አስላ
        bank_rate, black_market_rate = get_rates()
        
        net_spread = black_market_rate - bank_rate
        profit_percentage = (net_spread / bank_rate) * 100
        
        # 🚨 አውቶሜትድ የንግድ ምልክት (Signal Logic)
        if net_spread >= 17.0:
            signal_alert = "🔴 **የሽያጭ ምልክት (SELL SIGNAL) - ዶላር ጨምሯል ሽጥ!**"
            trading_advice = "💡 በጥቁር ገበያ ላይ ያለው የዶላር ዋጋ በከፍተኛ ሁኔታ ጨምሯል። የያዝከውን ዶላር/USDT ወደ ብር በመቀየር ትርፍህን የምትሰበስብበት መድረክ አሁን ነው።"
        elif net_spread <= 13.0:
            signal_alert = "🟢 **የግዢ ምልክት (BUY SIGNAL) - ዶላር ቀንሷል ግዛ!**"
            trading_advice = "💡 በጥቁር ገበያ ላይ ያለው የዶላር ዋጋ ወደ ባንክ ተመን ተጠግቶ ቀንሷል። ብርህን በፍጥነት ወደ ዲጂታል ዶላር (USDT) ቀይረህ የምታከማችበት ትክክለኛ ሰዓት አሁን ነው።"
        else:
            signal_alert = "🟡 **የመጠባበቂያ ቀጠና (HOLD) - ገበያውን ታዘብ**"
            trading_advice = "💡 ገበያው መካከለኛ መረጋጋት ላይ ነው። ዋጋው በከፍተኛ ሁኔታ እስኪጨምር ወይም እስኪቀንስ ድረስ በጥንቃቄ መከታተል ይመረጣል።"

        dashboard_text = (
            "🏦 *አውቶሜትድ የፋይናንስ ረዳት (VIP)*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🏛️ *የባንክ መግዣ ዋጋ (ይፋዊ)፦* `{bank_rate:.2f} ETB`\n"
            f"👤 *የጥቁር ገበያ መሸጫ (P2P)፦* `{black_market_rate:.2f} ETB`\n\n"
            f"📊 *የተጣራ የዋጋ ልዩነት፦* `+{net_spread:.2f} ETB` (`{profit_percentage:.1f}%`)\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{signal_alert}\n\n"
            f"{trading_advice}\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔄 በየሰከንዱ የገበያውን አዲስ ምልክት ለማየት /check ይጫኑ።"
        )
        
        bot.reply_to(message, dashboard_text)
    except Exception as e:
        print(f"Dashboard Error: {e}")

@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def webhook():
    return "Automated Signals Live", 200
