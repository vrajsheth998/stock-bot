

import json
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
import threading
import os

BOT_TOKEN = "8804006236:AAH2YXyMZ2ikvBuh4UQuyG9-XitshoiLwXs"

app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Stock Bot Running!", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

with open("holdings.json", "r") as file:
    all_holdings = json.load(file)


def process_portfolio(stocks, name):

    total_invested = 0
    total_current = 0
    today_pl = 0

    stock_message = ""

    top_gainer = ""
    top_gainer_value = -999
    top_loser = ""
    top_loser_value = 999
    best_holding = ""
    best_holding_value = -999

    for stock in stocks:

        symbol = stock["symbol"]
        qty = stock["qty"]
        buy_price = stock["buy_price"]

        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="5d")

            if data.empty or len(data) < 2:
                continue

            current_price = round(float(data["Close"].iloc[-1]), 2)
            prev_close = round(float(data["Close"].iloc[-2]), 2)

            day_percent = round(((current_price - prev_close) / prev_close) * 100, 2)

            invested = round(qty * buy_price, 2)
            current_value = round(qty * current_price, 2)
            overall_pl = round(current_value - invested, 2)
            overall_percent = round(((current_price - buy_price) / buy_price) * 100, 2)
            stock_today_pl = round(qty * (current_price - prev_close), 2)

            total_invested += invested
            total_current += current_value
            today_pl += stock_today_pl

            display_symbol = symbol.replace(".NS", "").replace(".BO", "")

            if day_percent > top_gainer_value:
                top_gainer_value = day_percent
                top_gainer = display_symbol

            if day_percent < top_loser_value:
                top_loser_value = day_percent
                top_loser = display_symbol

            if overall_percent > best_holding_value:
                best_holding_value = overall_percent
                best_holding = display_symbol

            overall_icon = "🟢" if overall_pl >= 0 else "🔴"
            overall_arrow = "▲" if overall_pl >= 0 else "▼"
            today_icon = "🟢" if day_percent >= 0 else "🔴"
            pl_sign = "+" if overall_pl >= 0 else ""
            day_sign = "+" if day_percent >= 0 else ""

            stock_message += (
                f"{overall_icon} {display_symbol} {overall_arrow} {overall_percent}%\n"
                f"Qty: {qty} | Avg: ₹{buy_price}\n"
                f"Invested: ₹{invested}\n"
                f"LTP: ₹{current_price}\n"
                f"Today: {today_icon} {day_sign}{day_percent}%\n"
                f"P/L: {pl_sign}₹{overall_pl}\n\n"
                f"━━━━━━━━━━━━━━\n\n"
            )

        except Exception as e:
            print(f"Error with {symbol}: {e}")

    total_pl = round(total_current - total_invested, 2)
    total_percent = round(((total_current - total_invested) / total_invested) * 100, 2) if total_invested > 0 else 0
    today_sign = "+" if today_pl >= 0 else ""
    today_total_icon = "🟢" if today_pl >= 0 else "🔴"
    total_icon = "🟢" if total_pl >= 0 else "🔴"
    pl_sign = "+" if total_pl >= 0 else ""

    header = (
        f"📊 {name} PORTFOLIO\n\n"
        f"{today_total_icon} Today's P/L: {today_sign}₹{round(today_pl, 2)}\n\n"
        f"━━━━━━━━━━━━━━\n\n"
    )

    footer = (
        f"📈 {name} SUMMARY\n\n"
        f"🚀 Top Gainer: {top_gainer} ({day_sign}{top_gainer_value}%)\n"
        f"🔴 Top Loser:  {top_loser} ({top_loser_value}%)\n"
        f"🏆 Best Overall: {best_holding} ({best_holding_value}%)\n\n"
        f"💰 Invested: ₹{round(total_invested, 2)}\n"
        f"💎 Current:  ₹{round(total_current, 2)}\n"
        f"{total_icon} Total P/L: {pl_sign}₹{total_pl} ({pl_sign}{total_percent}%)\n"
    )

    return header + stock_message + footer


async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    vraj_message = process_portfolio(all_holdings["vraj"], "VRAJ")
    mom_message = process_portfolio(all_holdings["mom"], "MOM")

    separator = "\n\n━━━━━━━━━━━━━━━━━━━━\n\n"

    final_message = vraj_message + separator + mom_message

    await update.message.reply_text(final_message)


app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("portfolio", portfolio))

print("Bot Running...")

threading.Thread(target=run_web, daemon=True).start()

app.run_polling()