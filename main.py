import json
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
import threading
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle

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


def fmt(n):
    n = round(n, 2)
    s = f"{n:.2f}"
    integer, decimal = s.split(".")
    negative = integer.startswith("-")
    if negative:
        integer = integer[1:]
    if len(integer) > 3:
        last3 = integer[-3:]
        rest = integer[:-3]
        groups = []
        while len(rest) > 2:
            groups.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.append(rest)
        integer = last3 if not groups else ",".join(reversed(groups)) + "," + last3
    result = f"Rs.{integer}.{decimal}"
    return f"-{result}" if negative else result


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

            if data.empty:
                print(f"Empty data for {symbol}")
                continue

            if len(data) < 2:
                current_price = round(float(data["Close"].iloc[-1]), 2)
                prev_close = current_price
            else:
                current_price = round(float(data["Close"].iloc[-1]), 2)
                prev_close = round(float(data["Close"].iloc[-2]), 2)

            day_percent = round(((current_price - prev_close) / prev_close) * 100, 2) if prev_close > 0 else 0
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
                f"{overall_icon}{display_symbol} {overall_arrow} {overall_percent}%\n"
                f"Qty: {qty} | Avg: {fmt(buy_price)}\n"
                f"Invested: {fmt(invested)}\n"
                f"LTP: {fmt(current_price)}\n"
                f"Today: {today_icon} {day_sign}{day_percent}%\n"
                f"P/L: {pl_sign}{fmt(overall_pl)}\n\n"
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
        f"{today_total_icon} Today's P/L: {today_sign}{fmt(today_pl)}\n\n"
        f"━━━━━━━━━━━━━━\n\n"
    )

    footer = (
        f"📈 {name} SUMMARY\n\n"
        f"🟢 Top Gainer:    {top_gainer} ({day_sign}{top_gainer_value}%)\n"
        f"🔴 Top Loser:     {top_loser} ({top_loser_value}%)\n"
        f"🏆 Best Overall:  {best_holding} ({best_holding_value}%)\n\n"
        f"💰 Invested: {fmt(total_invested)}\n"
        f"💎 Current:  {fmt(total_current)}\n"
        f"{total_icon} Total P/L: {pl_sign}{fmt(total_pl)} ({pl_sign}{total_percent}%)\n"
    )

    return header + stock_message + footer


def get_stock_data_for_report(stocks):
    rows = []
    total_invested = 0
    total_current = 0
    total_pl = 0

    for stock in stocks:
        symbol = stock["symbol"]
        qty = stock["qty"]
        buy_price = stock["buy_price"]

        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="7d")

            if data.empty:
                print(f"Report: empty data for {symbol}")
                continue

            current_price = round(float(data["Close"].iloc[-1]), 2)
            week_open = round(float(data["Close"].iloc[0]), 2)
            week_percent = round(((current_price - week_open) / week_open) * 100, 2) if week_open > 0 else 0
            invested = round(qty * buy_price, 2)
            current_value = round(qty * current_price, 2)
            overall_pl = round(current_value - invested, 2)
            overall_percent = round(((current_price - buy_price) / buy_price) * 100, 2)

            total_invested += invested
            total_current += current_value
            total_pl += overall_pl

            display_symbol = symbol.replace(".NS", "").replace(".BO", "")

            rows.append({
                "symbol": display_symbol,
                "qty": qty,
                "buy_price": buy_price,
                "current_price": current_price,
                "invested": invested,
                "overall_pl": overall_pl,
                "overall_percent": overall_percent,
                "week_percent": week_percent,
            })

        except Exception as e:
            print(f"Report error with {symbol}: {e}")

    return rows, total_invested, total_current, total_pl


def get_news_for_stock(symbol, display_symbol):
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        headlines = []
        for item in news[:3]:
            title = item.get("content", {}).get("title", "")
            age = item.get("content", {}).get("pubDate", "")
            if title:
                if age:
                    try:
                        pub = datetime.strptime(age[:10], "%Y-%m-%d")
                        age_str = pub.strftime("%d %b")
                    except:
                        age_str = ""
                else:
                    age_str = ""
                headlines.append(f"• {title} ({age_str})" if age_str else f"• {title}")
        return headlines
    except Exception as e:
        print(f"News error for {symbol}: {e}")
        return []


def generate_pdf(vraj_rows, vraj_totals, mom_rows, mom_totals):
    filepath = "/tmp/family_portfolio_report.pdf"
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=20*mm,
        bottomMargin=15*mm
    )

    BLUE = colors.HexColor("#185FA5")
    LIGHT_BLUE = colors.HexColor("#E6F1FB")
    GREEN = colors.HexColor("#3B6D11")
    RED = colors.HexColor("#A32D2D")
    GRAY = colors.HexColor("#F1EFE8")
    DARK = colors.HexColor("#2C2C2A")

    title_style = ParagraphStyle(
        "title", fontSize=22, textColor=BLUE,
        spaceAfter=6, spaceBefore=0, fontName="Helvetica-Bold"
    )
    sub_style = ParagraphStyle(
        "sub", fontSize=12, textColor=colors.HexColor("#5F5E5A"),
        spaceAfter=4, spaceBefore=0
    )
    date_style = ParagraphStyle(
        "date", fontSize=10, textColor=colors.HexColor("#888780"),
        spaceAfter=14, spaceBefore=0
    )
    section_style = ParagraphStyle(
        "section", fontSize=13, textColor=BLUE,
        spaceBefore=10, spaceAfter=6, fontName="Helvetica-Bold"
    )
    news_title_style = ParagraphStyle(
        "newstitle", fontSize=11, textColor=BLUE,
        spaceBefore=8, spaceAfter=3, fontName="Helvetica-Bold"
    )
    news_item_style = ParagraphStyle(
        "newsitem", fontSize=9, textColor=colors.HexColor("#5F5E5A"),
        spaceAfter=3, leftIndent=8
    )

    def make_holdings_table(rows, totals):
        total_invested, total_current, total_pl = totals
        total_percent = round(((total_current - total_invested) / total_invested) * 100, 2) if total_invested > 0 else 0

        header = ["Stock", "Qty", "Avg", "LTP", "Invested", "P&L", "Week %"]
        data = [header]

        for r in rows:
            pl_str = f"+{fmt(r['overall_pl'])}" if r['overall_pl'] >= 0 else fmt(r['overall_pl'])
            week_str = f"+{r['week_percent']}%" if r['week_percent'] >= 0 else f"{r['week_percent']}%"
            data.append([
                r["symbol"],
                str(r["qty"]),
                fmt(r["buy_price"]),
                fmt(r["current_price"]),
                fmt(r["invested"]),
                pl_str,
                week_str,
            ])

        total_pl_str = f"+{fmt(total_pl)}" if total_pl >= 0 else fmt(total_pl)
        total_pct_str = f"+{total_percent}%" if total_percent >= 0 else f"{total_percent}%"
        data.append(["TOTAL", "", "", "", fmt(total_invested), total_pl_str, total_pct_str])

        t = Table(
           data,
              colWidths=[
        35*mm,
        15*mm,
        22*mm,
        22*mm,
        26*mm,
        26*mm,
        16*mm
             ]
           )

        t.repeatRows = 1         
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), BLUE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("BACKGROUND", (0, -1), (-1, -1), GRAY),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F9F9F7")]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D3D1C7")),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        return t

    story = []

    now = datetime.now()

    # PAGE 1 - COVER
    story.append(Paragraph("Family Portfolio", title_style))
    story.append(Paragraph("Weekly Report — Vraj &amp; Mom", sub_style))
    story.append(Paragraph(f"Generated on {now.strftime('%d %B %Y, %I:%M %p')}", date_style))

    combined_invested = vraj_totals[0] + mom_totals[0]
    combined_current = vraj_totals[1] + mom_totals[1]
    combined_pl = vraj_totals[2] + mom_totals[2]
    combined_pct = round(((combined_current - combined_invested) / combined_invested) * 100, 2) if combined_invested > 0 else 0
    pl_sign = "+" if combined_pl >= 0 else ""

    summary_data = [
        ["Total Invested", "Current Value", "Overall P&L"],
        [fmt(combined_invested), fmt(combined_current), f"{pl_sign}{fmt(combined_pl)} ({pl_sign}{combined_pct}%)"]
    ]
    summary_table = Table(summary_data, colWidths=[60*mm, 60*mm, 60*mm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), BLUE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D3D1C7")),
        ("TEXTCOLOR", (0, 1), (0, 1), DARK),
        ("TEXTCOLOR", (1, 1), (1, 1), DARK),
        ("TEXTCOLOR", (2, 1), (2, 1), GREEN if combined_pl >= 0 else RED),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
    ]))
    story.append(summary_table)

    # PAGE 2 - HOLDINGS
    story.append(PageBreak())
    story.append(Paragraph("Vraj — Holdings", section_style))
    story.append(make_holdings_table(vraj_rows, vraj_totals))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("Mom — Holdings", section_style))
    story.append(make_holdings_table(mom_rows, mom_totals))

    # PAGE 3 - NEWS
    story.append(PageBreak())
    story.append(Paragraph("Stock News — Last 7 Days", section_style))
    story.append(Spacer(1, 4*mm))

    all_stocks = list(all_holdings["vraj"]) + list(all_holdings["mom"])
    seen = set()
    for stock in all_stocks:
        symbol = stock["symbol"]
        display = symbol.replace(".NS", "").replace(".BO", "")
        if display in seen:
            continue
        seen.add(display)
        headlines = get_news_for_stock(symbol, display)
        if headlines:
            story.append(Paragraph(display, news_title_style))
            for h in headlines:
                story.append(Paragraph(h, news_item_style))

    doc.build(story)
    return filepath


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Generating your weekly report PDF... please wait ⏳"
    )

    try:

        vraj_rows, vi, vc, vp = get_stock_data_for_report(
            all_holdings["vraj"]
        )

        mom_rows, mi, mc, mp = get_stock_data_for_report(
            all_holdings["mom"]
        )

        filepath = generate_pdf(
            vraj_rows,
            (vi, vc, vp),
            mom_rows,
            (mi, mc, mp)
        )

        with open(filepath, "rb") as f:

            await update.message.reply_document(
                document=f,
                filename="Family_Portfolio_Report.pdf",
                caption="Your weekly portfolio report"
            )

    except Exception as e:

        print(f"Report generation error: {e}")

        await update.message.reply_text(
            f"Sorry, error generating report: {e}"
        )


async def portfolio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    vraj_message = process_portfolio(
        all_holdings["vraj"],
        "VRAJ"
    )

    mom_message = process_portfolio(
        all_holdings["mom"],
        "MOM"
    )

    separator = "\n\n━━━━━━━━━━━━━━━━━━━━\n\n"

    final_message = (
        vraj_message +
        separator +
        mom_message
    )

    MAX_MESSAGE_LENGTH = 4000

    for i in range(
        0,
        len(final_message),
        MAX_MESSAGE_LENGTH
    ):

        await update.message.reply_text(
            final_message[
                i:i + MAX_MESSAGE_LENGTH
            ]
        )
async def watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = process_portfolio(all_holdings["watchlist"][:26], "WATCHLIST")
    await update.message.reply_text(message)

async def watchlist2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = process_portfolio(all_holdings["watchlist"][26:], "WATCHLIST 2")
    await update.message.reply_text(message)

async def meenakshi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = process_portfolio(all_holdings["meenakshi"], "MEENAKSHI")
    await update.message.reply_text(message)
async def ashok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = process_portfolio(all_holdings["ashok"], "ASHOK")
    await update.message.reply_text(message)

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

app.add_handler(
    CommandHandler(
        "report",
        report
    )
)
app.add_handler(CommandHandler("watchlist", watchlist))
app.add_handler(CommandHandler("watchlist2", watchlist2))
app.add_handler(CommandHandler("meenakshi", meenakshi))
app.add_handler(CommandHandler("ashok", ashok))

print("Bot Running...")

threading.Thread(
    target=run_web,
    daemon=True
).start()

app.run_polling()