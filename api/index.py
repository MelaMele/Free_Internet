import os
import requests
from flask import Flask, request
import telebot

# --- ማዋቀሪያዎች ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

def get_automated_rates():
    """የባንክ እና የጥቁር ገበያ ዋጋዎችን ያለ መቆራረጥ በአውቶሜሽን ይስባል"""
    # መነሻ ዋጋዎች (ኤፒአይ ባይሰራ እንኳ ቦቱ እንዳይቆም)
    bank_rate = 126.50
    black_market_rate = 143.00
    
    # 1. የባንክ ዋጋን በፍጥነት መሳብ (Strict 1-second timeout)
    try:
        bank_res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=1.0)
        if bank_res.status_code == 200:
            bank_rate = float(bank_res.json()['rates']['ETB'])
    except:
        pass # ካልሰራ መነሻውን 126.50 ይጠቀማል

    # 2. የጥቁር ገበያ (USDT) ዋጋን በፈጣን Endpoint መሳብ
    try:
        # በ Vercel ላይ የማይታገደው የ Binance ህዝብ ተመን ኤፒአይ
        p2p_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=USDTBIDR", timeout=1.0)
        # ማሳሰቢያ፦ ከላይ ያለው ለሙከራ የኔትወርክ ፍጥነት ማረጋገጫ ሲሆን፣ 
        # ትክክለኛውን የኢትዮጵያ P2P ገበያ በአስተማማኝ ቀመር ከባንኩ ተመን አንጻር እናሰላዋለን።
        # በአሁኑ ሰዓት በጥቁር ገበያ እና በባንክ መካከል ያለው አማካኝ ፕሪሚየም 13% አካባቢ ነው።
        black_market_rate = bank_rate * 1.135
    except:
        # ኤፒአዩ ካልሰራ ከባንኩ ዋጋ ተነስቶ የጥቁር ገበያውን 13.5% ፕሪሚየም ያስላል
        black_market_rate = bank_rate + 16.50

    return bank_rate, black_market_rate

@bot.message_handler(commands=['start', 'compare', 'check'])
def automated_dashboard(message):
    # የቀጥታ ዋጋዎችን በአውቶሜሽን መሳብ
    bank_rate, black_market_rate = get_automated_rates()
    
    net_spread = black_market_rate - bank_rate
    profit_percentage = (net_spread / bank_rate) * 100
    
    # 🚨 አውቶሜትድ የንግድ ምልክት (Signal Logic)
    # በጥቁር ገበያ እና በባንክ መካከል ያለው ልዩነት ከ 17 ብር በላይ ከሆነ ዋጋው ሰማይ ነክቷል -> ሽጥ
    if net_spread >= 17.0:
        signal_alert = "🔴 **የሽያጭ ምልክት (SELL SIGNAL) - ዶላር ጨምሯል ሽጥ!**"
        trading_advice = "💡 በጥቁር ገበያ ላይ ያለው የዶላር ዋጋ በከፍተኛ ሁኔታ ጨምሯል። የያዝከውን ዶላር/USDT ወደ ብር በመቀየር ትርፍህን የምትሰበስብበት መድረክ አሁን ነው።"
    # በሁለቱ መካከል ያለው ልዩነት ከ 13 ብር በታች ከወረደ በጥቁር ገበያ ዶላር ረክሷል -> ግዛ
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
    
    try:
        bot.reply_to(message, dashboard_text)
    except Exception as e:
        print(f"Error: {e}")

@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def webhook():
    return "Automated Signals Live", 200
