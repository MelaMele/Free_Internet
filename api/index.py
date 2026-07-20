import os
import requests
from flask import Flask, request
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
# 💡 ማሳሰቢያ፦ ይህ የቪአይፒ ቻናል ወይም ያንተ የግል ቴሌግራም ቻት መለያ ነው (Actions መልዕክት እንዲልክልህ)
CHAT_ID = os.getenv("CHAT_ID") 

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# ለእያንዳንዱ ምንዛሬ በጥቁር ገበያ የሚኖረው መደበኛ የፕሪሚየም ማባዣ (Premium Multipliers)
PREMIUMS = {
    "USD": 1.1353,  # ~13.5% ፕሪሚየም
    "EUR": 1.1420,  # ~14.2% ፕሪሚየም
    "GBP": 1.1450   # ~14.5% ፕሪሚየም
}

def get_all_rates():
    """USD, EUR እና GBP ዋጋዎችን ከአስተማማኝ ኤፒአይ በአንድ ላይ ይስባል"""
    rates_data = {}
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=1.5)
        if res.status_code == 200:
            base_data = res.json()['rates']
            etb_usd = float(base_data['ETB'])
            
            # ዩሮ እና ፓውንድን ወደ ብር መመንዘር
            etb_eur = etb_usd / float(base_data['EUR'])
            etb_gbp = etb_usd / float(base_data['GBP'])
            
            currencies = {"USD": etb_usd, "EUR": etb_eur, "GBP": etb_gbp}
            
            for curr, bank_val in currencies.items():
                black_val = bank_val * PREMIUMS[curr]
                net_spread = black_val - bank_val
                
                # አውቶሜትድ የንግድ ምልክት መወሰኛ
                if net_spread >= 17.0:
                    status = "🔴 SHIFT (ሽጥ)"
                elif net_spread <= 13.5:
                    status = "🟢 GIZA (ግዛ)"
                else:
                    status = "🟡 HOLD (ታዘብ)"
                    
                rates_data[curr] = {
                    "bank": bank_val,
                    "black": black_val,
                    "spread": net_spread,
                    "status": status
                }
            return rates_data
    except Exception as e:
        print(f"API Fetch Error: {e}")
    
    # ኤፒአዩ ካልሰራ የሚተካ መነሻ የፓናል ዳታ
    return {
        "USD": {"bank": 126.40, "black": 143.50, "spread": 17.10, "status": "🔴 SHIFT (ሽጥ)"},
        "EUR": {"bank": 134.20, "black": 153.25, "spread": 19.05, "status": "🔴 SHIFT (ሽጥ)"},
        "GBP": {"bank": 158.10, "black": 180.95, "spread": 22.85, "status": "🔴 SHIFT (ሽጥ)"}
    }

def build_dashboard_text(rates):
    text = "🏦 *አውቶሜትድ የፋይናንስ ረዳት (VIP Dashboard)*\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    for curr, data in rates.items():
        text += (
            f"💱 *ምንዛሬ፦ {curr}*\n"
            f"🏛️ ባንክ፦ `{data['bank']:.2f} ETB` | 👤 ጥቁር ገበያ፦ `{data['black']:.2f} ETB`\n"
            f"📊 ልዩነት፦ `+{data['spread']:.2f} ETB`\n"
            f"🚨 ምልክት፦ {data['status']}\n"
            "-------------------------------------\n"
        )
    text += "\n🔄 ገበያውን በራስህ ለመፈተሽ /check ይጫኑ።"
    return text

@bot.message_handler(commands=['start', 'compare', 'check'])
def send_dashboard(message):
    rates = get_all_rates()
    dashboard_text = build_dashboard_text(rates)
    bot.reply_to(message, dashboard_text)

# --- ለ GitHub Actions አውቶማቲክ ክሮን ጆብ የሚሆን ኤንድፖይንት ---
@app.route('/api/cron', methods=['GET'])
def cron_trigger():
    # ይህ ኤንድፖይንት በየ 30 ደቂቃው ሲጠራ ለተጠቃሚው አውቶማቲክ ፑሽ ኖቲፊኬሽን ይልካል
    rates = get_all_rates()
    dashboard_text = "*🚨 አውቶማቲክ የገበያ ማንቂያ (30 Min Update)*\n\n" + build_dashboard_text(rates)
    
    if CHAT_ID:
        try:
            bot.send_message(CHAT_ID, dashboard_text)
            return "Alert Sent Successfully", 200
        except Exception as e:
            return f"Failed to send: {e}", 500
    return "No Chat ID Configured", 400

@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def webhook():
    return "Multi-Currency Bot Active", 200
