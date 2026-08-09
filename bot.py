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
# محصولات سبزی یو
# =========================

PRODUCTS = {

    # -------------------------
    # سرخ شده
    # -------------------------

    "fried_1": {
        "name": "سبزی قورمه سرخ‌شده",
        "size": "۵۰۰ گرم",
        "price": 280000,
        "category": "fried",
    },

    "fried_2": {
        "name": "سبزی کرفس (مخلوط)",
        "size": "۵۰۰ گرم",
        "price": 280000,
        "category": "fried",
    },

    "fried_3": {
        "name": "سبزی کرفس (بدون ساقه)",
        "size": "۵۰۰ گرم",
        "price": 280000,
        "category": "fried",
    },

    "fried_4": {
        "name": "ساقه کرفس (بدون سبزی)",
        "size": "۵۰۰ گرم",
        "price": 280000,
        "category": "fried",
    },

    "fried_5": {
        "name": "اسفناج سرخ‌شده",
        "size": "۵۰۰ گرم",
        "price": 280000,
        "category": "fried",
    },

    "fried_6": {
        "name": "قلیه ماهی",
        "size": "۵۰۰ گرم",
        "price": 280000,
        "category": "fried",
    },

    "fried_7": {
        "name": "لوبیا سرخ‌شده",
        "size": "۵۰۰ گرم",
        "price": 280000,
        "category": "fried",
    },

    "fried_8": {
        "name": "بادمجان سرخ‌شده",
        "size": "۱ کیلو",
        "price": 190000,
        "category": "fried",
    },

    "fried_9": {
        "name": "بادمجان کبابی",
        "size": "۱ کیلو",
        "price": 190000,
        "category": "fried",
    },


    # -------------------------
    # سبزی خام
    # -------------------------

    "raw_1": {
        "name": "سبزی آش",
        "size": "۵۰۰ گرم",
        "price": 280000,
        "category": "raw",
    },

    "raw_2": {
        "name": "کوکو سبزی",
        "size": "۵۰۰ گرم",
        "price": 280000,
        "category": "raw",
    },


    # -------------------------
    # ترشیجات
    # -------------------------

    "pickle_1": {
        "name": "ترشی نازخاتون",
        "size": "۵۰۰ گرم",
        "price": 300000,
        "category": "pickles",
    },

    "pickle_2": {
        "name": "ترشی بندری",
        "size": "۵۰۰ گرم",
        "price": 250000,
        "category": "pickles",
    },


    # -------------------------
    # شربت و مربا
    # -------------------------

    "syrup_1": {
        "name": "شربت انبه زعفران",
        "size": "۱ لیتر",
        "price": 550000,
        "category": "syrup",
    },

    "syrup_2": {
        "name": "شربت انبه زعفران",
        "size": "۱.۵ لیتر",
        "price": 750000,
        "category": "syrup",
    },

    "syrup_3": {
        "name": "شربت آلبالو",
        "size": "۱ لیتر",
        "price": 350000,
        "category": "syrup",
    },

    "syrup_4": {
        "name": "شربت آلبالو",
        "size": "۱.۵ لیتر",
        "price": 450000,
        "category": "syrup",
    },

    "syrup_5": {
        "name": "شربت هل و زعفران",
        "size": "۱ لیتر",
        "price": 400000,
        "category": "syrup",
    },

    "syrup_6": {
        "name": "شربت هل و زعفران",
        "size": "۱.۵ لیتر",
        "price": 500000,
        "category": "syrup",
    },
}


# =========================
# سبد خرید
# =========================

carts = {}


# =========================
# منوی اصلی
# =========================

def main_menu():

    keyboard = [
        [
            InlineKeyboardButton(
                "🛒 فروشگاه سبزی‌یو",
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


# =========================
# دسته‌بندی فروشگاه
# =========================

def categories_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                "🌿 سبزی‌های سرخ‌شده",
                callback_data="category_fried",
            )
        ],
        [
            InlineKeyboardButton(
                "🥬 سبزی‌های خام",
                callback_data="category_raw",
            )
        ],
        [
            InlineKeyboardButton(
                "🥒 ترشیجات",
                callback_data="category_pickles",
            )
        ],
        [
            InlineKeyboardButton(
                "🥭 شربت‌ها و مربا",
                callback_data="category_syrup",
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


# =========================
# محصولات هر دسته
# =========================

def category_keyboard(category):

    keyboard = []

    for product_id, product in PRODUCTS.items():

        if product["category"] == category:

            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{product['name']} | {product['size']}",
                        callback_data=f"product_{product_id}",
                    )
                ]
            )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ بازگشت به فروشگاه",
                callback_data="shop",
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


# =========================
# صفحه محصول
# =========================

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
                    "🛒 ادامه خرید",
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


# =========================
# منوی سبد خرید
# =========================

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


# =========================
# محل تحویل
# =========================

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


# =========================
# تأیید سفارش
# =========================

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
# شروع
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    context.user_data.clear()

    await update.message.reply_text(
        "سلام 👋\n\n"
        "به فروشگاه سبزی‌یو خوش آمدید 🌿\n\n"
        "از منوی زیر انتخاب کنید:",
        reply_markup=main_menu(),
    )


# =========================
# نمایش سبد خرید
# =========================

async def show_cart(
    query,
    user_id,
):

    items = carts.get(user_id, [])

    if not items:

        await query.edit_message_text(
            "🧺 سبد خرید شما خالی است.",
            reply_markup=categories_keyboard(),
        )

        return

    total = 0

    lines = [
        "🧺 سبد خرید شما:\n"
    ]

    for index, product_id in enumerate(
        items,
        start=1,
    ):

        product = PRODUCTS[product_id]

        total += product["price"]

        lines.append(
            f"{index}. {product['name']}\n"
            f"   {product['size']} — "
            f"{product['price']:,} تومان\n"
        )

    lines.append(
        f"\n💰 جمع کل: {total:,} تومان"
    )

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=cart_keyboard(),
    )


# =========================
# دکمه‌ها
# =========================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    data = query.data


    # =====================
    # فروشگاه
    # =====================

    if data == "shop":

        await query.edit_message_text(
            "🛒 فروشگاه سبزی‌یو\n\n"
            "دسته‌بندی موردنظر را انتخاب کنید:",
            reply_markup=categories_keyboard(),
        )

        return


    # =====================
    # دسته سرخ‌شده
    # =====================

    if data == "category_fried":

        await query.edit_message_text(
            "🌿 سبزی‌های سرخ‌شده\n\n"
            "محصول موردنظر را انتخاب کنید:",
            reply_markup=category_keyboard(
                "fried"
            ),
        )

        return


    # =====================
    # دسته خام
    # =====================

    if data == "category_raw":

        await query.edit_message_text(
            "🥬 سبزی‌های خام\n\n"
            "محصول موردنظر را انتخاب کنید:",
            reply_markup=category_keyboard(
                "raw"
            ),
        )

        return


    # =====================
    # دسته ترشی
    # =====================

    if data == "category_pickles":

        await query.edit_message_text(
            "🥒 ترشیجات\n\n"
            "محصول موردنظر را انتخاب کنید:",
            reply_markup=category_keyboard(
                "pickles"
            ),
        )

        return


    # =====================
    # دسته شربت
    # =====================

    if data == "category_syrup":

        await query.edit_message_text(
            "🥭 شربت‌ها و مربا\n\n"
            "محصول موردنظر را انتخاب کنید:",
            reply_markup=category_keyboard(
                "syrup"
            ),
        )

        return


    # =====================
    # نمایش محصول
    # =====================

    if data.startswith("product_"):

        product_id = data.replace(
            "product_",
            "",
        )

        product = PRODUCTS.get(
            product_id
        )

        if not product:

            await query.edit_message_text(
                "❌ محصول پیدا نشد.",
                reply_markup=categories_keyboard(),
            )

            return

        await query.edit_message_text(
            f"🌿 {product['name']}\n\n"
            f"📦 وزن/حجم: {product['size']}\n"
            f"💰 قیمت: {product['price']:,} تومان\n\n"
            "برای اضافه کردن محصول به سبد، "
            "دکمه زیر را بزنید:",
            reply_markup=product_keyboard(
                product_id
            ),
        )

        return


    # =====================
    # افزودن محصول
    # =====================

    if data.startswith("add_"):

        product_id = data.replace(
            "add_",
            "",
        )

        if product_id not in PRODUCTS:

            await query.edit_message_text(
                "❌ محصول پیدا نشد.",
                reply_markup=categories_keyboard(),
            )

            return

        if user_id not in carts:

            carts[user_id] = []

        carts[user_id].append(
            product_id
        )

        await query.edit_message_text(
            "✅ محصول به سبد خرید اضافه شد.\n\n"
            "می‌توانید خرید را ادامه دهید "
            "یا سبد خرید را مشاهده کنید.",
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


    # =====================
    # سبد خرید
    # =====================

    if data == "cart":

        await show_cart(
            query,
            user_id,
        )

        return


    # =====================
    # شروع سفارش
    # =====================

    if data == "order":

        if not carts.get(user_id):

            await query.edit_message_text(
                "🧺 سبد خرید شما خالی است.",
                reply_markup=categories_keyboard(),
            )

            return

        context.user_data[
            "order_items"
        ] = list(
            carts[user_id]
        )

        context.user_data[
            "order_step"
        ] = "name"

        await query.message.reply_text(
            "📦 ثبت سفارش\n\n"
            "لطفاً نام و نام خانوادگی خود را وارد کنید:"
        )

        return


    # =====================
    # تحویل هیأت امنا
    # =====================

    if data == "delivery_heyat":

        context.user_data[
            "delivery"
        ] = "هیأت امنا"

        await show_order_summary(
            query,
            context,
        )

        return


    # =====================
    # تحویل مسجد
    # =====================

    if data == "delivery_mola":

        context.user_data[
            "delivery"
        ] = "مسجد مولای متقیان"

        await show_order_summary(
            query,
            context,
        )

        return


    # =====================
    # تأیید سفارش
    # =====================

    if data == "confirm_order":

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

            product = PRODUCTS[
                product_id
            ]

            total += product["price"]

            order_lines.append(
                f"• {product['name']} "
                f"({product['size']}) — "
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

        carts.pop(
            user_id,
            None,
        )

        context.user_data.clear()

        return


    # =====================
    # لغو
    # =====================

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

        product = PRODUCTS[
            product_id
        ]

        total += product["price"]

        order_lines.append(
            f"• {product['name']} "
            f"({product['size']}) — "
            f"{product['price']:,} تومان"
        )

    summary = (
        "📋 بررسی نهایی سفارش\n\n"
        f"👤 نام: {name}\n"
        f"📱 تلفن: {phone}\n"
        f"📍 محل تحویل: {delivery}\n"
        "🚚 هزینه تحویل: رایگان\n\n"
        "🛍 محصولات:\n"
        + "\n".join(order_lines)
        + f"\n\n💰 مبلغ کل: {total:,} تومان\n\n"
        "اگر اطلاعات صحیح است، "
        "«تأیید و ثبت سفارش» را بزنید."
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


    # =====================
    # نام
    # =====================

    if step == "name":

        context.user_data[
            "name"
        ] = text

        context.user_data[
            "order_step"
        ] = "phone"

        keyboard = [
            [
                KeyboardButton(
                    "📱 ارسال شماره تلفن",
                    request_contact=True,
                )
            ]
        ]

        await update.message.reply_text(
            "📱 لطفاً شماره تلفن خود را "
            "با زدن دکمه زیر ارسال کنید:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )

        return


    # =====================
    # شماره تلفن دستی
    # =====================

    if step == "phone":

        context.user_data[
            "phone"
        ] = text

        context.user_data[
            "order_step"
        ] = "delivery"

        await update.message.reply_text(
            "📍 محل تحویل سفارش را انتخاب کنید:",
            reply_markup=ReplyKeyboardRemove(),
        )

        await update.message.reply_text(
            "لطفاً یکی از دو محل تحویل را انتخاب کنید:",
            reply_markup=delivery_keyboard(),
        )

        return


    # =====================
    # پیام عادی
    # =====================

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
            "در حال حاضر در مرحله "
            "دریافت شماره تلفن نیستیم."
        )

        return

    phone = (
        update.message.contact.phone_number
    )

    context.user_data[
        "phone"
    ] = phone

    context.user_data[
        "order_step"
    ] = "delivery"

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
# لغو سفارش
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

    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    app.add_handler(
        CommandHandler(
            "cancel",
            cancel,
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
            contact_message,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
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
