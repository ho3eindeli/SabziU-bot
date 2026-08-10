```python
import os
import logging
import bale

from bale import (
    Bot,
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    MenuKeyboardMarkup,
    MenuKeyboardButton,
)


# =========================================================
# تنظیمات
# =========================================================

TOKEN = os.getenv("BALE_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("BALE_ADMIN_CHAT_ID")

if not TOKEN:
    raise RuntimeError("BALE_BOT_TOKEN تنظیم نشده است.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

bot = Bot(token=TOKEN)


# =========================================================
# شماره سفارش
# =========================================================

ORDER_NUMBER = 1000


# =========================================================
# محصولات
# =========================================================

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


# =========================================================
# حافظه مشتری‌ها
# =========================================================

customers = {}


# =========================================================
# سبد خرید
# =========================================================

carts = {}


# =========================================================
# وضعیت کاربران
# =========================================================

user_states = {}


# =========================================================
# منوی اصلی
# =========================================================

def main_menu():

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="🛒 فروشگاه سبزی‌یو",
            callback_data="shop",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🧺 سبد خرید",
            callback_data="cart",
        )
    )

    return keyboard


# =========================================================
# دسته‌بندی‌ها
# =========================================================

def categories_keyboard():

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="🌿 سبزی‌های سرخ‌شده",
            callback_data="category_fried",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🥬 سبزی‌های خام",
            callback_data="category_raw",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🥒 ترشیجات",
            callback_data="category_pickles",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🥭 شربت‌ها و مربا",
            callback_data="category_syrup",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🧺 سبد خرید",
            callback_data="cart",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🏠 منوی اصلی",
            callback_data="home",
        )
    )

    return keyboard


# =========================================================
# محصولات هر دسته
# =========================================================

def category_keyboard(category):

    keyboard = InlineKeyboardMarkup()

    for product_id, product in PRODUCTS.items():

        if product["category"] == category:

            keyboard.add(
                InlineKeyboardButton(
                    text=f"{product['name']} | {product['size']}",
                    callback_data=f"product_{product_id}",
                )
            )

    keyboard.add(
        InlineKeyboardButton(
            text="⬅️ بازگشت به دسته‌بندی‌ها",
            callback_data="shop",
        )
    )

    return keyboard


# =========================================================
# صفحه محصول
# =========================================================

def product_keyboard(product_id):

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="➕ افزودن به سبد خرید",
            callback_data=f"add_{product_id}",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🛒 ادامه خرید",
            callback_data="shop",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🧺 مشاهده سبد خرید",
            callback_data="cart",
        )
    )

    return keyboard


# =========================================================
# سبد خرید
# =========================================================

def cart_keyboard(user_id):

    keyboard = InlineKeyboardMarkup()

    cart = carts.get(user_id, {})

    for product_id, quantity in cart.items():

        product = PRODUCTS[product_id]

        keyboard.add(
            InlineKeyboardButton(
                text=f"➕ افزایش «{product['name']}»",
                callback_data=f"plus_{product_id}",
            )
        )

        keyboard.add(
            InlineKeyboardButton(
                text=f"➖ کاهش «{product['name']}»",
                callback_data=f"minus_{product_id}",
            )
        )

    if cart:

        keyboard.add(
            InlineKeyboardButton(
                text="📦 ثبت سفارش",
                callback_data="order",
            )
        )

    keyboard.add(
        InlineKeyboardButton(
            text="🛒 ادامه خرید",
            callback_data="shop",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🏠 منوی اصلی",
            callback_data="home",
        )
    )

    return keyboard


# =========================================================
# محل تحویل
# =========================================================

def delivery_keyboard():

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="🏢 هیأت امنا — رایگان",
            callback_data="delivery_heyat",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🕌 مسجد مولای متقیان — رایگان",
            callback_data="delivery_mola",
        )
    )

    return keyboard


# =========================================================
# تأیید سفارش
# =========================================================

def final_order_keyboard():

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="✅ تأیید و ثبت سفارش",
            callback_data="confirm_order",
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            text="❌ لغو سفارش",
            callback_data="cancel_order",
        )
    )

    return keyboard


# =========================================================
# شماره تلفن
# =========================================================

def phone_keyboard():

    keyboard = MenuKeyboardMarkup()

    keyboard.add(
        MenuKeyboardButton(
            "📱 ارسال شماره تلفن",
            request_contact=True,
        )
    )

    return keyboard


# =========================================================
# نمایش سبد خرید
# =========================================================

async def show_cart(message, user_id):

    cart = carts.get(user_id, {})

    if not cart:

        await message.reply(
            "🧺 سبد خرید شما خالی است.\n\n"
            "برای شروع خرید، یکی از دسته‌بندی‌ها را انتخاب کنید.",
            components=categories_keyboard(),
        )

        return

    total = 0

    lines = [
        "🧺 سبد خرید شما:",
        ""
    ]

    for product_id, quantity in cart.items():

        product = PRODUCTS[product_id]

        subtotal = product["price"] * quantity

        total += subtotal

        lines.append(
            f"• {product['name']}"
        )

        lines.append(
            f"  📦 {product['size']} × {quantity}"
        )

        lines.append(
            f"  💰 {subtotal:,} تومان"
        )

        lines.append("")

    lines.append(
        f"💰 جمع کل: {total:,} تومان"
    )

    await message.reply(
        "\n".join(lines),
        components=cart_keyboard(user_id),
    )


# =========================================================
# پیام‌های معمولی و /start
# =========================================================

@bot.event
async def on_message(message: Message):

    if not message.content and not message.contact:
        return

    user_id = str(message.author.user_id)

    text = ""

    if message.content:
        text = message.content.strip()

    # -----------------------------------------------------
    # شماره تلفن
    # -----------------------------------------------------

    if message.contact:

        if user_states.get(user_id) != "phone":
            return

        phone = message.contact.phone_number

        customers.setdefault(user_id, {})

        customers[user_id]["phone"] = phone

        user_states[user_id] = None

        await message.reply(
            "✅ شماره تلفن شما با موفقیت دریافت شد.\n\n"
            "حالا می‌توانید وارد فروشگاه شوید:",
            components=main_menu(),
        )

        return

    # -----------------------------------------------------
    # /start
    # -----------------------------------------------------

    if text == "/start":

        user_states[user_id] = None

        if user_id in customers:

            customer = customers[user_id]

            keyboard = InlineKeyboardMarkup()

            keyboard.add(
                InlineKeyboardButton(
                    text=f"👤 ادامه با نام «{customer.get('name', '')}»",
                    callback_data="use_saved_customer",
                )
            )

            keyboard.add(
                InlineKeyboardButton(
                    text="✏️ ثبت مشخصات جدید",
                    callback_data="new_customer",
                )
            )

            keyboard.add(
                InlineKeyboardButton(
                    text="🛒 ورود به فروشگاه",
                    callback_data="shop",
                )
            )

            await message.reply(
                "سلام 👋\n\n"
                "به فروشگاه سبزی‌یو خوش آمدید 🌿\n\n"
                f"👤 نام ثبت‌شده: {customer.get('name', '')}\n\n"
                "برای سفارش جدید یکی از گزینه‌های زیر را انتخاب کنید:",
                components=keyboard,
            )

        else:

            await message.reply(
                "سلام 👋\n\n"
                "به فروشگاه سبزی‌یو خوش آمدید 🌿\n\n"
                "از منوی زیر انتخاب کنید:",
                components=main_menu(),
            )

        return

    # -----------------------------------------------------
    # لغو
    # -----------------------------------------------------

    if text == "/cancel":

        user_states[user_id] = None

        await message.reply(
            "❌ عملیات لغو شد.",
            components=main_menu(),
        )

        return

    # -----------------------------------------------------
    # دریافت نام
    # -----------------------------------------------------

    if user_states.get(user_id) == "name":

        customers.setdefault(user_id, {})

        customers[user_id]["name"] = text

        user_states[user_id] = "phone"

        await message.reply(
            "📱 لطفاً شماره تلفن خود را با دکمه زیر ارسال کنید:",
            components=phone_keyboard(),
        )

        return

    # -----------------------------------------------------
    # سلام
    # -----------------------------------------------------

    if text in ["سلام", "سلام 👋"]:

        await message.reply(
            "سلام 👋\n\n"
            "به فروشگاه سبزی‌یو خوش آمدید 🌿",
            components=main_menu(),
        )

        return


# =========================================================
# Callback ها
# =========================================================

@bot.event
async def on_callback(callback: CallbackQuery):

    user_id = str(callback.from_user.user_id)

    data = callback.data

    # -----------------------------------------------------
    # مشتری ذخیره‌شده
    # -----------------------------------------------------

    if data == "use_saved_customer":

        customer = customers.get(user_id)

        if not customer:

            await callback.message.reply(
                "❌ اطلاعات قبلی پیدا نشد.",
                components=main_menu(),
            )

            return

        await callback.message.reply(
            f"👤 {customer.get('name', '')}\n"
            f"📱 {customer.get('phone', 'ثبت نشده')}\n\n"
            "اطلاعات شما آماده است.\n\n"
            "حالا محصول موردنظر را انتخاب کنید:",
            components=categories_keyboard(),
        )

        return

    # -----------------------------------------------------
    # ثبت مشخصات جدید
    # -----------------------------------------------------

    if data == "new_customer":

        user_states[user_id] = "name"

        await callback.message.reply(
            "👤 لطفاً نام و نام خانوادگی خود را وارد کنید:"
        )

        return

    # -----------------------------------------------------
    # خانه
    # -----------------------------------------------------

    if data == "home":

        await callback.message.reply(
            "🌿 سبزی‌یو\n\n"
            "به فروشگاه سبزی‌یو خوش آمدید.",
            components=main_menu(),
        )

        return

    # -----------------------------------------------------
    # فروشگاه
    # -----------------------------------------------------

    if data == "shop":

        await callback.message.reply(
            "🛒 فروشگاه سبزی‌یو\n\n"
            "دسته‌بندی موردنظر را انتخاب کنید:",
            components=categories_keyboard(),
        )

        return

    # -----------------------------------------------------
    # دسته‌بندی
    # -----------------------------------------------------

    if data.startswith("category_"):

        category = data.replace(
            "category_",
            "",
            1,
        )

        names = {
            "fried": "🌿 سبزی‌های سرخ‌شده",
            "raw": "🥬 سبزی‌های خام",
            "pickles": "🥒 ترشیجات",
            "syrup": "🥭 شربت‌ها و مربا",
        }

        await callback.message.reply(
            f"{names.get(category, '🛒 فروشگاه')}\n\n"
            "محصول موردنظر را انتخاب کنید:",
            components=category_keyboard(category),
        )

        return

    # -----------------------------------------------------
    # محصول
    # -----------------------------------------------------

    if data.startswith("product_"):

        product_id = data.replace(
            "product_",
            "",
            1,
        )

        product = PRODUCTS.get(product_id)

        if not product:

            await callback.message.reply(
                "❌ محصول پیدا نشد.",
                components=categories_keyboard(),
            )

            return

        await callback.message.reply(
            f"🌿 {product['name']}\n\n"
            f"📦 وزن/حجم: {product['size']}\n"
            f"💰 قیمت: {product['price']:,} تومان\n\n"
            "برای افزودن محصول به سبد خرید، دکمه زیر را بزنید:",
            components=product_keyboard(product_id),
        )

        return

    # -----------------------------------------------------
    # افزودن به سبد
    # -----------------------------------------------------

    if data.startswith("add_"):

        product_id = data.replace(
            "add_",
            "",
            1,
        )

        if product_id not in PRODUCTS:

            await callback.message.reply(
                "❌ محصول پیدا نشد.",
                components=categories_keyboard(),
            )

            return

        carts.setdefault(
            user_id,
            {},
        )

        carts[user_id][product_id] = (
            carts[user_id].get(product_id, 0) + 1
        )

        product = PRODUCTS[product_id]

        quantity = carts[user_id][product_id]

        await callback.message.reply(
            f"✅ «{product['name']}» به سبد خرید اضافه شد.\n\n"
            f"📦 تعداد: {quantity}\n"
            f"💰 قیمت واحد: {product['price']:,} تومان",
            components=cart_keyboard(user_id),
        )

        return

    # -----------------------------------------------------
    # افزایش تعداد
    # -----------------------------------------------------

    if data.startswith("plus_"):

        product_id = data.replace(
            "plus_",
            "",
            1,
        )

        if product_id not in PRODUCTS:
            return

        carts.setdefault(
            user_id,
            {},
        )

        carts[user_id][product_id] = (
            carts[user_id].get(product_id, 0) + 1
        )

        await show_cart(
            callback.message,
            user_id,
        )

        return

    # -----------------------------------------------------
    # کاهش تعداد
    # -----------------------------------------------------

    if data.startswith("minus_"):

        product_id = data.replace(
            "minus_",
            "",
            1,
        )

        if product_id in carts.get(user_id, {}):

            carts[user_id][product_id] -= 1

            if carts[user_id][product_id] <= 0:

                del carts[user_id][product_id]

        await show_cart(
            callback.message,
            user_id,
        )

        return

    # -----------------------------------------------------
    # سبد خرید
    # -----------------------------------------------------

    if data == "cart":

        await show_cart(
            callback.message,
            user_id,
        )

        return

    # -----------------------------------------------------
    # ثبت سفارش
    # -----------------------------------------------------

    if data == "order":

        if not carts.get(user_id):

            await callback.message.reply(
                "🧺 سبد خرید شما خالی است.",
                components=categories_keyboard(),
            )

            return

        if (
            user_id in customers
            and customers[user_id].get("name")
            and customers[user_id].get("phone")
        ):

            user_states[user_id] = "delivery"

            await callback.message.reply(
                f"👤 مشتری: {customers[user_id]['name']}\n\n"
                "📍 محل تحویل سفارش را انتخاب کنید:",
                components=delivery_keyboard(),
            )

        else:

            user_states[user_id] = "name"

            await callback.message.reply(
                "📦 ثبت سفارش\n\n"
                "👤 لطفاً نام و نام خانوادگی خود را وارد کنید:"
            )

        return

    # -----------------------------------------------------
    # محل تحویل - هیأت
    # -----------------------------------------------------

    if data == "delivery_heyat":

        customers.setdefault(
            user_id,
            {},
        )

        customers[user_id]["delivery"] = "هیأت امنا"

        await show_order_summary(
            callback.message,
            user_id,
        )

        return

    # -----------------------------------------------------
    # محل تحویل - مسجد
    # -----------------------------------------------------

    if data == "delivery_mola":

        customers.setdefault(
            user_id,
            {},
        )

        customers[user_id]["delivery"] = "مسجد مولای متقیان"

        await show_order_summary(
            callback.message,
            user_id,
        )

        return

    # -----------------------------------------------------
    # تأیید سفارش
    # -----------------------------------------------------

    if data == "confirm_order":

        await confirm_order(
            callback.message,
            user_id,
        )

        return

    # -----------------------------------------------------
    # لغو سفارش
    # -----------------------------------------------------

    if data == "cancel_order":

        carts.pop(
            user_id,
            None,
        )

        user_states[user_id] = None

        await callback.message.reply(
            "❌ سفارش لغو شد.",
            components=main_menu(),
        )

        return


# =========================================================
# خلاصه سفارش
# =========================================================

async def show_order_summary(message, user_id):

    customer = customers.get(
        user_id,
        {},
    )

    cart = carts.get(
        user_id,
        {},
    )

    if not cart:

        await message.reply(
            "🧺 سبد خرید شما خالی است.",
            components=main_menu(),
        )

        return

    total = 0

    lines = []

    for product_id, quantity in cart.items():

        product = PRODUCTS[product_id]

        subtotal = product["price"] * quantity

        total += subtotal

        lines.append(
            f"• {product['name']}\n"
            f"  📦 {product['size']} × {quantity}\n"
            f"  💰 {subtotal:,} تومان"
        )

    text = (
        "📋 بررسی نهایی سفارش\n\n"
        f"👤 نام: {customer.get('name', '')}\n"
        f"📱 تلفن: {customer.get('phone', '')}\n"
        f"📍 محل تحویل: {customer.get('delivery', '')}\n"
        "🚚 هزینه تحویل: رایگان\n\n"
        "🛍 محصولات:\n\n"
        + "\n\n".join(lines)
        + f"\n\n💰 مبلغ کل: {total:,} تومان\n\n"
        "اگر اطلاعات صحیح است، "
        "«تأیید و ثبت سفارش» را بزنید."
    )

    await message.reply(
        text,
        components=final_order_keyboard(),
    )


# =========================================================
# ثبت نهایی سفارش
# =========================================================

async def confirm_order(message, user_id):

    global ORDER_NUMBER

    customer = customers.get(
        user_id,
        {},
    )

    cart = carts.get(
        user_id,
        {},
    )

    if not cart:

        await message.reply(
            "🧺 سبد خرید شما خالی است.",
            components=main_menu(),
        )

        return

    total = 0

    lines = []

    for product_id, quantity in cart.items():

        product = PRODUCTS[product_id]

        subtotal = product["price"] * quantity

        total += subtotal

        lines.append(
            f"• {product['name']} "
            f"({product['size']}) × {quantity} "
            f"— {subtotal:,} تومان"
        )

    order_number = ORDER_NUMBER

    ORDER_NUMBER += 1

    # -----------------------------------------------------
    # پیام مشتری
    # -----------------------------------------------------

    customer_text = (
        "🎉 سفارش شما با موفقیت ثبت شد!\n\n"
        f"🔢 شماره سفارش: #{order_number}\n"
        f"👤 نام: {customer.get('name', '')}\n"
        f"📱 تلفن: {customer.get('phone', '')}\n"
        f"📍 محل تحویل: {customer.get('delivery', '')}\n"
        "🚚 هزینه تحویل: رایگان\n\n"
        f"💰 مبلغ کل: {total:,} تومان\n\n"
        "از خرید شما از سبزی‌یو سپاسگزاریم 🌿"
    )

    await message.reply(
        customer_text,
        components=main_menu(),
    )

    # -----------------------------------------------------
    # پیام مدیر
    # -----------------------------------------------------

    if ADMIN_CHAT_ID:

        admin_text = (
            "🆕 سفارش جدید سبزی‌یو\n\n"
            f"🔢 شماره سفارش: #{order_number}\n\n"
            f"👤 مشتری: {customer.get('name', '')}\n"
            f"📱 تلفن: {customer.get('phone', '')}\n"
            f"📍 محل تحویل: {customer.get('delivery', '')}\n\n"
            "🛍 محصولات:\n"
            + "\n".join(lines)
            + f"\n\n💰 مبلغ کل: {total:,} تومان\n"
            "🚚 هزینه تحویل: رایگان\n\n"
            f"🆔 شناسه بله مشتری: {user_id}"
        )

        try:

            await bot.send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text=admin_text,
            )

        except Exception as e:

            logging.error(
                f"خطا در ارسال سفارش به مدیر: {e}"
            )

    # -----------------------------------------------------
    # پاک کردن سبد
    # -----------------------------------------------------

    carts.pop(
        user_id,
        None,
    )

    user_states[user_id] = None


# =========================================================
# آماده شدن ربات
# =========================================================

@bot.event
async def on_ready():

    print("=== BALE BOT CONNECTED ===")
    print("SabziU Bale Store is ready!")


# =========================================================
# اجرای ربات
# =========================================================

bot.run()
```
