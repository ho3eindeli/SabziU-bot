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
    MessageHandler,
    ContextTypes,
    filters
)


logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


products = {
    "ghorme": {
        "name": "🌿 سبزی قورمه سرخ‌شده",
        "price": 180000
    },
    "kookoo": {
        "name": "🌿 سبزی کوکو",
        "price": 150000
    },
    "torshi": {
        "name": "🥒 ترشی خانگی",
        "price": 120000
    }
}


carts = {}
customers = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🛒 فروشگاه", callback_data="shop")],
        [InlineKeyboardButton("🧺 سبد خرید", callback_data="cart")]
    ]

    await update.message.reply_text(
        "سلام 👋\n"
        "به فروشگاه سبزی‌یو خوش آمدید 🌿",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id


    if query.data == "shop":

        keyboard = []

        for key, item in products.items():
            keyboard.append([
                InlineKeyboardButton(
                    item["name"],
                    callback_data=key
                )
            ])


        await query.edit_message_text(
            "🛒 محصولات سبزی‌یو:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    elif query.data in products:

        item = products[query.data]


        await query.edit_message_text(
            f"{item['name']}\n"
            f"💰 قیمت: {item['price']:,} تومان",

            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "➕ افزودن به سبد",
                        callback_data="add_"+query.data
                    )
                ]
            ])
        )


    elif query.data.startswith("add_"):

        product_id = query.data.replace("add_","")


        if user_id not in carts:
            carts[user_id] = []


        carts[user_id].append(product_id)


        await query.edit_message_text(
            "✅ محصول به سبد خرید اضافه شد.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🧺 مشاهده سبد",
                        callback_data="cart"
                    )
                ]
            ])
        )


    elif query.data == "cart":

        if user_id not in carts or not carts[user_id]:

            await query.edit_message_text(
                "🧺 سبد خرید خالی است."
            )

            return


        text = "🧺 سبد خرید شما:\n\n"
        total = 0


        for item_id in carts[user_id]:

            item = products[item_id]

            text += item["name"] + "\n"
            text += f"{item['price']:,} تومان\n\n"

            total += item["price"]


        text += f"💰 مبلغ کل: {total:,} تومان"


        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📦 ثبت سفارش",
                        callback_data="order"
                    )
                ]
            ])
        )


    elif query.data == "order":

        customers[user_id] = {
            "step": "name",
            "cart": carts.get(user_id, [])
        }


        await query.message.reply_text(
            "👤 لطفاً نام و نام خانوادگی خود را وارد کنید:"
        )



async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id


    if user_id in customers and customers[user_id]["step"] == "name":

        customers[user_id]["name"] = update.message.text

        customers[user_id]["step"] = "phone"


        phone_button = KeyboardButton(
            "📱 ارسال شماره تماس",
            request_contact=True
        )


        await update.message.reply_text(
            "لطفاً شماره تماس خود را ارسال کنید:",
            reply_markup=ReplyKeyboardMarkup(
                [[phone_button]],
                resize_keyboard=True
            )
        )



async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id


    if user_id not in customers:
        return


    data = customers[user_id]


    name = data["name"]
    phone = update.message.contact.phone_number


    total = 0
    order_list = ""


    for item_id in data["cart"]:

        item = products[item_id]

        order_list += item["name"] + "\n"

        total += item["price"]


    await update.message.reply_text(
        "✅ سفارش شما ثبت شد\n\n"
        f"👤 نام: {name}\n"
        f"📱 تلفن: {phone}\n\n"
        "🏢 محل تحویل:\n"
        "هیأت امنا (رایگان)\n\n"
        "🛒 سفارش:\n"
        f"{order_list}\n"
        f"💰 مبلغ کل: {total:,} تومان"
    )


    customers.pop(user_id)



def main():

    app = Application.builder().token(TOKEN).build()


    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )


    app.add_handler(
        MessageHandler(
            filters.CONTACT,
            contact_handler
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT,
            text_handler
        )
    )


    app.run_polling()



if __name__ == "__main__":
    main()
