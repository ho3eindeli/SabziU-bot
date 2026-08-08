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

order_step = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🛒 فروشگاه", callback_data="shop")],
        [InlineKeyboardButton("🧺 سبد خرید", callback_data="cart")]
    ]

    await update.message.reply_text(
        "سلام 👋\nبه سبزی‌یو خوش آمدید 🌿",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user.id


    if query.data == "shop":

        keyboard=[]

        for key,item in products.items():
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

        item=products[query.data]

        await query.edit_message_text(
            f"{item['name']}\n"
            f"💰 {item['price']:,} تومان",

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

        pid=query.data.replace("add_","")

        if user not in carts:
            carts[user]=[]

        carts[user].append(pid)

        await query.edit_message_text(
            "✅ به سبد خرید اضافه شد.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🧺 سبد خرید",
                        callback_data="cart"
                    )
                ]
            ])
        )


    elif query.data=="cart":

        if user not in carts or len(carts[user])==0:
            await query.edit_message_text(
                "🧺 سبد خرید خالی است."
            )
            return


        text="🧺 سبد خرید:\n\n"
        total=0

        for pid in carts[user]:

            item=products[pid]

            text += item["name"]+"\n"
            text += f"{item['price']:,} تومان\n\n"

            total+=item["price"]


        text+=f"💰 مجموع: {total:,} تومان"


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


    elif query.data=="order":

        order_step[user]="name"

        await query.message.reply_text(
            "👤 نام و نام خانوادگی خود را وارد کنید:"
        )



async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user=update.message.from_user.id


    if order_step.get(user)=="name":

        context.user_data["name"]=update.message.text

        order_step[user]="phone"


        button=KeyboardButton(
            "📱 ارسال شماره تماس",
            request_contact=True
        )


        await update.message.reply_text(
            "شماره تماس خود را ارسال کنید:",
            reply_markup=ReplyKeyboardMarkup(
                [[button]],
                resize_keyboard=True
            )
        )


    else:

        pass




async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user=update.message.from_user.id


    if order_step.get(user)=="phone":

        name=context.user_data["name"]

        phone=update.message.contact.phone_number


        total=0
        items=""


        for pid in carts.get(user,[]):

            item=products[pid]

            items+=item["name"]+"\n"

            total+=item["price"]



        await update.message.reply_text(
            "✅ سفارش شما ثبت شد\n\n"
            f"👤 نام: {name}\n"
            f"📱 تلفن: {phone}\n\n"
            "🏢 محل تحویل:\n"
            "هیأت امنا (رایگان)\n\n"
            "🛒 محصولات:\n"
            f"{items}\n"
            f"💰 مبلغ: {total:,} تومان"
        )


        order_step[user]=None



def main():

    app=Application.builder().token(TOKEN).build()


    app.add_handler(CommandHandler("start",start))

    app.add_handler(
        CallbackQueryHandler(buttons)
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



if __name__=="__main__":
    main()
