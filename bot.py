import os
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


NAME, PHONE, ADDRESS = range(3)


PRODUCTS = {
    "1": {
        "name": "🌿 سبزی قورمه سرخ شده",
        "price": 180000,
    },
    "2": {
        "name": "🌿 سبزی کوکو",
        "price": 150000,
    },
    "3": {
        "name": "🥒 ترشی خانگی",
        "price": 120000,
    },
}


carts = {}


def main_menu():
    keyboard = [
        [
            InlineKeyboardButton(
                "🛒 فروشگاه",
                callback_data="shop",
            )
        ],
        [
            InlineKeyboardButton(
                "🧺 سبد خرید",
                callback_data="cart",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def shop_keyboard():
    keyboard = []

    for product_id, product in PRODUCTS.items():
        keyboard.append(
            [
                InlineKeyboardButton(
                    product["name"],
                    callback_data=f"product_{product_id}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "🧺 سبد خرید",
                callback_data="cart",
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)


def product_keyboard(product_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ افزودن به سبد",
                    callback_data=f"add_{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🛒 بازگشت به فروشگاه",
                    callback_data="shop",
                )
            ],
            [
                InlineKeyboardButton(
                    "🧺 سبد خرید",
                    callback_data="cart",
                )
            ],
        ]
    )


def cart_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📦 ثبت سفارش",
                    callback_data="order",
                )
            ],
            [
                InlineKeyboardButton(
                    "🛒 ادامه خرید",
                    callback_data="shop",
                )
            ],
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n"
        "به سبزی‌یو خوش آمدید 🌿\n\n"
        "از منوی زیر انتخاب کنید:",
        reply_markup=main_menu(),
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "shop":
        await query.edit_message_text(
            "🛒 فروشگاه سبزی‌یو\n\n"
            "محصول موردنظر را انتخاب کنید:",
            reply_markup=shop_keyboard(),
        )
        return

    if data.startswith("product_"):
        product_id = data.replace("product_", "")
        product = PRODUCTS.get(product_id)

        if not product:
            await query.edit_message_text(
                "محصول پیدا نشد.",
                reply_markup=shop_keyboard(),
            )
            return

        await query.edit_message_text(
            f"{product['name']}\n\n"
            f"💰 قیمت: {product['price']:,} تومان\n\n"
            "برای افزودن محصول به سبد، دکمه زیر را بزنید.",
            reply_markup=product_keyboard(product_id),
        )
        return

    if data.startswith("add_"):
        product_id = data.replace("add_", "")

        if product_id not in PRODUCTS:
            await query.edit_message_text(
                "محصول پیدا نشد.",
                reply_markup=shop_keyboard(),
            )
            return

        if user_id not in carts:
            carts[user_id] = []

        carts[user_id].append(product_id)

        await query.edit_message_text(
            "✅ محصول به سبد خرید اضافه شد.\n\n"
            "می‌توانید خرید را ادامه دهید یا سبد خرید را ببینید.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🧺 سبد خرید",
                            callback_data="cart",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🛒 ادامه خرید",
                            callback_data="shop",
                        )
                    ],
                ]
            ),
        )
        return

    if data == "cart":
        await show_cart(query, user_id)
        return

    if data == "order":
        if not carts.get(user_id):
            await query.edit_message_text(
                "🧺 سبد خرید شما خالی است.",
                reply_markup=shop_keyboard(),
            )
            return

        context.user_data["order_items"] = list(carts[user_id])

        await query.message.reply_text(
            "📦 ثبت سفارش\n\n"
            "لطفاً نام و نام خانوادگی خود را وارد کنید:"
        )

        context.user_data["order_step"] = "name"

        return


async def show_cart(query, user_id):
    items = carts.get(user_id, [])

    if not items:
        await query.edit_message_text(
            "🧺 سبد خرید شما خالی است.",
            reply_markup=shop_keyboard(),
        )
        return

    total = 0
    lines = ["🧺 سبد خرید شما:\n"]

    for index, product_id in enumerate(items, start=1):
        product = PRODUCTS[product_id]

        lines.append(
            f"{index}. {product['name']}\n"
            f"   {product['price']:,} تومان\n"
        )

        total += product["price"]

    lines.append(f"\n💰 جمع کل: {total:,} تومان")

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=cart_keyboard(),
    )


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    step = context.user_data.get("order_step")

    if step == "name":
        context.user_data["name"] = text
        context.user_data["order_step"] = "phone"

        keyboard = [
            [
                KeyboardButton(
                    "📱 ارسال شماره تلفن",
                    request_contact=True,
                )
            ]
        ]

        await update.message.reply_text(
            "📱 لطفاً شماره تلفن خود را با زدن دکمه زیر ارسال کنید:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return

    if step == "phone":
        context.user_data["phone"] = text
        context.user_data["order_step"] = "address"

        await update.message.reply_text(
            "📍 لطفاً آدرس کامل تحویل را وارد کنید:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if step == "address":
        context.user_data["address"] = text

        name = context.user_data.get("name", "")
        phone = context.user_data.get("phone", "")
        address = context.user_data.get("address", "")
        items = context.user_data.get("order_items", [])

        total = 0
        order_lines = []

        for product_id in items:
            product = PRODUCTS[product_id]
            total += product["price"]
            order_lines.append(
                f"• {product['name']} — {product['price']:,} تومان"
            )

        order_text = (
            "🎉 سفارش شما با موفقیت ثبت شد!\n\n"
            f"👤 نام: {name}\n"
            f"📱 تلفن: {phone}\n"
            f"📍 آدرس: {address}\n\n"
            "🛍 محصولات:\n"
            + "\n".join(order_lines)
            + f"\n\n💰 مبلغ کل: {total:,} تومان\n"
            "🚚 تحویل: هیأت امنا — رایگان"
        )

        await update.message.reply_text(
            order_text,
            reply_markup=main_menu(),
        )

        carts.pop(user_id, None)
        context.user_data.clear()
        return

    await update.message.reply_text(
        "برای شروع، /start را بزنید."
    )


async def contact_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id
    contact = update.message.contact

    step = context.user_data.get("order_step")

    if step != "phone":
        await update.message.reply_text(
            "در حال حاضر سفارشی در حال ثبت نیست."
        )
        return

    phone = contact.phone_number

    context.user_data["phone"] = phone
    context.user_data["order_step"] = "address"

    await update.message.reply_text(
        "✅ شماره تلفن دریافت شد.\n\n"
        "📍 حالا لطفاً آدرس کامل تحویل را وارد کنید:",
        reply_markup=ReplyKeyboardRemove(),
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "❌ ثبت سفارش لغو شد.",
        reply_markup=main_menu(),
    )


def main():
    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN تنظیم نشده است."
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("cancel", cancel)
    )

    app.add_handler(
        CallbackQueryHandler(buttons)
    )

    app.add_handler(
        MessageHandler(
            filters.CONTACT,
            contact_message,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message,
        )
    )

    print("SabziU bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()