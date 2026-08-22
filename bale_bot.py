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
ADMIN_CHAT_IDS = [x.strip() for x in os.getenv("BALE_ADMIN_CHAT_IDS", "").split(",") if x.strip()]

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

from products import PRODUCTS

# =========================================================
# حافظه
# =========================================================

customers = {}
carts = {}
user_states = {}

# =========================================================
# منوی اصلی
# دکمه‌ها عمودی هستند
# =========================================================

def main_menu():
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="🛒 فروشگاه سبزی‌یو",
            callback_data="shop",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🧺 سبد خرید",
            callback_data="cart",
        ),
        row=2,
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
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🥬 سبزی‌های خام",
            callback_data="category_raw",
        ),
        row=2,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🥒 ترشیجات",
            callback_data="category_pickles",
        ),
        row=3,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🥭 شربت‌ها و مربا",
            callback_data="category_syrup",
        ),
        row=4,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🧺 سبد خرید",
            callback_data="cart",
        ),
        row=5,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🏠 منوی اصلی",
            callback_data="home",
        ),
        row=6,
    )

    return keyboard


# =========================================================
# محصولات هر دسته
# هر محصول در یک ردیف جدا
# =========================================================

def category_keyboard(category):
    keyboard = InlineKeyboardMarkup()

    row = 1

    for product_id, product in PRODUCTS.items():

        if product["category"] == category:

            keyboard.add(
                InlineKeyboardButton(
                    text=f"{product['name']} | {product['size']}",
                    callback_data=f"product_{product_id}",
                ),
                row=row,
            )

            row += 1

    keyboard.add(
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="shop",
        ),
        row=row,
    )

    return keyboard


# =========================================================
# صفحه محصول
# =========================================================

def product_keyboard(product_id):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="➕ اضافه کردن سفارش",
            callback_data=f"add_{product_id}",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🛒 ادامه خرید",
            callback_data="shop",
        ),
        row=2,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🧺 سبد خرید",
            callback_data="cart",
        ),
        row=3,
    )

    return keyboard


# =========================================================
# سبد خرید
# =========================================================

def cart_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()

    cart = carts.get(user_id, {})

    row = 1

    for product_id, quantity in cart.items():

        product = PRODUCTS[product_id]

        keyboard.add(
            InlineKeyboardButton(
                text=f"➕ اضافه کردن {product['name']}",
                callback_data=f"plus_{product_id}",
            ),
            row=row,
        )

        row += 1

        keyboard.add(
            InlineKeyboardButton(
                text=f"➖ کم کردن {product['name']}",
                callback_data=f"minus_{product_id}",
            ),
            row=row,
        )

        row += 1

    if cart:

        keyboard.add(
            InlineKeyboardButton(
                text="📦 ثبت سفارش",
                callback_data="order",
            ),
            row=row,
        )

        row += 1

    keyboard.add(
        InlineKeyboardButton(
            text="🛒 ادامه خرید",
            callback_data="shop",
        ),
        row=row,
    )

    row += 1

    keyboard.add(
        InlineKeyboardButton(
            text="🏠 منوی اصلی",
            callback_data="home",
        ),
        row=row,
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
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🕌 مسجد مولای متقیان — رایگان",
            callback_data="delivery_mola",
        ),
        row=2,
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
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="❌ لغو سفارش",
            callback_data="cancel_order",
        ),
        row=2,
    )

    return keyboard


# =========================================================
# دکمه ارسال شماره
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
# نمایش سبد
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

    lines = ["🧺 سبد خرید شما:\n"]

    for product_id, quantity in cart.items():

        product = PRODUCTS[product_id]

        subtotal = product["price"] * quantity

        total += subtotal

        lines.append(
            f"• {product['name']}\n"
            f"  {product['size']} × {quantity}\n"
            f"  {subtotal:,} تومان\n"
        )

    lines.append(
        f"\n💰 جمع کل: {total:,} تومان"
    )

    await message.reply(
        "\n".join(lines),
        components=cart_keyboard(user_id),
    )


# =========================================================
# خلاصه سفارش
# =========================================================

async def show_order_summary(message, user_id):

    customer = customers.get(user_id, {})
    cart = carts.get(user_id, {})

    total = 0
    lines = []

    for product_id, quantity in cart.items():

        product = PRODUCTS[product_id]

        subtotal = product["price"] * quantity

        total += subtotal

        lines.append(
            f"• {product['name']}\n"
            f"  {product['size']} × {quantity}\n"
            f"  {subtotal:,} تومان"
        )

    text = (
        "📋 بررسی نهایی سفارش\n\n"
        f"👤 نام: {customer.get('name', '')}\n"
        f"📱 تلفن: {customer.get('phone', '')}\n"
        f"📍 محل تحویل: {customer.get('delivery', '')}\n"
        "🚚 هزینه تحویل: رایگان\n\n"
        "🛍 محصولات:\n"
        + "\n".join(lines)
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

    customer = customers.get(user_id, {})
    cart = carts.get(user_id, {})

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

    if ADMIN_CHAT_IDS:

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

            for admin_chat_id in ADMIN_CHAT_IDS:
                await bot.send_message(
                    chat_id=int(admin_chat_id),
                    text=admin_text,
                )

        except Exception as e:

            logging.error(
                f"خطا در ارسال سفارش به مدیر: {e}"
            )

    carts.pop(user_id, None)

    user_states[user_id] = None


# =========================================================
# دریافت پیام‌ها
# =========================================================

@bot.event
async def on_message(message: Message):

    user_id = str(message.author.user_id)
    print(f"USER_ID: {user_id}", flush=True)

    # -----------------------------------------------------
    # دریافت شماره تلفن
    # این قسمت عمداً قبل از بررسی متن قرار گرفته
    # -----------------------------------------------------

    if message.contact:

        phone = message.contact.phone_number

        customers.setdefault(user_id, {})

        customers[user_id]["phone"] = phone

        # اگر نام قبلاً ثبت شده باشد
        if not customers[user_id].get("name"):

            user_states[user_id] = "name"

            await message.reply(
                "📱 شماره تلفن شما ثبت شد.\n\n"
                "👤 لطفاً نام و نام خانوادگی خود را وارد کنید:"
            )

        else:

            user_states[user_id] = None

            await message.reply(
                "✅ شماره تلفن شما با موفقیت ثبت شد.\n\n"
                "حالا می‌توانید خرید خود را ادامه دهید:",
                components=main_menu(),
            )

        return

    # -----------------------------------------------------
    # اگر متن وجود ندارد
    # -----------------------------------------------------

    if not message.content:
        return

    text = message.content.strip()

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
                ),
                row=1,
            )

            keyboard.add(
                InlineKeyboardButton(
                    text="✏️ ثبت مشخصات جدید",
                    callback_data="new_customer",
                ),
                row=2,
            )

            keyboard.add(
                InlineKeyboardButton(
                    text="🛒 ورود به فروشگاه",
                    callback_data="shop",
                ),
                row=3,
            )

            await message.reply(
                "سلام 👋\n\n"
                "خوش آمدید به سبزی‌یو 🌿\n\n"
                f"نام ثبت‌شده شما:\n"
                f"👤 {customer.get('name', '')}\n\n"
                "برای سفارش جدید می‌توانید از اطلاعات قبلی استفاده کنید.",
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

    state = user_states.get(user_id)

    if state == "name":

        customers.setdefault(user_id, {})

        customers[user_id]["name"] = text

        user_states[user_id] = "phone"

        await message.reply(
            "👤 نام شما ثبت شد.\n\n"
            "📱 لطفاً شماره تلفن خود را با دکمه زیر ارسال کنید:",
            components=phone_keyboard(),
        )

        return

    # -----------------------------------------------------
    # دریافت شماره تلفن به صورت متن
    # -----------------------------------------------------

    if state == "phone":

        customers.setdefault(user_id, {})
        customers[user_id]["phone"] = text
        user_states[user_id] = None

        await message.reply(
            "✅ شماره تلفن شما ثبت شد.\n\n"
            "حالا می‌توانید خرید خود را ادامه دهید:",
            components=main_menu(),
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
                "اطلاعات قبلی پیدا نشد.",
                components=main_menu(),
            )

            return

        await callback.message.reply(
            f"👤 {customer.get('name', '')}\n"
            f"📱 {customer.get('phone', 'ثبت نشده')}\n\n"
            "اطلاعات شما آماده است.\n"
            "حالا محصول موردنظر را انتخاب کنید:",
            components=categories_keyboard(),
        )

        return

    # -----------------------------------------------------
    # مشتری جدید
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
        )

        names = {
            "fried": "🌿 سبزی‌های سرخ‌شده",
            "raw": "🥬 سبزی‌های خام",
            "pickles": "🥒 ترشیجات",
            "syrup": "🥭 شربت‌ها و مربا",
        }

        await callback.message.reply(
            f"{names.get(category, 'فروشگاه')}\n\n"
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
            f"📦 {product['size']}\n"
            f"💰 {product['price']:,} تومان\n\n"
            "برای افزودن محصول به سبد، دکمه زیر را بزنید:",
            components=product_keyboard(product_id),
        )

        return

    # -----------------------------------------------------
    # اضافه کردن سفارش
    # -----------------------------------------------------

    if data.startswith("add_"):

        product_id = data.replace(
            "add_",
            "",
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

        await callback.message.reply(
            f"✅ «{product['name']}» به سبد خرید اضافه شد.\n\n"
            f"تعداد فعلی: {carts[user_id][product_id]}",
            components=cart_keyboard(user_id),
        )

        return

    # -----------------------------------------------------
    # اضافه کردن تعداد
    # -----------------------------------------------------

    if data.startswith("plus_"):

        product_id = data.replace(
            "plus_",
            "",
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
    # کم کردن تعداد
    # -----------------------------------------------------

    if data.startswith("minus_"):

        product_id = data.replace(
            "minus_",
            "",
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
    # سبد
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

        customer = customers.get(
            user_id,
            {},
        )

        # اگر نام و تلفن هر دو ثبت شده‌اند
        if (
            customer.get("name")
            and customer.get("phone")
        ):

            user_states[user_id] = "delivery"

            await callback.message.reply(
                f"👤 مشتری: {customer['name']}\n\n"
                "📍 محل تحویل سفارش را انتخاب کنید:",
                components=delivery_keyboard(),
            )

        # اگر مشخصات ناقص است
        else:

            user_states[user_id] = "name"

            await callback.message.reply(
                "📦 ثبت سفارش\n\n"
                "👤 لطفاً نام و نام خانوادگی خود را وارد کنید:"
            )

        return

    # -----------------------------------------------------
    # تحویل هیأت
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
    # تحویل مسجد
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
    # تأیید
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
