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


if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is missing")



# محصولات سبزی یو

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



# سبد کاربران

carts = {}


# وضعیت سفارش کاربران

customers = {}



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

        "سلام 👋\n"
        "به فروشگاه سبزی‌یو خوش آمدید 🌿\n\n"
        "از منوی زیر انتخاب کنید:",

        reply_markup=InlineKeyboardMarkup(keyboard)

    )




async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()


    user_id = query.from_user.id



    # نمایش فروشگاه

    if query.data == "shop":


        keyboard = []


        for key, item in products.items():

            keyboard.append(
                [
                    InlineKeyboardButton(
                        item["name"],
                        callback_data=key
                    )
                ]
            )


        await query.edit_message_text(

            "🛒 محصولات سبزی‌یو:",

            reply_markup=InlineKeyboardMarkup(keyboard)

        )



    # انتخاب محصول

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
                    "🧺 مشاهده سبد",
                    callback_data="cart"
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
            f"💰 قیمت: {item['price']:,} تومان",

            reply_markup=InlineKeyboardMarkup(keyboard)

        )
            # افزودن به سبد خرید

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

                ],

                [

                    InlineKeyboardButton(
                        "🛒 ادامه خرید",
                        callback_data="shop"
                    )

                ]

            ])

        )



    # نمایش سبد خرید

    elif query.data == "cart":


        if user_id not in carts or len(carts[user_id]) == 0:


            await query.edit_message_text(
                "🧺 سبد خرید شما خالی است.",
                reply_markup=InlineKeyboardMarkup([

                    [

                        InlineKeyboardButton(
                            "🛒 رفتن به فروشگاه",
                            callback_data="shop"
                        )

                    ]

                ])
            )

            return



        text = "🧺 سبد خرید شما:\n\n"

        total = 0



        for product_id in carts[user_id]:

            item = products[product_id]


            text += (
                f"{item['name']}\n"
                f"{item['price']:,} تومان\n\n"
            )


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

                ],

                [

                    InlineKeyboardButton(
                        "🛒 ادامه خرید",
                        callback_data="shop"
                    )

                ]

            ])

        )



    # شروع ثبت سفارش

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



    customer = customers[user_id]


    name = customer["name"]

    phone = update.message.contact.phone_number



    total = 0

    order_items = ""



    for product_id in customer["cart"]:


        item = products[product_id]


        order_items += (

            f"{item['name']}\n"

            f"{item['price']:,} تومان\n\n"

        )


        total += item["price"]




    await update.message.reply_text(

        "✅ سفارش شما ثبت شد\n\n"

        f"👤 نام: {name}\n"

        f"📱 تلفن: {phone}\n\n"

        "🏢 محل تحویل:\n"

        "هیأت امنا (رایگان)\n\n"

        "🛒 سفارش:\n"

        f"{order_items}"

        f"💰 مبلغ کل: {total:,} تومان"

    )



    customers.pop(user_id, None)

    carts.pop(user_id, None)




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

            button_handler

        )

    )



    app.add_handler(

        MessageHandler(

            filters.CONTACT,

            contact_handler

        )

    )



    app.add_handler(

        MessageHandler(

            filters.TEXT & ~filters.COMMAND,

            text_handler

        )

    )



    app.run_polling()




if __name__ == "__main__":

    main()
