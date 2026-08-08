import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set")


products = {
    "sabzi_ghorme": {
        "name": "🌿 سبزی قورمه سرخ‌شده",
        "price": 180000
    },
    "sabzi_kookoo": {
        "name": "🌿 سبزی کوکو",
        "price": 150000
    },
    "torshi": {
        "name": "🥒 ترشی خانگی",
        "price": 120000
    }
}


carts = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🛒 فروشگاه", callback_data="shop")],
        [InlineKeyboardButton("🧺 سبد خرید", callback_data="cart")],
        [InlineKeyboardButton("💚 یو کارت", callback_data="ucard")]
    ]

    await update.message.reply_text(
        "سلام 👋\n"
        "به سبزی‌یو خوش آمدید 🌿",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id


    if query.data == "shop":

        buttons = []

        for key, item in products.items():
            buttons.append([
                InlineKeyboardButton(
                    item["name"],
                    callback_data=key
                )
            ])

        await query.edit_message_text(
            "🛒 محصولات سبزی‌یو:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )


    elif query.data in products:

        item = products[query.data]

        keyboard = [
            [
                InlineKeyboardButton(
                    "➕ افزودن به سبد",
                    callback_data="add_" + query.data
                )
            ],
            [
                InlineKeyboardButton(
                    "🧺 مشاهده سبد خرید",
                    callback_data="cart"
                )
            ]
        ]

        await query.edit_message_text(
            f"{item['name']}\n"
            f"💰 قیمت: {item['price']:,} تومان",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    elif query.data.startswith("add_"):

        product_id = query.data.replace("add_", "")

        if user_id not in carts:
            carts[user_id] = []

        carts[user_id].append(product_id)

        await query.edit_message_text(
            "✅ محصول به سبد خرید اضافه شد.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🧺 مشاهده سبد خرید",
                        callback_data="cart"
                    )
                ]
            ])
        )


    elif query.data == "cart":

        if user_id not in carts or len(carts[user_id]) == 0:

            await query.edit_message_text(
                "🧺 سبد خرید شما خالی است."
            )
            return


        total = 0
        text = "🧺 سبد خرید شما:\n\n"

        for product_id in carts[user_id]:

            item = products[product_id]

            text += f"{item['name']}\n"
            text += f"{item['price']:,} تومان\n\n"

            total += item["price"]


        text += f"💰 مبلغ کل: {total:,} تومان"


        keyboard = [
            [
                InlineKeyboardButton(
                    "📦 ثبت سفارش",
                    callback_data="order"
                )
            ]
        ]


        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    elif query.data == "order":

        await query.edit_message_text(
            "📦 سفارش شما ثبت اولیه شد.\n"
            "مرحله بعد: دریافت نام، تلفن و آدرس."
        )


    elif query.data == "ucard":

        await query.edit_message_text(
            "💚 یو کارت سبزی‌یو\n"
            "امتیاز خرید مشتریان وفادار."
        )


def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
