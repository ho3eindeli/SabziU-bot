import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters


logging.basicConfig(level=logging.INFO)


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


products = {
    "1": {
        "name": "🌿 سبزی قورمه سرخ شده",
        "price": 180000
    },
    "2": {
        "name": "🌿 سبزی کوکو",
        "price": 150000
    },
    "3": {
        "name": "🥒 ترشی خانگی",
        "price": 120000
    }
}


cart = {}

orders = {}



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "🛒 فروشگاه",
                callback_data="shop"
            )
        ],
        [
            InlineKeyboardButton(
                "🧺 سبد خرید",
                callback_data="cart"
            )
        ]
    ]


    await update.message.reply_text(
        "سلام 👋\nبه سبزی‌یو خوش آمدید 🌿",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()


    keyboard = []


    for key, item in products.items():

        keyboard.append(
            [
                InlineKeyboardButton(
                    item["name"],
                    callback_data="product_" + key
                )
            ]
        )


    await query.edit_message_text(
        "🛒 محصولات سبزی‌یو:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()


    user = query.from_user.id


    if query.data == "shop":

        await shop(update, context)



    elif query.data.startswith("product_"):

        pid = query.data.replace("product_", "")

        item = products[pid]


        keyboard = [
            [
                InlineKeyboardButton(
                    "➕ افزودن به سبد",
                    callback_data="add_" + pid
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت به فروشگاه",
                    callback_data="shop"
                )
            ]
        ]


        await query.edit_message_text(
            f"{item['name']}\n"
            f"💰 {item['price']:,} تومان",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
      elif query.data.startswith("add_"):

        pid = query.data.replace("add_", "")


        if user not in cart:

            cart[user] = []


        cart[user].append(pid)


        keyboard = [
            [
                InlineKeyboardButton(
                    "🧺 مشاهده سبد خرید",
                    callback_data="cart"
                )
            ],
            [
                InlineKeyboardButton(
                    "🛒 ادامه خرید",
                    callback_data="shop"
                )
            ]
        ]


        await query.edit_message_text(
            "✅ محصول به سبد خرید اضافه شد.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )



    elif query.data == "cart":


        if user not in cart or len(cart[user]) == 0:


            await query.edit_message_text(
                "🧺 سبد خرید خالی است.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🛒 فروشگاه",
                                callback_data="shop"
                            )
                        ]
                    ]
                )
            )

            return



        text = "🧺 سبد خرید:\n\n"

        total = 0


        for pid in cart[user]:

            item = products[pid]

            text += (
                item["name"]
                + "\n"
                + f"{item['price']:,} تومان\n\n"
            )

            total += item["price"]


        text += f"💰 جمع کل: {total:,} تومان"


        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📦 ثبت سفارش",
                            callback_data="order"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🛒 ادامه خرید",
                            callback_data="shop"
                        )
                    ]
                ]
            )
        )



    elif query.data == "order":


        orders[user] = {
            "step": "name",
            "items": cart[user]
        }


        await query.message.reply_text(
            "👤 نام و نام خانوادگی خود را وارد کنید:"
        )



async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id


    if user in orders and orders[user]["step"] == "name":

        orders[user]["name"] = update.message.text

        orders[user]["step"] = "phone"


        button = KeyboardButton(
            "📱 ارسال شماره تماس",
            request_contact=True
        )


        await update.message.reply_text(
            "شماره تماس را ارسال کنید:",
            reply_markup=ReplyKeyboardMarkup(
                [[button]],
                resize_keyboard=True
            )
        )



async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user.id


    if user not in orders:

        return


    phone = update.message.contact.phone_number


    name = orders[user]["name"]


    await update.message.reply_text(
        "✅ سفارش ثبت شد\n\n"
        f"👤 {name}\n"
        f"📱 {phone}\n\n"
        "🏢 تحویل: هیأت امنا (رایگان)"
    )


    cart.pop(user, None)

    orders.pop(user, None)



def main():

    app = Application.builder().token(TOKEN).build()


    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )


    app.add_handler(
        MessageHandler(
            filters.CONTACT,
            contact
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message
        )
    )


    app.run_polling()



if __name__ == "__main__":

    main()
