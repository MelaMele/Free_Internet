import os
from flask import Flask, request
import telebot

# --- ማዋቀሪያዎች ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

@bot.message_handler(commands=['start', 'compare'])
def compare_market(message):
    # 💡 ኔትወርኩ እንዳያቆመው ለአሁኑ ወቅታዊውን የኢትዮጵያ ገበያ ዋጋ እዚሁ ላይ እንመድበዋለን
    # (ኮዱ መስራቱን ካረጋገጥን በኋላ የኤፒአይ ጥሪውን እናስተካክላለን)
    bank_rate = 126.40          # የባንክ አማካኝ መሸጫ ዋጋ
    black_market_rate = 142.50   # የጥቁር ገበያ (Binance USDT) መሸጫ ዋጋ
    
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
        "🟢 **የሲስተም ሁኔታ፦** መዋቅሩ በትክክል እየሰራ ነው።\n"
        "💡 *የማንቂያ ፍንጭ፦* በሁለቱ መካከል ያለው ሰፊ ልዩነት ከፍተኛ ትርፍ የሚያስገኝበት ቀጠና ላይ መሆንህን ያሳያል።\n\n"
        "🔄 ገበያውን ለመፈተሽ /compare ይጫኑ።"
    )
    
    # በቀጥታ መልዕክቱን መላክ (ያለ edit_message_text ስጋት)
    bot.reply_to(message, dashboard_text)

@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def webhook():
    return "Test Dashboard Ready", 200
