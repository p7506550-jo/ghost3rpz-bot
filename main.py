import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()

admin_env = os.getenv("ADMIN_CHAT_ID", "").strip()
ADMIN_CHAT_ID = int(admin_env) if admin_env.isdigit() else 0


def money_eur(n: float) -> str:
    try:
        return f"€{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return f"€{n}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🛍 Catalogo", callback_data="cats")],
        [InlineKeyboardButton("📋 Menu disponibile", callback_data="menu_today")],
        [InlineKeyboardButton("💬 Contattami", callback_data="contact")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
        [InlineKeyboardButton("🚚 Delivery", callback_data="delivery")],
    ]
    await update.message.reply_text(
        "GhOST3RPz5s • Benvenuto\n\nScegli cosa vuoi fare:",
        reply_markup=InlineKeyboardMarkup(kb),
    )

    kb = [[InlineKeyboardButton("🛒 Apri catalogo", web_app=WebAppInfo(url=WEBAPP_URL))]]
    await update.message.reply_text(
        "GhOST3RPz5s • Catalogo\n\nPremi il bottone qui sotto per aprire il catalogo e ordinare.",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Il tuo chat_id è: {update.effective_chat.id}\n"
        "Copia questo numero e mettilo in ADMIN_CHAT_ID su Render."
    )


async def on_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg or not msg.web_app_data:
        return

    try:
        payload = json.loads(msg.web_app_data.data)
    except Exception:
        await msg.reply_text("❌ Dati ordine non validi.")
        return

    user = msg.from_user
    username = f"@{user.username}" if user and user.username else "(senza username)"
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() if user else "Utente"
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    items = payload.get("items", [])
    total = payload.get("total", 0)

    lines = []
    lines.append("🧾 *NUOVO ORDINE*")
    lines.append(f"🕒 {dt}")
    lines.append(f"👤 {name} — {username}")
    lines.append("")
    for it in items:
        nm = it.get("name", "Item")
        qty = it.get("qty", 1)
        price = it.get("price", None)
        if isinstance(price, (int, float)):
            lines.append(f"• {nm} x{qty} ({money_eur(price)})")
        else:
            lines.append(f"• {nm} x{qty} (prezzo su richiesta)")
    lines.append("")
    if isinstance(total, (int, float)):
        lines.append(f"💰 Totale stimato: *{money_eur(total)}*")

    text = "\n".join(lines)

    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode="Markdown")
        except Exception:
            pass

    await msg.reply_text("✅ Ordine ricevuto! Ti rispondiamo a breve.")


def build_app() -> Application:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN mancante. Impostalo come variabile d'ambiente su Render.")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, on_webapp_data))
    return app


if __name__ == "__main__":
    build_app().run_polling(allowed_updates=Update.ALL_TYPES)
