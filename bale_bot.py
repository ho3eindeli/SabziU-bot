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

ADMIN_CHAT_IDS = [
    x.strip()
    for x in os.getenv("BALE_ADMIN_CHAT_IDS", "").split(",")
    if x.strip()
]

if not TOKEN:
    raise RuntimeError("BALE_BOT_TOKEN تنظیم نشده است.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

bot = Bot(token=TOKEN)

# =========================================================
# محصولات
# =========================================================

from products import PRODUCTS

# =========================================================
# حافظه
# =========================================================

ORDER_NUMBER = 1000

customers = {}
carts = {}
user_states = {}

# مشتری فعلی که کاربر برای خرید انتخاب کرده
active_customer = {}

# اطلاعات محل تحویل فقط برای سفارش جاری
order_delivery = {}


# =========================================================
# نام دسته‌بندی‌ها
# =========================================================

CATEGORY_NAMES = {
    "herbs": "🌿 سبزی‌های سرخ‌شده",
    "fried": "🌿 سبزی‌های سرخ‌شده",
    "raw": "🥬 سبزی‌های خام",
    "pickle": "🥒 ترشیجات",
    "pickles": "🥒 ترشیجات",
    "sauce": "🥫 سس‌ها",
    "syrup": "🥭 شربت‌ها",
    "distillate": "🌱 عرقیات",
    "spice": "🧂 ادویه‌ها",
    "spices": "🧂 ادویه‌ها",
    "jam": "🍓 مرباها",
    "semi_ready": "🍽️ محصولات نیمه‌آماده",
    "fresh": "🥬 محصولات تازه و آماده پخت",
    "drinks": "🥤 نوشیدنی‌ها",
}


# =========================================================
# منوی اصلی
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

    keyboard.add(
        InlineKeyboardButton(
            text="👥 مشتریان",
            callback_data="customers",
        ),
        row=3,
    )

    return keyboard


# =========================================================
# صفحه مشتریان
# =========================================================

def customers_keyboard():

    keyboard = InlineKeyboardMarkup()

    row = 1

    for customer_id, customer in customers.items():

        name = customer.get(
            "name",
            "بدون نام",
        )

        keyboard.add(
            InlineKeyboardButton(
                text=f"👤 {name}",
                callback_data=f"profile_{customer_id}",
            ),
            row=row,
        )

        row += 1

    keyboard.add(
        InlineKeyboardButton(
            text="➕ خرید برای شخص جدید",
            callback_data="new_customer",
        ),
        row=row,
    )

    row += 1

    keyboard.add(
        InlineKeyboardButton(
            text="🛒 ورود به فروشگاه",
            callback_data="shop",
        ),
        row=row,
    )

    return keyboard


# =========================================================
# مدیریت مشتری
# =========================================================

def customer_management_keyboard(customer_id):

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="🛒 خرید برای این شخص",
            callback_data=f"use_customer_{customer_id}",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="✏️ ویرایش مشخصات",
            callback_data=f"edit_customer_{customer_id}",
        ),
        row=2,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🗑 حذف شخص",
            callback_data=f"delete_customer_{customer_id}",
        ),
        row=3,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="customers",
        ),
        row=4,
    )

    return keyboard


# =========================================================
# دسته‌بندی‌ها
# =========================================================

def categories_keyboard():

    keyboard = InlineKeyboardMarkup()

    row = 1

    added = set()

    for product in PRODUCTS.values():

        category = product.get(
            "category"
        )

        if not category:
            continue

        if category in added:
            continue

        added.add(category)

        keyboard.add(
            InlineKeyboardButton(
                text=CATEGORY_NAMES.get(
                    category,
                    f"📦 {category}",
                ),
                callback_data=f"category_{category}",
            ),
            row=row,
        )

        row += 1

    keyboard.add(
        InlineKeyboardButton(
            text="🧺 سبد خرید",
            callback_data="cart",
        ),
        row=row,
    )

    row += 1

    keyboard.add(
        InlineKeyboardButton(
            text="👥 مشتریان",
            callback_data="customers",
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
# محصولات یک دسته
# =========================================================

def category_keyboard(category):

    keyboard = InlineKeyboardMarkup()

    row = 1

    found = False

    for product_id, product in PRODUCTS.items():

        if product.get("category") != category:
            continue

        if product.get("active", True) is False:
            continue

        found = True

        keyboard.add(
            InlineKeyboardButton(
                text=(
                    f"{product['name']} | "
                    f"{product['size']}"
                ),
                callback_data=f"product_{product_id}",
            ),
            row=row,
        )

        row += 1

    if not found:

        keyboard.add(
            InlineKeyboardButton(
                text="❌ محصولی در این دسته نیست",
                callback_data="shop",
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
            text="➕ اضافه کردن به سبد",
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

    cart = carts.get(
        user_id,
        {},
    )

    row = 1

    for product_id, quantity in cart.items():

        product = PRODUCTS.get(
            product_id
        )

        if not product:
            continue

        keyboard.add(
            InlineKeyboardButton(
                text=f"➕ {product['name']}",
                callback_data=f"plus_{product_id}",
            ),
            row=row,
        )

        row += 1

        keyboard.add(
            InlineKeyboardButton(
                text=f"➖ {product['name']}",
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
            text="👥 تغییر مشتری",
            callback_data="customers",
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
            text="📍 محل دیگر",
            callback_data="delivery_other",
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
            text="✏️ اصلاح سفارش",
            callback_data="edit_order",
        ),
        row=2,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="❌ لغو سفارش",
            callback_data="cancel_order",
        ),
        row=3,
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

    cart = carts.get(
        user_id,
        {},
    )

    if not cart:

        await message.reply(
            "🧺 سبد خرید شما خالی است.\n\n"
            "برای شروع خرید یکی از دسته‌بندی‌ها را انتخاب کنید.",
            components=categories_keyboard(),
        )

        return

    total = 0

    lines = [
        "🧺 سبد خرید شما:\n"
    ]

    for product_id, quantity in cart.items():

        product = PRODUCTS.get(
            product_id
        )

        if not product:
            continue

        subtotal = (
            product["price"]
            * quantity
        )

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

    customer_id = active_customer.get(
        user_id
    )

    customer = customers.get(
        customer_id,
        {},
    )

    cart = carts.get(
        user_id,
        {},
    )

    delivery = order_delivery.get(
        user_id,
        {},
    )

    total = 0

    lines = []

    for product_id, quantity in cart.items():

        product = PRODUCTS.get(
            product_id
        )

        if not product:
            continue

        subtotal = (
            product["price"]
            * quantity
        )

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
        f"📍 محل تحویل: "
        f"{delivery.get('place', '')}\n"
    )

    if delivery.get("address"):

        text += (
            f"🏠 آدرس: "
            f"{delivery['address']}\n"
        )

    text += (
        "🚚 هزینه تحویل: رایگان\n\n"
        "🛍 محصولات:\n"
        + "\n".join(lines)
        + f"\n\n💰 مبلغ کل: {total:,} تومان\n\n"
        "اطلاعات را بررسی کنید:"
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

    customer_id = active_customer.get(
        user_id
    )

    customer = customers.get(
        customer_id,
        {},
    )

    cart = carts.get(
        user_id,
        {},
    )

    delivery = order_delivery.get(
        user_id,
        {},
    )

    if not cart:

        await message.reply(
            "🧺 سبد خرید شما خالی است.",
            components=main_menu(),
        )

        return

    if not delivery.get("place"):

        await message.reply(
            "❌ محل تحویل مشخص نشده است.",
            components=delivery_keyboard(),
        )

        return

    total = 0

    lines = []

    for product_id, quantity in cart.items():

        product = PRODUCTS.get(
            product_id
        )

        if not product:
            continue

        subtotal = (
            product["price"]
            * quantity
        )

        total += subtotal

        lines.append(
            f"• {product['name']} "
            f"({product['size']}) × {quantity} "
            f"— {subtotal:,} تومان"
        )

    order_number = ORDER_NUMBER

    ORDER_NUMBER += 1

    address_text = ""

    if delivery.get("address"):

        address_text = (
            f"🏠 آدرس: "
            f"{delivery['address']}\n"
        )

    # -----------------------------------------------------
    # پیام مشتری
    # -----------------------------------------------------

    customer_text = (
        "🎉 سفارش شما با موفقیت ثبت شد!\n\n"
        f"🔢 شماره سفارش: #{order_number}\n"
        f"👤 نام: {customer.get('name', '')}\n"
        f"📱 تلفن: {customer.get('phone', '')}\n"
        f"📍 محل تحویل: "
        f"{delivery.get('place', '')}\n"
        f"{address_text}"
        "🚚 هزینه تحویل: رایگان\n\n"
        f"💰 مبلغ کل: {total:,} تومان\n\n"
        "از خرید شما از سبزی‌یو سپاسگزاریم 🌿"
    )

    await message.reply(
        customer_text
    )

    # -----------------------------------------------------
    # پیام مدیر
    # -----------------------------------------------------

    if ADMIN_CHAT_IDS:

        admin_text = (
            "🆕 سفارش جدید سبزی‌یو\n\n"
            f"🔢 شماره سفارش: #{order_number}\n\n"
            f"👤 مشتری: "
            f"{customer.get('name', '')}\n"
            f"📱 تلفن: "
            f"{customer.get('phone', '')}\n"
            f"📍 محل تحویل: "
            f"{delivery.get('place', '')}\n"
            f"{address_text}\n"
            "🛍 محصولات:\n"
            + "\n".join(lines)
            + f"\n\n💰 مبلغ کل: {total:,} تومان\n"
            "🚚 هزینه تحویل: رایگان\n\n"
            f"🆔 شناسه بله مشتری: {user_id}"
        )

        for admin_chat_id in ADMIN_CHAT_IDS:

            try:

                await bot.send_message(
                    chat_id=int(admin_chat_id),
                    text=admin_text,
                )

            except Exception as e:

                logging.error(
                    f"خطا در ارسال سفارش به مدیر "
                    f"{admin_chat_id}: {e}"
                )

    carts.pop(
        user_id,
        None,
    )

    order_delivery.pop(
        user_id,
        None,
    )

    user_states[user_id] = None


# =========================================================
# دریافت پیام‌ها
# =========================================================

@bot.event
async def on_message(message: Message):

    user_id = str(
        message.author.user_id
    )

    print(
        f"USER_ID: {user_id}",
        flush=True,
    )

    # -----------------------------------------------------
    # دریافت شماره تلفن
    # -----------------------------------------------------

    if message.contact:

        customer_id = active_customer.get(
            user_id
        )

        if not customer_id:

            customer_id = user_id

            active_customer[user_id] = customer_id

        customers.setdefault(
            customer_id,
            {},
        )

        customers[customer_id]["phone"] = (
            message.contact.phone_number
        )

        # بسیار مهم:
        # بعد از ثبت شماره، فقط به منوی اصلی می‌رویم.
        # اینجا به هیچ عنوان آدرس یا محل تحویل درخواست نمی‌شود.

        user_states[user_id] = None

        await message.reply(
            "✅ شماره تلفن ثبت شد.\n\n"
            "حالا وارد فروشگاه شوید و خرید خود را انجام دهید:",
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

        await message.reply(
            "سلام 👋\n\n"
            "به فروشگاه سبزی‌یو خوش آمدید 🌿\n\n"
            "👥 مشتری موردنظر را انتخاب کنید:",
            components=customers_keyboard(),
        )

        return

    state = user_states.get(
        user_id
    )

    # -----------------------------------------------------
    # دریافت آدرس
    # فقط برای سفارش جاری
    # -----------------------------------------------------

    if state == "delivery_address":

        if not text:

            await message.reply(
                "❌ آدرس نمی‌تواند خالی باشد.\n\n"
                "لطفاً آدرس همان سفارش را وارد کنید:"
            )

            return

        order_delivery[user_id] = {
            "place": "محل دیگر",
            "address": text,
        }

        user_states[user_id] = None

        await show_order_summary(
            message,
            user_id,
        )

        return

    # -----------------------------------------------------
    # دریافت نام
    # -----------------------------------------------------

    if state == "name":

        customer_id = active_customer.get(
            user_id
        )

        if not customer_id:

            customer_id = user_id

            active_customer[user_id] = customer_id

        customers.setdefault(
            customer_id,
            {},
        )

        customers[customer_id]["name"] = text

        user_states[user_id] = "phone"

        await message.reply(
            "👤 نام ثبت شد.\n\n"
            "📱 لطفاً شماره تلفن خود را با دکمه زیر ارسال کنید:",
            components=phone_keyboard(),
        )

        return

    # -----------------------------------------------------
    # دریافت شماره به صورت متن
    # -----------------------------------------------------

    if state == "phone":

        customer_id = active_customer.get(
            user_id
        )

        if not customer_id:

            customer_id = user_id

            active_customer[user_id] = customer_id

        customers.setdefault(
            customer_id,
            {},
        )

        customers[customer_id]["phone"] = text

        user_states[user_id] = None

        await message.reply(
            "✅ شماره تلفن ثبت شد.\n\n"
            "حالا وارد فروشگاه شوید و خرید خود را انجام دهید:",
            components=main_menu(),
        )

        return

    # -----------------------------------------------------
    # سلام
    # -----------------------------------------------------

    if text in [
        "سلام",
        "سلام 👋",
    ]:

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

    user_id = str(
        callback.from_user.user_id
    )

    data = callback.data

    # =====================================================
    # مشتریان
    # =====================================================

    if data == "customers":

        user_states[user_id] = None

        await callback.message.reply(
            "👥 مشتریان ثبت‌شده\n\n"
            "مشتری موردنظر را انتخاب کنید:",
            components=customers_keyboard(),
        )

        return

    # =====================================================
    # پروفایل مشتری
    # =====================================================

    if data.startswith("profile_"):

        customer_id = data.replace(
            "profile_",
            "",
        )

        customer = customers.get(
            customer_id
        )

        if not customer:

            await callback.message.reply(
                "❌ اطلاعات مشتری پیدا نشد.",
                components=customers_keyboard(),
            )

            return

        await callback.message.reply(
            f"👤 نام: "
            f"{customer.get('name', '')}\n"
            f"📱 شماره: "
            f"{customer.get('phone', 'ثبت نشده')}\n\n"
            "عملیات موردنظر را انتخاب کنید:",
            components=customer_management_keyboard(
                customer_id
            ),
        )

        return

    # =====================================================
    # استفاده از مشتری
    # =====================================================

    if data.startswith("use_customer_"):

        customer_id = data.replace(
            "use_customer_",
            "",
        )

        customer = customers.get(
            customer_id
        )

        if not customer:

            await callback.message.reply(
                "❌ مشتری پیدا نشد.",
                components=customers_keyboard(),
            )

            return

        active_customer[user_id] = customer_id

        await callback.message.reply(
            f"👤 مشتری انتخاب شد: "
            f"{customer.get('name', '')}\n\n"
            "حالا وارد فروشگاه شوید:",
            components=main_menu(),
        )

        return

    # =====================================================
    # ویرایش مشتری
    # =====================================================

    if data.startswith("edit_customer_"):

        customer_id = data.replace(
            "edit_customer_",
            "",
        )

        if customer_id not in customers:

            await callback.message.reply(
                "❌ مشتری پیدا نشد.",
                components=customers_keyboard(),
            )

            return

        active_customer[user_id] = customer_id

        user_states[user_id] = "name"

        await callback.message.reply(
            "✏️ ویرایش مشخصات\n\n"
            "👤 نام و نام خانوادگی جدید را وارد کنید:"
        )

        return

    # =====================================================
    # حذف مشتری
    # =====================================================

    if data.startswith("delete_customer_"):

        customer_id = data.replace(
            "delete_customer_",
            "",
        )

        if customer_id not in customers:

            await callback.message.reply(
                "❌ مشتری پیدا نشد.",
                components=customers_keyboard(),
            )

            return

        customers.pop(
            customer_id,
            None,
        )

        if active_customer.get(
            user_id
        ) == customer_id:

            active_customer.pop(
                user_id,
                None,
            )

        await callback.message.reply(
            "🗑 مشتری با موفقیت حذف شد.",
            components=customers_keyboard(),
        )

        return

    # =====================================================
    # مشتری جدید
    # =====================================================

    if data == "new_customer":

        customer_id = (
            f"{user_id}_customer_"
            f"{len(customers) + 1}"
        )

        customers[customer_id] = {}

        active_customer[user_id] = (
            customer_id
        )

        user_states[user_id] = "name"

        await callback.message.reply(
            "➕ خرید برای شخص جدید\n\n"
            "👤 لطفاً نام و نام خانوادگی را وارد کنید:"
        )

        return

    # =====================================================
    # خانه
    # =====================================================

    if data == "home":

        await callback.message.reply(
            "🌿 سبزی‌یو\n\n"
            "به فروشگاه سبزی‌یو خوش آمدید.",
            components=main_menu(),
        )

        return

    # =====================================================
    # فروشگاه
    # =====================================================

    if data == "shop":

        await callback.message.reply(
            "🛒 فروشگاه سبزی‌یو\n\n"
            "دسته‌بندی موردنظر را انتخاب کنید:",
            components=categories_keyboard(),
        )

        return

    # =====================================================
    # دسته‌بندی
    # =====================================================

    if data.startswith("category_"):

        category = data.replace(
            "category_",
            "",
        )

        await callback.message.reply(
            f"{CATEGORY_NAMES.get(category, '📦 محصولات')}\n\n"
            "محصول موردنظر را انتخاب کنید:",
            components=category_keyboard(category),
        )

        return

    # =====================================================
    # محصول
    # =====================================================

    if data.startswith("product_"):

        product_id = data.replace(
            "product_",
            "",
        )

        product = PRODUCTS.get(
            product_id
        )

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
            "برای افزودن محصول به سبد، "
            "دکمه زیر را بزنید:",
            components=product_keyboard(
                product_id
            ),
        )

        return

    # =====================================================
    # اضافه کردن محصول
    # =====================================================

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
            carts[user_id].get(
                product_id,
                0,
            ) + 1
        )

        product = PRODUCTS[product_id]

        await callback.message.reply(
            f"✅ «{product['name']}» "
            "به سبد خرید اضافه شد.\n\n"
            f"تعداد فعلی: "
            f"{carts[user_id][product_id]}",
            components=cart_keyboard(
                user_id
            ),
        )

        return

    # =====================================================
    # افزایش تعداد
    # =====================================================

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
            carts[user_id].get(
                product_id,
                0,
            ) + 1
        )

        await show_cart(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # کاهش تعداد
    # =====================================================

    if data.startswith("minus_"):

        product_id = data.replace(
            "minus_",
            "",
        )

        if product_id in carts.get(
            user_id,
            {},
        ):

            carts[user_id][product_id] -= 1

            if carts[user_id][product_id] <= 0:

                del carts[user_id][product_id]

        await show_cart(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # سبد خرید
    # =====================================================

    if data == "cart":

        await show_cart(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # ثبت سفارش
    # =====================================================

    if data == "order":

        if not carts.get(
            user_id
        ):

            await callback.message.reply(
                "🧺 سبد خرید شما خالی است.",
                components=categories_keyboard(),
            )

            return

        customer_id = active_customer.get(
            user_id
        )

        customer = customers.get(
            customer_id,
            {},
        )

        if not customer.get(
            "name"
        ):

            user_states[user_id] = "name"

            await callback.message.reply(
                "👤 لطفاً نام و نام خانوادگی را وارد کنید:"
            )

            return

        if not customer.get(
            "phone"
        ):

            user_states[user_id] = "phone"

            await callback.message.reply(
                "📱 لطفاً شماره تلفن خود را ارسال کنید:",
                components=phone_keyboard(),
            )

            return

        # محل تحویل فقط هنگام ثبت سفارش
        order_delivery.pop(
            user_id,
            None,
        )

        user_states[user_id] = "delivery"

        await callback.message.reply(
            f"👤 مشتری: "
            f"{customer['name']}\n\n"
            "📍 محل تحویل سفارش را انتخاب کنید:",
            components=delivery_keyboard(),
        )

        return

    # =====================================================
    # هیأت امنا
    # =====================================================

    if data == "delivery_heyat":

        order_delivery[user_id] = {
            "place": "هیأت امنا",
            "address": "",
        }

        user_states[user_id] = None

        await show_order_summary(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # محل دیگر
    # =====================================================

    if data == "delivery_other":

        order_delivery[user_id] = {
            "place": "محل دیگر",
            "address": "",
        }

        user_states[user_id] = (
            "delivery_address"
        )

        await callback.message.reply(
            "📍 محل دیگر انتخاب شد.\n\n"
            "🏠 لطفاً آدرس همان سفارش را وارد کنید:"
        )

        return

    # =====================================================
    # اصلاح سفارش
    # =====================================================

    if data == "edit_order":

        user_states[user_id] = None

        await callback.message.reply(
            "✏️ اصلاح سفارش\n\n"
            "سبد خرید را اصلاح کنید:",
            components=cart_keyboard(
                user_id
            ),
        )

        return

    # =====================================================
    # تأیید سفارش
    # =====================================================

    if data == "confirm_order":

        await confirm_order(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # لغو سفارش
    # =====================================================

    if data == "cancel_order":

        carts.pop(
            user_id,
            None,
        )

        order_delivery.pop(
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

    print(
        "=== BALE BOT CONNECTED ==="
    )

    print(
        "SabziU Bale Store is ready!"
    )


# =========================================================
# اجرای ربات
# =========================================================

bot.run()
