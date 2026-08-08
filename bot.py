import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🛒 فروشگاه", callback_data="shop"),
         InlineKeyboardButton("🧺 سبد خرید", callback_data="cart")],
        [InlineKeyboardButton("📦 سفارش‌های من", callback_data="orders"),
         InlineKeyboardButton("🎁 یو کارت", callback_data="card")],
        [InlineKeyboardButton("👤 حساب من", callback_data="profile"),
         InlineKeyboardButton("💬 پشتیبانی", callback_data="support")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🌿 <b>به سبزی یو خوش آمدید!</b>\n\n"
        "محصولات خانگی سبزی یو را از اینجا ببینید و به‌زودی سفارش خود را ثبت کنید.\n\n"
        "از منوی زیر انتخاب کنید:"
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    messages = {
        "shop": "🛒 <b>فروشگاه سبزی یو</b>\n\nفعلاً بخش محصولات در حال آماده‌سازی است. به‌زودی محصولات سایت SabziU.ir اینجا نمایش داده می‌شوند.",
        "cart": "🧺 سبد خرید شما خالی است.",
        "orders": "📦 هنوز سفارشی ثبت نکرده‌اید.",
        "card": "🎁 <b>یو کارت</b>\n\nامتیاز شما: 0\n\nبا خرید از سبزی یو امتیاز جمع کنید.",
        "profile": "👤 <b>حساب کاربری</b>\n\nاطلاعات حساب شما به‌زودی در این بخش نمایش داده می‌شود.",
        "support": "💬 <b>پشتیبانی سبزی یو</b>\n\nبرای ارتباط با پشتیبانی، پیام خود را ارسال کنید."
    }

    text = messages.get(query.data, "گزینه نامعتبر است.")
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="home")]]
    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def home_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🌿 <b>سبزی یو</b>\n\nاز منوی زیر انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

def run():
    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN تنظیم نشده است. "
            "توکن BotFather را به‌عنوان متغیر محیطی تنظیم کنید."
        )

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(home_handler, pattern="^home$"))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("SabziU bot is running...")
    app.run_polling()

if __name__ == "__main__":
    run()
