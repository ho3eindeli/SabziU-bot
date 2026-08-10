import os
import logging

from bale import (
Bot,
Message,
CallbackQuery,
InlineKeyboardMarkup,
InlineKeyboardButton,
MenuKeyboardMarkup,
MenuKeyboardButton,
)

TOKEN = os.getenv("BALE_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("BALE_ADMIN_CHAT_ID")

if not TOKEN:
raise RuntimeError("BALE_BOT_TOKEN تنظیم نشده است.")

logging.basicConfig(
level=logging.INFO,
format="%(asctime)s - %(levelname)s - %(message)s",
)

bot = Bot(token=TOKEN)

ORDER_NUMBER = 1000

customers = {}
carts = {}
user_states = {}

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

def main_menu():
keyboard = InlineKeyboardMarkup()

```
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
```

def categories_keyboard():
keyboard = InlineKeyboardMarkup()

```
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
```

def category_keyboard(category):
keyboard = InlineKeyboardMarkup()

```
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
```

def product_keyboard(product_id):
keyboard = InlineKeyboardMarkup()

```
keyboard.add(
    InlineKeyboardButton(
        text="🛒 افزودن به سبد",
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
```

def cart_keyboard(user_id):
keyboard = InlineKeyboardMarkup()

```
cart = carts.get(user_id, {})

row = 1

for product_id, quantity in cart.items():
    product = PRODUCTS[product_id]

    keyboard.add(
        InlineKeyboardButton(
            text=f"➕ اضافه کردن | {product['name']}",
            callback_data=f"plus_{product_id}",
        ),
        row=row,
    )
    row += 1

    keyboard.add(
        InlineKeyboardButton(
            text=f"➖ کم کردن | {product['name']}",
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
```

def phone_keyboard():
keyboard = MenuKeyboardMarkup()

```
keyboard.add(
    MenuKeyboardButton(
        "📱 ارسال شماره تلفن",
        request_contact=True,
    )
)

return keyboard
```

def delivery_keyboard():
keyboard = InlineKeyboardMarkup()

```
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
```

def final_order_keyboard():
keyboard = InlineKeyboardMarkup()

```
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
```

async def show_cart(message, user_id):
cart = carts.get(user_id, {})

```
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

lines.append(f"\n💰 جمع کل: {total:,} تومان")

await message.reply(
    "\n".join(lines),
    components=cart_keyboard(user_id),
)
```

async def show_order_summary(message, user_id):
customer = customers.get(user_id, {})
cart = carts.get(user_id, {})

```
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
    "اگر اطلاعات صحیح است، «تأیید و ثبت سفارش» را بزنید."
)

await message.reply(
    text,
    components=final_order_keyboard(),
)
```

async def confirm_order(message, user_id):
global ORDER_NUMBER

```
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

carts.pop(user_id, None)
user_states[user_id] = None
```

@bot.event
async def on_message(message: Message):

```
user_id = str(message.author.user_id)

# =====================================================
# دریافت Contact
# =====================================================

if message.contact is not None:

    phone = message.contact.phone_number

    customers.setdefault(
        user_id,
        {},
    )

    customers[user_id]["phone"] = str(phone)

    logging.info(
        f"PHONE RECEIVED: {user_id}"
    )

    if carts.get(user_id):

        user_states[user_id] = "delivery"

        await message.reply(
            "✅ شماره تلفن شما با موفقیت ثبت شد.\n\n"
            "📍 محل تحویل سفارش را انتخاب کنید:",
            components=delivery_keyboard(),
        )

    else:

        user_states[user_id] = None

        await message.reply(
            "✅ شماره تلفن شما با موفقیت ثبت شد.\n\n"
            "🛒 حالا می‌توانید فروشگاه سبزی‌یو را باز کنید:",
            components=main_menu(),
        )

    return

# =====================================================
# پیام متنی
# =====================================================

if message.content is None:
    return

text = message.content.strip()

# =====================================================
# /start
# =====================================================

if text == "/start":

    user_states[user_id] = None

    await message.reply(
        "سلام 👋\n\n"
        "به فروشگاه سبزی‌یو خوش آمدید 🌿\n\n"
        "از منوی زیر انتخاب کنید:",
        components=main_menu(),
    )

    return

# =====================================================
# لغو
# =====================================================

if text == "/cancel":

    user_states[user_id] = None

    await message.reply(
        "❌ عملیات لغو شد.",
        components=main_menu(),
    )

    return

state = user_states.get(user_id)

# =====================================================
# دریافت نام
# =====================================================

if state == "name":

    customers.setdefault(
        user_id,
        {},
    )

    customers[user_id]["name"] = text

    user_states[user_id] = "phone"

    await message.reply(
        "👤 نام شما ثبت شد.\n\n"
        "📱 لطفاً شماره تلفن خود را با دکمه زیر ارسال کنید:",
        components=phone_keyboard(),
    )

    return

# =====================================================
# شماره تلفن دستی
# =====================================================

if state == "phone":

    customers.setdefault(
        user_id,
        {},
    )

    customers[user_id]["phone"] = text

    logging.info(
        f"PHONE MANUAL: {user_id}"
    )

    if carts.get(user_id):

        user_states[user_id] = "delivery"

        await message.reply(
            "✅ شماره تلفن شما ثبت شد.\n\n"
            "📍 محل تحویل سفارش را انتخاب کنید:",
            components=delivery_keyboard(),
        )

    else:

        user_states[user_id] = None

        await message.reply(
            "✅ شماره تلفن شما ثبت شد.\n\n"
            "🛒 حالا می‌توانید فروشگاه سبزی‌یو را باز کنید:",
            components=main_menu(),
        )

    return

# =====================================================
# سلام
# =====================================================

if text in ["سلام", "سلام 👋"]:

    await message.reply(
        "سلام 👋\n\n"
        "به فروشگاه سبزی‌یو خوش آمدید 🌿",
        components=main_menu(),
    )
```

@bot.event
async def on_callback(callback: CallbackQuery):

```
user_id = str(callback.from_user.user_id)
data = callback.data

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

# =====================================================
# انتخاب محصول
# =====================================================

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

# =====================================================
# افزودن محصول
# =====================================================

if data.startswith("add_"):

    product_id = data.replace(
        "add_",
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

    product = PRODUCTS[product_id]

    await callback.message.reply(
        f"✅ «{product['name']}» به سبد خرید اضافه شد.\n\n"
        f"📦 تعداد فعلی: {carts[user_id][product_id]}",
        components=cart_keyboard(user_id),
    )

    return

# =====================================================
# اضافه کردن سفارش
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
        carts[user_id].get(product_id, 0) + 1
    )

    await show_cart(
        callback.message,
        user_id,
    )

    return

# =====================================================
# کم کردن سفارش
# =====================================================

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

    if not customer.get("name"):

        user_states[user_id] = "name"

        await callback.message.reply(
            "📦 ثبت سفارش\n\n"
            "👤 لطفاً نام و نام خانوادگی خود را وارد کنید:"
        )

        return

    if not customer.get("phone"):

        user_states[user_id] = "phone"

        await callback.message.reply(
            "📱 لطفاً شماره تلفن خود را با دکمه زیر ارسال کنید:",
            components=phone_keyboard(),
        )

        return

    user_states[user_id] = "delivery"

    await callback.message.reply(
        "📍 محل تحویل سفارش را انتخاب کنید:",
        components=delivery_keyboard(),
    )

    return

# =====================================================
# محل تحویل
# =====================================================

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

    user_states[user_id] = None

    await callback.message.reply(
        "❌ سفارش لغو شد.",
        components=main_menu(),
    )

    return
```

@bot.event
async def on_ready():

```
print("=== BALE BOT CONNECTED ===")
print("SabziU Bale Store is ready!")
```

bot.run()
