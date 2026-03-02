import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
admin_env = os.getenv("ADMIN_CHAT_ID", "").strip()
ADMIN_CHAT_ID = int(admin_env) if admin_env.isdigit() else 0

CATALOG_PATH = "catalog.json"


def euro(n: float) -> str:
    return f"€{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def load_catalog() -> dict:
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "categories" not in data:
            return {"categories": []}
        return data
    except Exception:
        return {"categories": []}


def get_cart(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.setdefault("cart", {})  # {product_id: qty}


def find_product(catalog: dict, product_id: str):
    for c in catalog.get("categories", []):
        for p in c.get("products", []):
            if p.get("id") == product_id:
                return c, p
    return None, None


def cart_total(catalog: dict, cart: dict) -> float:
    tot = 0.0
    for pid, qty in cart.items():
        _, p = find_product(catalog, pid)
        if p and p.get("active", True):
            tot += float(p.get("price", 0)) * int(qty)
    return tot


def home_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton("🛍 Catalogo", callback_data="cats")],
        [InlineKeyboardButton("📋 Menu disponibile", callback_data="menu_today")],
        [InlineKeyboardButton("💬 Contattami", callback_data="contact")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
        [InlineKeyboardButton("🚚 Delivery", callback_data="delivery")],
        [InlineKeyboardButton("🛒 Carrello", callback_data="cart")],
    ]
    return InlineKeyboardMarkup(kb)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "GhOST3RPz5s • Benvenuto\n\nScegli cosa vuoi fare:",
        reply_markup=home_keyboard(),
    )


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Il tuo chat_id è: {update.effective_chat.id}")


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    catalog = load_catalog()

    # HOME
    if data == "home":
        await q.edit_message_text(
            "GhOST3RPz5s • Menu principale\n\nScegli cosa vuoi fare:",
            reply_markup=home_keyboard(),
        )
        return

    # ====== MENU DISPONIBILE (testo fisso, lo aggiorni quando vuoi) ======
    if data == "menu_today":
        text = (
            "📋 *Menu disponibile*\n\n"
            "• Prodotto A\n"
            "• Prodotto B\n"
            "• Prodotto C\n\n"
            "_Vuoi aggiornare questo testo? Dimmi cosa ci mettiamo e lo impaginiamo._"
        )
        await q.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menu principale", callback_data="home")]]),
        )
        return

    # ====== CONTATTAMI ======
    if data == "contact":
        kb = [
            [InlineKeyboardButton("💬 Scrivimi su Telegram", url="https://t.me/Ghstrpz_5s")],
            [InlineKeyboardButton("📸 Instagram", url="https://instagram.com/ghOst_t3rpz_back")],
            [InlineKeyboardButton("⬅️ Menu principale", callback_data="home")],
        ]
        await q.edit_message_text(
            "💬 *Contatti*\n\nTelegram: @Ghstrpz_5s\nInstagram: @ghOst_t3rpz_back",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return

    # ====== INFO ======
    if data == "info":
        await q.edit_message_text(
            "ℹ️ *Info*\n\n"
            "Brand: GhOST3RPz5s\n"
            "Telegram: @Ghstrpz_5s\n"
            "Instagram: @ghOst_t3rpz_back",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menu principale", callback_data="home")]]),
        )
        return

    # ====== DELIVERY ======
    if data == "delivery":
        text = (
            "🚚 *Delivery*\n\n"
            "• Zone: (scrivi qui)\n"
            "• Orari: (scrivi qui)\n"
            "• Costo: (scrivi qui)\n\n"
            "Per consegna scrivimi su Telegram."
        )
        kb = [
            [InlineKeyboardButton("💬 Richiedi consegna", url="https://t.me/Ghstrpz_5s")],
            [InlineKeyboardButton("⬅️ Menu principale", callback_data="home")],
        ]
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return

    # ====== CATEGORIE ======
    if data == "cats":
        cats = catalog.get("categories", [])
        if not cats:
            await q.edit_message_text(
                "⚠️ Nessun prodotto in vetrina (catalog.json vuoto).",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menu principale", callback_data="home")]]),
            )
            return
        kb = [[InlineKeyboardButton(c.get("name", "Categoria"), callback_data=f"cat:{c.get('id','')}")] for c in cats]
        kb.append([InlineKeyboardButton("🛒 Carrello", callback_data="cart")])
        kb.append([InlineKeyboardButton("⬅️ Menu principale", callback_data="home")])
        await q.edit_message_text("🛍 *Catalogo* • Categorie:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return

    # ====== PRODOTTI DI UNA CATEGORIA ======
    if data.startswith("cat:"):
        cat_id = data.split(":", 1)[1]
        cat = next((c for c in catalog.get("categories", []) if c.get("id") == cat_id), None)
        if not cat:
            await q.edit_message_text(
                "Categoria non trovata.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Catalogo", callback_data="cats")]]),
            )
            return

        products = [p for p in cat.get("products", []) if p.get("active", True)]
        if not products:
            await q.edit_message_text(
                "⚠️ Nessun prodotto disponibile in questa categoria.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Catalogo", callback_data="cats")]]),
            )
            return

        kb = []
        for p in products:
            name = p.get("name", "Prodotto")
            price = float(p.get("price", 0))
            desc = p.get("desc", "")
            label = f"➕ {name} ({euro(price)})"
            if desc:
                label = f"➕ {name} ({euro(price)})"
            kb.append([InlineKeyboardButton(label, callback_data=f"add:{p.get('id')}")])

        kb.append([InlineKeyboardButton("🛒 Carrello", callback_data="cart")])
        kb.append([InlineKeyboardButton("⬅️ Catalogo", callback_data="cats")])
        kb.append([InlineKeyboardButton("⬅️ Menu principale", callback_data="home")])

        await q.edit_message_text(
            f"🖤 *{cat.get('name','Categoria')}*\nSeleziona un prodotto da aggiungere:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return

    # ====== AGGIUNGI AL CARRELLO ======
    if data.startswith("add:"):
        pid = data.split(":", 1)[1]
        _, p = find_product(catalog, pid)
        if not p or not p.get("active", True):
            await q.answer("Prodotto non disponibile.", show_alert=True)
            return
        cart = get_cart(context)
        cart[pid] = cart.get(pid, 0) + 1
        await q.answer("Aggiunto ✅", show_alert=False)
        return

    # ====== CARRELLO ======
    if data == "cart":
        cart = get_cart(context)
        if not cart:
            await q.edit_message_text(
                "🛒 Carrello vuoto.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🛍 Catalogo", callback_data="cats")],
                     [InlineKeyboardButton("⬅️ Menu principale", callback_data="home")]]
                ),
            )
            return

        lines = ["🛒 *Carrello*"]
        for pid, qty in cart.items():
            _, p = find_product(catalog, pid)
            if p:
                price = float(p.get("price", 0))
                lines.append(f"• {p.get('name','Prodotto')} x{qty} — {euro(price*qty)}")

        tot = cart_total(catalog, cart)
        lines.append("")
        lines.append(f"💰 Totale: *{euro(tot)}*")

        kb = [
            [InlineKeyboardButton("✅ Ordina", callback_data="order")],
            [InlineKeyboardButton("🗑️ Svuota", callback_data="clear")],
            [InlineKeyboardButton("🛍 Catalogo", callback_data="cats")],
            [InlineKeyboardButton("⬅️ Menu principale", callback_data="home")],
        ]
        await q.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    # ====== SVUOTA CARRELLO ======
    if data == "clear":
        context.user_data["cart"] = {}
        await q.edit_message_text(
            "🗑️ Carrello svuotato.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menu principale", callback_data="home")]]),
        )
        return

    # ====== ORDINA (ti arriva in privato) ======
    if data == "order":
        cart = get_cart(context)
        if not cart:
            await q.answer("Carrello vuoto.", show_alert=True)
            return

        user = q.from_user
        username = f"@{user.username}" if user.username else "(senza username)"
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tot = cart_total(catalog, cart)

        lines = ["🧾 *NUOVO ORDINE*", f"🕒 {dt}", f"👤 {name} — {username}", ""]
        for pid, qty in cart.items():
            _, p = find_product(catalog, pid)
            if p:
                price = float(p.get("price", 0))
                lines.append(f"• {p.get('name','Prodotto')} x{qty} — {euro(price*qty)}")
        lines.append("")
        lines.append(f"💰 Totale: *{euro(tot)}*")

        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(ADMIN_CHAT_ID, "\n".join(lines), parse_mode="Markdown")
            except Exception:
                pass

        context.user_data["cart"] = {}
        await q.edit_message_text(
            "✅ Ordine inviato! Ti contattiamo a breve.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menu principale", callback_data="home")]]),
        )
        return

    # fallback
    await q.edit_message_text("Comando non riconosciuto.", reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Menu principale", callback_data="home")]]
    ))


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN mancante. Impostalo come variabile d'ambiente su Railway.")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(CallbackQueryHandler(on_button))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
