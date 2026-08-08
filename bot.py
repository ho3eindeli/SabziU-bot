import os
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters
)


logging.basicConfig(level=logging.INFO)


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set")


# مراحل فرم سفارش
NAME, PHONE = range(2)


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


orders = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🛒 فروشگاه", callback_data="shop")],
        [InlineKeyboardButton("🧺 سبد خرید", callback_data="cart")]
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
            buttons.append(
                [
                    InlineKeyboardButton(
                        item["name"],
                        callback_data=key
                    )
                ]
            )


        await query.edit_message_text(
            "🛒 محصولات سبزی‌یو:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )



    elif query.data in products:

        item = products[query.data]

        await query.edit_message_text(
            f"{item['name']}\n"
            f"💰 قیمت: {item['price']:,} تومان",

            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "➕ افزودن به سبد",
                            callback_data="add_" + query.data
                        )
                    ]
                ]
            )
        )



    elif query.data.startswith("add_"):

        product_id = query.data.replace("add_", "")


        if user_id not in carts:
            carts[user_id] = []


        carts[user_id].append(product_id)


        await query.edit_message_text(
            "✅ محصول به سبد خرید اضافه شد.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🧺 مشاهده سبد خرید",
                            callback_data="cart"
                        )
                    ]
                ]
            )
        )



    elif query.data == "cart":


        if user_id not in carts or not carts[user_id]:

            await query.edit_message_text(
                "🧺 سبد خرید شما خالی است."
            )

            return


        text = "🧺 سبد خرید شما:\n\n"

        total = 0


        for p in carts[user_id]:

            item = products[p]

            text += item["name"] + "\n"
            text += f"{item['price']:,} تومان\n\n"

            total += item["price"]


        text += f"💰 مبلغ کل: {total:,} تومان"


        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📦 ثبت سفارش",
                            callback_data="order"
                        )
                    ]
                ]
            )
        )



    elif query.data == "order":

        await query.message.reply_text(
            "👤 لطفاً نام و نام خانوادگی خود را وارد کنید:"
        )

        context.user_data["cart"] = carts.get(user_id, [])

        return NAME




async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["name"] = update.message.text


    button = KeyboardButton(
        "📱 ارسال شماره تماس",
        request_contact=True
    )


    await update.message.reply_text(
        "شماره تماس خود را ارسال کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [[button]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )


    return PHONE



async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):

    phone = update.message.contact.phone_number

    name = context.user_data["name"]


    user_id = update.message.from_user.id


    total = 0
    order_text = ""


    for p in context.user_data["cart"]:

        item = products[p]

        order_text += item["name"] + "\n"

        total += item["price"]



    await update.message.reply_text(
        "✅ سفارش شما ثبت شد\n\n"
        f"👤 نام: {name}\n"
        f"📱 تلفن: {phone}\n\n"
        "🏢 محل تحویل:\n"
        "هیأت امنا (رایگان)\n\n"
        "🛒 سفارش:\n"
        f"{order_text}\n"
        f"💰 مبلغ کل: {total:,} تومان"
    )


    return ConversationHandler.END




def main():

    app = Application.builder().token(TOKEN).build()


    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                button_handler,
                pattern="^order$"
            )
        ],

        states={
            NAME: [
                MessageHandler(
                    filters.TEXT,
                    get_name
                )
            ],

            PHONE: [
                MessageHandler(
                    filters.CONTACT,
                    get_phone
                )
            ]
        },

        fallbacks=[]
    )


    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    app.add_handler(conv)


    app.run_polling()



if __name__ == "__main__":
    main()
