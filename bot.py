import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set")


products = {
    "sabzi_ghorme": "🌿 سبزی قورمه سرخ‌شده\n۵۰۰ گرم - ۱۸۰ هزار تومان",
    "sabzi_kookoo": "🌿 سبزی کوکو\n۵۰۰ گرم - ۱۵۰ هزار تومان",
    "torshi": "🥒 ترشی خانگی\n۷۰۰ گرم - ۱۲۰ هزار تومان",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🛒 فروشگاه", callback_data="shop")],
        [InlineKeyboardButton("📦 سفارش‌های من", callback_data="orders")],
        [InlineKeyboardButton("💚 یو کارت", callback_data="ucard")],
    ]

    await update.message.reply_text(
        "سلام 👋\n"
        "به فروشگاه سبزی‌یو خوش آمدید 🌿\n\n"
        "محصول موردنظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "shop":

        keyboard = []

        for key in products:
            keyboard.append([
                InlineKeyboardButton(
                    products[key].split("\n")[0],
                    callback_data=key
                )
            ])

        await query.edit_message_text(
            "🛒 محصولات سبزی‌یو:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    elif query.data in products:

        keyboard = [
            [
                InlineKeyboardButton(
                    "🛍 افزودن به سبد خرید",
                    callback_data="add_" + query.data
                )
            ]
        ]

        await query.edit_message_text(
            products[query.data],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    elif query.data.startswith("add_"):

        await query.edit_message_text(
            "✅ محصول به سبد خرید اضافه شد.\n"
            "به‌زودی مرحله ثبت سفارش اضافه می‌شود."
        )


    elif query.data == "orders":

        await query.edit_message_text(
            "📦 هنوز سفارشی ثبت نشده است."
        )


    elif query.data == "ucard":

        await query.edit_message_text(
            "💚 یو کارت سبزی‌یو\n"
            "امتیاز خرید و تخفیف مشتریان وفادار."
        )


def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
