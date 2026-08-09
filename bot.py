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
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# شمارنده سفارش
ORDER_NUMBER = 1000


# =========================
# محصولات
# =========================

PRODUCTS = {
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
# سبدهای خرید
# =========================

carts = {}


# =========================
# منوی اصلی
# =========================

def main_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🛒 فروشگاه سبزی‌یو",
                callback_data="shop"
            )
        ],
        [
            InlineKeyboardButton(
                "🧺 سبد خرید",
                callback_data="cart"
            )
        ],
    ])


# =========================
# دسته‌بندی‌ها
# =========================

def categories_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🌿 سبزی‌های سرخ‌شده",
                callback_data="category_fried"
            )
        ],
        [
            InlineKeyboardButton(
                "🥬 سبزی‌های خام",
                callback_data="category_raw"
            )
        ],
        [
            InlineKeyboardButton(
                "🥒 ترشیجات",
                callback_data="category_pickles"
            )
        ],
        [
            InlineKeyboardButton(
                "🥭 شربت‌ها و مربا",
                callback_data="category_syrup"
            )
        ],
        [
            InlineKeyboardButton(
                "🧺 سبد خرید",
                callback_data="cart"
            )
        ],
    ])


# =========================
# محصولات دسته
# =========================

def category_keyboard(category):

    keyboard = []

    for product_id, product in PRODUCTS.items():

        if product["category"] == category:

            keyboard.append([
                InlineKeyboardButton(
                    f"{product['name']} | {product['size']}",
                    callback_data=f"product_{product_id}"
                )
            ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ بازگشت به فروشگاه",
            callback_data="shop"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            "🧺 سبد خرید",
            callback_data="cart"
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# =========================
# صفحه محصول
# =========================

def product_keyboard(product_id):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ افزودن به سبد",
                callback_data=f"add_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🛒 ادامه خرید",
                callback_data="shop"
            )
        ],
        [
            InlineKeyboardButton(
                "🧺 سبد خرید",
                callback_data="cart"
            )
        ],
    ])


# =========================
# سبد خرید
# =========================

def cart_keyboard():

    return InlineKeyboardMarkup([
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
        ],
    ])


# =========================
# محل تحویل
# =========================

def delivery_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🏢 هیأت امنا — رایگان",
                callback_data="delivery_heyat"
            )
        ],
        [
            InlineKeyboardButton(
                "🕌 مسجد مولای متقیان — رایگان",
                callback_data="delivery_mola"
            )
        ],
    ])


# =========================
# تأیید سفارش
# =========================

def final_order_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ تأیید و ثبت سفارش",
                callback_data="confirm_order"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ لغو سفارش",
                callback_data="cancel_order"
            )
        ],
    ])


# =========================
# /start
# =========================

async def start(update, context):

    context.user_data.clear()

    await update.message.reply_text(
        "سلام 👋\n\n"
        "به فروشگاه سبزی‌یو خوش آمدید 🌿\n\n"
        "از منوی زیر انتخاب کنید:",
        reply_markup=main_menu()
    )


# =========================
# نمایش سبد
# =========================

async def show_cart(query, user_id):

    items = carts.get(user_id, [])

    if not items:

        await query.edit_message_text(
            "🧺 سبد خرید شما خالی است.",
            reply_markup=categories_keyboard()
        )

        return

    total = 0

    lines = ["🧺 سبد خرید شما:\n"]

    for index, product_id in enumerate(items, 1):

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
        reply_markup=cart_keyboard()
    )


# =========================
# دکمه‌ها
# =========================

async def buttons(update, context):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    data = query.data


    if data == "shop":

        await query.edit_message_text(
            "🛒 فروشگاه سبزی‌یو\n\n"
            "دسته‌بندی موردنظر را انتخاب کنید:",
            reply_markup=categories_keyboard()
        )

        return


    if data.startswith("category_"):

        category = data.replace(
            "category_",
            ""
        )

        names = {
            "fried": "🌿 سبزی‌های سرخ‌شده",
            "raw": "🥬 سبزی‌های خام",
            "pickles": "🥒 ترشیجات",
            "syrup": "🥭 شربت‌ها و مربا",
        }

        await query.edit_message_text(
            f"{names.get(category, 'فروشگاه')}\n\n"
            "محصول موردنظر را انتخاب کنید:",
            reply_markup=category_keyboard(category)
        )

        return


    if data.startswith("product_"):

        product_id = data.replace(
            "product_",
            ""
        )

        product = PRODUCTS.get(product_id)

        if not product:

            await query.edit_message_text(
                "❌ محصول پیدا نشد.",
                reply_markup=categories_keyboard()
            )

            return

        await query.edit_message_text(
            f"🌿 {product['name']}\n\n"
            f"📦 {product['size']}\n"
            f"💰 {product['price']:,} تومان\n\n"
            "برای اضافه کردن محصول به سبد، "
            "دکمه زیر را بزنید:",
            reply_markup=product_keyboard(product_id)
        )

        return


    if data.startswith("add_"):

        product_id = data.replace(
            "add_",
            ""
        )

        if product_id not in PRODUCTS:

            await query.edit_message_text(
                "❌ محصول پیدا نشد.",
                reply_markup=categories_keyboard()
            )

            return

        carts.setdefault(
            user_id,
            []
        )

        carts[user_id].append(
            product_id
        )

        await query.edit_message_text(
            "✅ محصول به سبد خرید اضافه شد.\n\n"
            "می‌توانید خرید را ادامه دهید یا "
            "سبد خرید را مشاهده کنید.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🧺 سبد خرید",
                        callback_data="cart"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🛒 ادامه خرید",
                        callback_data="shop"
                    )
                ],
            ])
        )

        return


    if data == "cart":

        await show_cart(
            query,
            user_id
        )

        return


    if data == "order":

        if not carts.get(user_id):

            await query.edit_message_text(
                "🧺 سبد خرید شما خالی است.",
                reply_markup=categories_keyboard()
            )

            return

        context.user_data[
            "order_items"
        ] = list(carts[user_id])

        context.user_data[
            "order_step"
        ] = "name"

        await query.message.reply_text(
            "📦 ثبت سفارش\n\n"
            "لطفاً نام و نام خانوادگی خود را وارد کنید:"
        )

        return


    if data == "delivery_heyat":

        context.user_data[
            "delivery"
        ] = "هیأت امنا"

        await show_order_summary(
            query,
            context
        )

        return


    if data == "delivery_mola":

        context.user_data[
            "delivery"
        ] = "مسجد مولای متقیان"

        await show_order_summary(
            query,
            context
        )

        return


    if data == "confirm_order":

        await confirm_order(
            query,
            context
        )

        return


    if data == "cancel_order":

        context.user_data.clear()

        await query.edit_message_text(
            "❌ سفارش لغو شد.",
            reply_markup=main_menu()
        )

        return


# =========================
# خلاصه سفارش
# =========================

async def show_order_summary(query, context):

    name = context.user_data.get(
        "name",
        ""
    )

    phone = context.user_data.get(
        "phone",
        ""
    )

    delivery = context.user_data.get(
        "delivery",
        ""
    )

    items = context.user_data.get(
        "order_items",
        []
    )

    total = 0

    lines = []

    for product_id in items:

        product = PRODUCTS[product_id]

        total += product["price"]

        lines.append(
            f"• {product['name']} "
            f"({product['size']}) — "
            f"{product['price']:,} تومان"
        )

    text = (
        "📋 بررسی نهایی سفارش\n\n"
        f"👤 نام: {name}\n"
        f"📱 تلفن: {phone}\n"
        f"📍 محل تحویل: {delivery}\n"
        "🚚 هزینه تحویل: رایگان\n\n"
        "🛍 محصولات:\n"
        + "\n".join(lines)
        + f"\n\n💰 مبلغ کل: {total:,} تومان\n\n"
        "اگر اطلاعات صحیح است، "
        "«تأیید و ثبت سفارش» را بزنید."
    )

    await query.edit_message_text(
        text,
        reply_markup=final_order_keyboard()
    )


# =========================
# ثبت نهایی سفارش
# =========================

async def confirm_order(query, context):

    global ORDER_NUMBER

    user_id = query.from_user.id

    name = context.user_data.get(
        "name",
        ""
    )

    phone = context.user_data.get(
        "phone",
        ""
    )

    delivery = context.user_data.get(
        "delivery",
        ""
    )

    items = context.user_data.get(
        "order_items",
        []
    )

    total = 0

    lines = []

    for product_id in items:

        product = PRODUCTS[product_id]

        total += product["price"]

        lines.append(
            f"• {product['name']} "
            f"({product['size']})"
        )

    order_number = ORDER_NUMBER

    ORDER_NUMBER += 1


    # =====================
    # پیام مشتری
    # =====================

    customer_text = (
        "🎉 سفارش شما با موفقیت ثبت شد!\n\n"
        f"🔢 شماره سفارش: #{order_number}\n"
        f"👤 نام: {name}\n"
        f"📱 تلفن: {phone}\n"
        f"📍 محل تحویل: {delivery}\n"
        "🚚 هزینه تحویل: رایگان\n\n"
        f"💰 مبلغ کل: {total:,} تومان\n\n"
        "از خرید شما از سبزی‌یو سپاسگزاریم 🌿"
    )

    await query.edit_message_text(
        customer_text,
        reply_markup=main_menu()
    )


    # =====================
    # پیام مدیر
    # =====================

    admin_text = (
        "🆕 سفارش جدید سبزی‌یو\n\n"
        f"🔢 شماره سفارش: #{order_number}\n\n"
        f"👤 مشتری: {name}\n"
        f"📱 تلفن: {phone}\n"
        f"📍 محل تحویل: {delivery}\n\n"
        "🛍 محصولات:\n"
        + "\n".join(lines)
        + f"\n\n💰 مبلغ کل: {total:,} تومان\n"
        "🚚 هزینه تحویل: رایگان\n\n"
        f"🆔 شناسه تلگرام مشتری: {user_id}"
    )


    if ADMIN_CHAT_ID:

        try:

            await context.bot.send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text=admin_text
            )

        except Exception as e:

            logging.error(
                f"خطا در ارسال سفارش به مدیر: {e}"
            )


    # =====================
    # پاک کردن سبد
    # =====================

    carts.pop(
        user_id,
        None
    )

    context.user_data.clear()


# =========================
# پیام متنی
# =========================

async def text_message(update, context):

    text = update.message.text.strip()

    step = context.user_data.get(
        "order_step"
    )


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
                    request_contact=True
                )
            ]
        ]

        await update.message.reply_text(
            "📱 لطفاً شماره تلفن خود را "
            "با زدن دکمه زیر ارسال کنید:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

        return


    if step == "phone":

        context.user_data[
            "phone"
        ] = text

        context.user_data[
            "order_step"
        ] = "delivery"

        await update.message.reply_text(
            "📍 محل تحویل سفارش را انتخاب کنید:",
            reply_markup=ReplyKeyboardRemove()
        )

        await update.message.reply_text(
            "لطفاً یکی از دو محل تحویل را انتخاب کنید:",
            reply_markup=delivery_keyboard()
        )

        return


    await update.message.reply_text(
        "برای شروع خرید، /start را بزنید.",
        reply_markup=main_menu()
    )


# =========================
# دریافت شماره تلفن
# =========================

async def contact_message(update, context):

    step = context.user_data.get(
        "order_step"
    )

    if step != "phone":

        await update.message.reply_text(
            "در حال حاضر در مرحله دریافت "
            "شماره تلفن نیستیم."
        )

        return

    phone = update.message.contact.phone_number

    context.user_data[
        "phone"
    ] = phone

    context.user_data[
        "order_step"
    ] = "delivery"

    await update.message.reply_text(
        "✅ شماره تلفن دریافت شد.\n\n"
        "📍 محل تحویل سفارش را انتخاب کنید:",
        reply_markup=ReplyKeyboardRemove()
    )

    await update.message.reply_text(
        "لطفاً یکی از دو محل تحویل را انتخاب کنید:",
        reply_markup=delivery_keyboard()
    )


# =========================
# /cancel
# =========================

async def cancel(update, context):

    context.user_data.clear()

    await update.message.reply_text(
        "❌ ثبت سفارش لغو شد.",
        reply_markup=main_menu()
    )


# =========================
# /myid
# =========================

async def myid(update, context):

    await update.message.reply_text(
        f"🆔 Chat ID شما:\n\n"
        f"{update.effective_chat.id}"
    )


# =========================
# اجرای ربات
# =========================

def main():

    if not TOKEN:

        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN تنظیم نشده است."
        )

    if not ADMIN_CHAT_ID:

        logging.warning(
            "ADMIN_CHAT_ID تنظیم نشده است."
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
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "cancel",
            cancel
        )
    )

    app.add_handler(
        CommandHandler(
            "myid",
            myid
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
            contact_message
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message
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
