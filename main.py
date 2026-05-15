

import json
import yfinance as yf

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

# NEW IMPORTS FOR RENDER
from flask import Flask
import threading
import os

BOT_TOKEN = "8804006236:AAH2YXyMZ2ikvBuh4UQuyG9-XitshoiLwXs"

# FLASK SERVER FOR RENDER
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Stock Bot Running!"


def run_web():
    port = int(os.environ.get("PORT", 10000))

    app_web.run(
        host="0.0.0.0",
        port=port
    )

# LOAD HOLDINGS
with open("holdings.json", "r") as file:
    holdings = json.load(file)


async def portfolio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    total_invested = 0
    total_current = 0

    stock_message = ""

    # SUMMARY VARIABLES
    top_gainer = ""
    top_gainer_value = -999

    top_loser = ""
    top_loser_value = 999

    best_holding = ""
    best_holding_value = -999

    for stock in holdings:

        symbol = stock["symbol"]
        qty = stock["qty"]
        buy_price = stock["buy_price"]

        try:

            ticker = yf.Ticker(symbol)

            data = ticker.history(
                period="5d"
            )

            # Skip invalid stocks
            if data.empty or len(data) < 2:
                continue

            current_price = round(
                float(data["Close"].iloc[-1]),
                2
            )

            prev_close = round(
                float(data["Close"].iloc[-2]),
                2
            )

            day_percent = round(
                (
                    (
                        current_price -
                        prev_close
                    )
                    / prev_close
                ) * 100,
                2
            )

            # CALCULATIONS
            invested = qty * buy_price

            current_value = qty * current_price

            overall_pl = round(
                current_value - invested,
                2
            )

            overall_percent = round(
                (
                    (
                        current_price -
                        buy_price
                    )
                    / buy_price
                ) * 100,
                2
            )

            total_invested += invested
            total_current += current_value

            # DISPLAY SYMBOL
            display_symbol = (
                symbol.replace(".NS", "")
            )

            # TOP GAINER TODAY
            if day_percent > top_gainer_value:
                top_gainer_value = day_percent
                top_gainer = display_symbol

            # TOP LOSER TODAY
            if day_percent < top_loser_value:
                top_loser_value = day_percent
                top_loser = display_symbol

            # BEST OVERALL HOLDING
            if overall_percent > best_holding_value:
                best_holding_value = overall_percent
                best_holding = display_symbol

            # OVERALL COLORS
            if overall_pl >= 0:
                stock_icon = "🟢"
                arrow = "▲"
            else:
                stock_icon = "🔴"
                arrow = "▼"

            # TODAY COLORS
            if day_percent >= 0:
                today_icon = "📈"
            else:
                today_icon = "📉"

            stock_message += (
                f"{stock_icon} "
                f"{display_symbol} "
                f"{arrow} "
                f"{overall_percent}%\n\n"

                f"Qty: {qty} | "
                f"Avg: ₹{buy_price}\n"

                f"LTP: ₹{current_price}\n"

                f"{today_icon} Today: "
                f"{day_percent}%\n"

                f"💰 P/L: ₹{overall_pl}\n\n"

                f"━━━━━━━━━━━━━━\n\n"
            )

        except Exception as e:

            print(
                f"Error with {symbol}: {e}"
            )

    # TOTAL PORTFOLIO
    total_pl = round(
        total_current - total_invested,
        2
    )

    if total_invested > 0:

        total_percent = round(
            (
                (
                    total_current -
                    total_invested
                )
                / total_invested
            ) * 100,
            2
        )

    else:

        total_percent = 0

    # TOTAL COLORS
    if total_pl >= 0:
        total_icon = "🟢"
    else:
        total_icon = "🔴"

    # PORTFOLIO MOOD
    if total_percent >= 2:
        mood = "Very Bullish 🚀"

    elif total_percent >= 0:
        mood = "Mostly Positive 📈"

    else:
        mood = "Weak 📉"

    # HEADER
    header = (
        "📊 FAMILY PORTFOLIO\n\n"

        f"💰 Invested: "
        f"₹{round(total_invested, 2)}\n"

        f"💎 Current: "
        f"₹{round(total_current, 2)}\n"

        f"{total_icon} "
        f"Total P/L: "
        f"₹{total_pl} "
        f"({total_percent}%)\n\n"

        f"━━━━━━━━━━━━━━\n\n"
    )

    # DAILY SUMMARY
    summary = (
        f"📈 DAILY SUMMARY\n\n"

        f"🚀 Top Gainer:\n"
        f"{top_gainer} "
        f"({top_gainer_value}%)\n\n"

        f"🔴 Top Loser:\n"
        f"{top_loser} "
        f"({top_loser_value}%)\n\n"

        f"🏆 Best Overall Holding:\n"
        f"{best_holding} "
        f"({best_holding_value}%)\n\n"

        f"📊 Portfolio Mood:\n"
        f"{mood}"
    )

    final_message = (
        header
        + stock_message
        + summary
    )

    await update.message.reply_text(
        final_message
    )


# TELEGRAM BOT SETUP
app = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .build()
)

app.add_handler(
    CommandHandler(
        "portfolio",
        portfolio
    )
)

print("Bot Running...")

# START FLASK SERVER
threading.Thread(
    target=run_web
).start()

# START TELEGRAM BOT
app.run_polling()