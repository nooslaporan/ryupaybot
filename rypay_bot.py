import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import json
import os

# === KONFIGURASI ===
TOKEN = "8022360140:AAHOAt9P66lOB7jmflBioZfziQHLObZTYQQ"
KURS = 17200  # Atur ke 17200 kalau perlu
FEE_PERSEN = 3.5
DATA_FILE = "data.json"

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FUNGSI UTILITY ===

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_today_transactions():
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    return [d for d in data if d["date"] == today]

# === HANDLER ===

async def tambah_transaksi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        if not text.startswith("+"):
            return
        nominal = int(text[1:].strip())
        now = datetime.now()
        entry = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "amount": nominal
        }
        data = load_data()
        data.append(entry)
        save_data(data)
        await update.message.reply_text(f"✅ Transaksi masuk: {nominal:,}")
    except Exception as e:
        await update.message.reply_text("⚠️ Format salah. Gunakan: `+ 1000000`")
        logger.error(e)

async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    trx = get_today_transactions()
    if not trx:
        await update.message.reply_text("📭 Belum ada transaksi hari ini.")
        return

    total = sum(t["amount"] for t in trx)
    fee = total * FEE_PERSEN / 100
    harus_dikirim = total - fee
    usdt = harus_dikirim / KURS

    text = "📊 *Laporan Hari Ini*\n"
    for t in trx:
        text += f"{t['time']} — {t['amount']:,}\n"
    text += f"\n*Total:* {total:,}"
    text += f"\n*Kurs:* {KURS}"
    text += f"\n*Fee:* {FEE_PERSEN}%"
    text += f"\n\n*Harus Dikirim:* {harus_dikirim:,.2f} | {usdt:.2f}U"
    text += f"\n*Sudah Dikirim:* 0 | 0U"
    text += f"\n*Belum Dikirim:* {harus_dikirim:,.2f} | {usdt:.2f}U"

    await update.message.reply_text(text, parse_mode="Markdown")

# === START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Kirim `+ nominal` untuk catat transaksi.\nKetik /laporan untuk lihat laporan hari ini.")

# === MAIN ===
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("laporan", laporan))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), tambah_transaksi))

    logger.info("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
