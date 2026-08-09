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
    filters,
)


# =========================
# تنظیمات
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# =========================
# محصولات
# =========================

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


# سبد خرید کاربران
carts = {}


# =========================
# منوها
# =========================

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


def delivery_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🏢 هیأت امنا — رایگان",
                    callback_data="delivery_heyat",
                )
            ],
            [
                InlineKeyboardButton(
                    "🕌 مسجد مولای متقیان — رایگان",
                    callback_data="delivery_mola",
                )
            ],
        ]
    )


def final_order_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ تأیید و ثبت سفارش",
                    callback_data="confirm_order",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ لغو سفارش",
                    callback_data="cancel_order",
                )
            ],
        ]
    )


# =========================
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "سلام 👋\n"
        "به سبزی‌یو خوش آمدید 🌿\n\n"
        "از منوی زیر انتخاب کنید:",
        reply_markup=main_menu(),
    )


# =========================
# نمایش سبد خرید
# =========================

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
            f"   💰 {product['price']:,} تومان\n"
        )

        total += product["price"]

    lines.append(
        f"\n💰 جمع کل: {total:,} تومان"
    )

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=cart_keyboard(),
    )


# =========================
# دکمه‌های اینلاین
# =========================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    # -------------------------
    # فروشگاه
    # -------------------------

    if data == "shop":
        await query.edit_message_text(
            "🛒 فروشگاه سبزی‌یو\n\n"
            "محصول موردنظر را انتخاب کنید:",
            reply_markup=shop_keyboard(),
        )
        return

    # -------------------------
    # نمایش محصول
    # -------------------------

    if data.startswith("product_"):
        product_id = data.replace("product_", "")
        product = PRODUCTS.get(product_id)

        if not product:
            await query.edit_message_text(
                "❌ محصول پیدا نشد.",
                reply_markup=shop_keyboard(),
            )
            return

        await query.edit_message_text(
            f"{product['name']}\n\n"
            f"💰 قیمت: {product['price']:,} تومان\n\n"
            "برای اضافه کردن محصول به سبد، دکمه زیر را بزنید:",
            reply_markup=product_keyboard(product_id),
        )
        return

    # -------------------------
    # افزودن محصول
    # -------------------------

    if data.startswith("add_"):
        product_id = data.replace("add_", "")

        if product_id not in PRODUCTS:
            await query.edit_message_text(
                "❌ محصول پیدا نشد.",
                reply_markup=shop_keyboard(),
            )
            return

        if user_id not in carts:
            carts[user_id] = []

        carts[user_id].append(product_id)

        await query.edit_message_text(
            "✅ محصول به سبد خرید اضافه شد.\n\n"
            "می‌توانید خرید را ادامه دهید یا سبد خرید را مشاهده کنید.",
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

    # -------------------------
    # سبد خرید
    # -------------------------

    if data == "cart":
        await show_cart(query, user_id)
        return

    # -------------------------
    # شروع ثبت سفارش
    # -------------------------

    if data == "order":
        if not carts.get(user_id):
            await query.edit_message_text(
                "🧺 سبد خرید شما خالی است.",
                reply_markup=shop_keyboard(),
            )
            return

        context.user_data["order_items"] = list(
            carts[user_id]
        )

        context.user_data["order_step"] = "name"

        await query.message.reply_text(
            "📦 ثبت سفارش\n\n"
            "لطفاً نام و نام خانوادگی خود را وارد کنید:"
        )

        return

    # -------------------------
    # انتخاب هیأت امنا
    # -------------------------

    if data == "delivery_heyat":
        context.user_data["delivery"] = (
            "هیأت امنا"
        )

        await show_order_summary(
            query,
            context,
        )
        return

    # -------------------------
    # انتخاب مسجد
    # -------------------------

    if data == "delivery_mola":
        context.user_data["delivery"] = (
            "مسجد مولای متقیان"
        )

        await show_order_summary(
            query,
            context,
        )
        return

    # -------------------------
    # تأیید سفارش
    # -------------------------

    if data == "confirm_order":
        name = context.user_data.get("name", "")
        phone = context.user_data.get("phone", "")
        delivery = context.user_data.get(
            "delivery",
            "",
        )

        items = context.user_data.get(
            "order_items",
            [],
        )

        total = 0
        order_lines = []

        for product_id in items:
            product = PRODUCTS[product_id]

            total += product["price"]

            order_lines.append(
                f"• {product['name']} — "
                f"{product['price']:,} تومان"
            )

        final_text = (
            "🎉 سفارش شما با موفقیت ثبت شد!\n\n"
            f"👤 نام: {name}\n"
            f"📱 تلفن: {phone}\n"
            f"📍 محل تحویل: {delivery}\n"
            "🚚 هزینه تحویل: رایگان\n\n"
            "🛍 محصولات:\n"
            + "\n".join(order_lines)
            + f"\n\n💰 مبلغ کل: {total:,} تومان"
        )

        await query.edit_message_text(
            final_text,
            reply_markup=main_menu(),
        )

        # خالی کردن سبد
        carts.pop(user_id, None)

        # پاک کردن اطلاعات سفارش
        context.user_data.clear()

        return

    # -------------------------
    # لغو سفارش
    # -------------------------

    if data == "cancel_order":
        context.user_data.clear()

        await query.edit_message_text(
            "❌ سفارش لغو شد.",
            reply_markup=main_menu(),
        )

        return


# =========================
# خلاصه سفارش
# =========================

async def show_order_summary(
    query,
    context,
):
    name = context.user_data.get(
        "name",
        "",
    )

    phone = context.user_data.get(
        "phone",
        "",
    )

    delivery = context.user_data.get(
        "delivery",
        "",
    )

    items = context.user_data.get(
        "order_items",
        [],
    )

    total = 0
    order_lines = []

    for product_id in items:
        product = PRODUCTS[product_id]

        total += product["price"]

        order_lines.append(
            f"• {product['name']} — "
            f"{product['price']:,} تومان"
        )

    summary = (
        "📋 لطفاً اطلاعات سفارش را بررسی کنید:\n\n"
        f"👤 نام: {name}\n"
        f"📱 تلفن: {phone}\n"
        f"📍 محل تحویل: {delivery}\n"
        "🚚 هزینه تحویل: رایگان\n\n"
        "🛍 محصولات:\n"
        + "\n".join(order_lines)
        + f"\n\n💰 مبلغ کل: {total:,} تومان\n\n"
        "اگر اطلاعات صحیح است، تأیید و ثبت سفارش را بزنید."
    )

    await query.edit_message_text(
        summary,
        reply_markup=final_order_keyboard(),
    )


# =========================
# پیام‌های متنی
# =========================

async def text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    step = context.user_data.get(
        "order_step"
    )

    # -------------------------
    # نام
    # -------------------------

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

    # -------------------------
    # اگر کاربر شماره را دستی نوشت
    # -------------------------

    if step == "phone":
        context.user_data["phone"] = text
        context.user_data["order_step"] = "delivery"

        await update.message.reply_text(
            "📍 محل تحویل سفارش را انتخاب کنید:",
            reply_markup=delivery_keyboard(),
        )

        return

    # -------------------------
    # سایر پیام‌ها
    # -------------------------

    await update.message.reply_text(
        "برای شروع خرید، /start را بزنید.",
        reply_markup=main_menu(),
    )


# =========================
# دریافت شماره تلفن
# =========================

async def contact_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    step = context.user_data.get(
        "order_step"
    )

    if step != "phone":
        await update.message.reply_text(
            "در حال حاضر در مرحله دریافت شماره تلفن نیستیم."
        )
        return

    phone = update.message.contact.phone_number

    context.user_data["phone"] = phone
    context.user_data["order_step"] = "delivery"

    await update.message.reply_text(
        "✅ شماره تلفن دریافت شد.\n\n"
        "📍 محل تحویل سفارش را انتخاب کنید:",
        reply_markup=ReplyKeyboardRemove(),
    )

    await update.message.reply_text(
        "لطفاً یکی از دو محل تحویل را انتخاب کنید:",
        reply_markup=delivery_keyboard(),
    )


# =========================
# لغو با /cancel
# =========================

async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.clear()

    await update.message.reply_text(
        "❌ ثبت سفارش لغو شد.",
        reply_markup=main_menu(),
    )


# =========================
# اجرای ربات
# =========================

def main():
    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN تنظیم نشده است."
        )

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    # /start
    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    # /cancel
    app.add_handler(
        CommandHandler(
            "cancel",
            cancel,
        )
    )

    # دکمه‌های اینلاین
    app.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )

    # شماره تلفن
    app.add_handler(
        MessageHandler(
            filters.CONTACT,
            contact_message,
        )
    )

    # پیام‌های متنی
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message,
        )
    )

    print(
        "SabziU bot is running..."
    )

    app.run_polling()


# =========================
# شروع
# =========================

if __name__ == "__main__":
    main()
