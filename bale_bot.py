import os
import json
import logging
from datetime import datetime

from bale import (
    Bot,
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    MenuKeyboardMarkup,
    MenuKeyboardButton,
)

from products import PRODUCTS


# =========================================================
# تنظیمات
# =========================================================

TOKEN = os.getenv("BALE_BOT_TOKEN")

ADMIN_CHAT_IDS = [
    x.strip()
    for x in os.getenv("BALE_ADMIN_CHAT_IDS", "").split(",")
    if x.strip()
]

PAYMENT_CARD = os.getenv(
    "BALE_PAYMENT_CARD",
    "شماره کارت در تنظیمات ربات وارد نشده است",
)

PAYMENT_OWNER = os.getenv(
    "BALE_PAYMENT_OWNER",
    "",
)

STATE_FILE = "bale_data.json"

if not TOKEN:
    raise RuntimeError("BALE_BOT_TOKEN تنظیم نشده است.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

bot = Bot(token=TOKEN)


# =========================================================
# داده‌ها
# =========================================================

def load_data():
    default = {
        "customers": {},
        "orders": [],
        "next_order_number": 1000,
    }

    if not os.path.exists(STATE_FILE):
        return default

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        data.setdefault("customers", {})
        data.setdefault("orders", [])
        data.setdefault("next_order_number", 1000)

        for customer in data["customers"].values():
            customer.setdefault("addresses", [])

        return data

    except Exception as e:
        logging.error(f"خطا در خواندن اطلاعات: {e}")
        return default


DATA = load_data()

user_states = {}
active_customer = {}
carts = {}
current_delivery = {}


def save_data():
    temp = STATE_FILE + ".tmp"

    with open(temp, "w", encoding="utf-8") as f:
        json.dump(
            DATA,
            f,
            ensure_ascii=False,
            indent=2,
        )

    os.replace(temp, STATE_FILE)


# =========================================================
# ابزارها
# =========================================================

def now_text():
    return datetime.now().strftime("%Y/%m/%d - %H:%M")


def money(value):
    return f"{int(value):,} تومان"


def get_user_customers(user_id):
    prefix = f"{user_id}_"

    return [
        (cid, customer)
        for cid, customer in DATA["customers"].items()
        if cid.startswith(prefix)
    ]


def cart_total(user_id):
    total = 0

    for product_id, quantity in carts.get(user_id, {}).items():
        product = PRODUCTS.get(product_id)

        if product:
            total += product["price"] * quantity

    return total


def delivery_fee(delivery):
    return int(delivery.get("fee", 0))


def clear_state(user_id):
    user_states.pop(user_id, None)


def clear_order_session(user_id):
    carts.pop(user_id, None)
    current_delivery.pop(user_id, None)
    user_states.pop(user_id, None)


# =========================================================
# دسته‌بندی‌ها
# =========================================================

CATEGORY_NAMES = {
    "fried": "🌿 سبزی‌های سرخ‌شده",
    "raw": "🥬 سبزی‌های خام",
    "pickles": "🥒 ترشیجات",
    "syrup": "🥭 شربت‌ها",
    "jam": "🍓 مرباها",
    "spices": "🧂 ادویه‌ها",
    "spice": "🧂 ادویه‌ها",
    "drinks": "🥤 نوشیدنی‌ها",
    "sauce": "🥫 سس‌ها",
    "distillate": "🌱 عرقیات",
    "semi_ready": "🍽️ محصولات نیمه‌آماده",
    "fresh": "🥬 محصولات تازه و آماده پخت",
    "herbs": "🌿 سبزی‌ها",
}


# =========================================================
# صفحه اول
# =========================================================

def home_keyboard():
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="🧾 خریدهای قبلی",
            callback_data="previous_orders",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🛒 فروشگاه سبزی‌یو",
            callback_data="shop",
        ),
        row=2,
    )

    return keyboard


async def show_home(message):
    clear_state(str(message.author.user_id))

    await message.reply(
        "سلام 👋\n\n"
        "به فروشگاه سبزی‌یو خوش آمدید 🌿\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        components=home_keyboard(),
    )


# =========================================================
# بازگشت
# =========================================================

def back_keyboard(callback_data):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data=callback_data,
        ),
        row=1,
    )

    return keyboard


# =========================================================
# خریدهای قبلی
# =========================================================

def previous_orders_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()

    orders = [
        order
        for order in DATA["orders"]
        if str(order.get("user_id")) == str(user_id)
    ]

    orders.sort(
        key=lambda x: x.get("created_at", ""),
        reverse=True,
    )

    row = 1

    for order in orders:
        keyboard.add(
            InlineKeyboardButton(
                text=(
                    f"#{order['order_number']} | "
                    f"{order['date']} | "
                    f"{money(order['total'])}"
                ),
                callback_data=f"order_history_{order['order_number']}",
            ),
            row=row,
        )
        row += 1

    keyboard.add(
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="home",
        ),
        row=row,
    )

    return keyboard


async def show_previous_orders(message, user_id):
    orders = [
        order
        for order in DATA["orders"]
        if str(order.get("user_id")) == str(user_id)
    ]

    if not orders:
        text = (
            "🧾 خریدهای قبلی\n\n"
            "هنوز سفارشی برای شما ثبت نشده است."
        )
    else:
        text = (
            "🧾 خریدهای قبلی\n\n"
            "شماره سفارش | تاریخ | مبلغ خرید"
        )

    await message.reply(
        text,
        components=previous_orders_keyboard(user_id),
    )


async def show_order_history(message, user_id, order_number):
    order = None

    for item in DATA["orders"]:
        if (
            str(item.get("user_id")) == str(user_id)
            and str(item.get("order_number")) == str(order_number)
        ):
            order = item
            break

    if not order:
        await message.reply(
            "❌ سفارش پیدا نشد.",
            components=back_keyboard("previous_orders"),
        )
        return

    lines = []

    for item in order.get("items", []):
        lines.append(
            f"• {item['name']}\n"
            f"  {item['size']} × {item['quantity']}\n"
            f"  {money(item['subtotal'])}"
        )

    text = (
        "🧾 جزئیات سفارش\n\n"
        f"🔢 شماره سفارش: #{order['order_number']}\n"
        f"📅 تاریخ خرید: {order['date']}\n\n"
        "🛍 ریز سفارش:\n"
        + "\n".join(lines)
        + "\n\n"
        f"💰 مبلغ کالاها: {money(order['subtotal'])}\n"
        f"🚚 هزینه ارسال: {money(order['delivery_fee'])}\n"
        f"💳 مبلغ نهایی: {money(order['total'])}\n\n"
        f"📍 محل تحویل: {order.get('delivery_place', '')}\n"
    )

    if order.get("address"):
        text += f"🏠 آدرس: {order['address']}\n"

    if order.get("shipping_method"):
        text += f"🚚 روش ارسال: {order['shipping_method']}\n"

    await message.reply(
        text,
        components=back_keyboard("previous_orders"),
    )


# =========================================================
# فروشگاه
# =========================================================

def categories_keyboard():
    keyboard = InlineKeyboardMarkup()

    categories = []

    for product in PRODUCTS.values():
        category = product.get("category")

        if (
            category
            and category not in categories
            and product.get("active", True) is not False
        ):
            categories.append(category)

    row = 1

    for category in categories:
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
            text="⬅️ بازگشت",
            callback_data="home",
        ),
        row=row,
    )

    return keyboard


async def show_shop(message):
    clear_state(str(message.author.user_id))

    await message.reply(
        "🛒 فروشگاه سبزی‌یو\n\n"
        "دسته‌بندی کالاها را انتخاب کنید:",
        components=categories_keyboard(),
    )


def category_keyboard(category):
    keyboard = InlineKeyboardMarkup()
    row = 1

    for product_id, product in PRODUCTS.items():
        if product.get("category") != category:
            continue

        if product.get("active", True) is False:
            continue

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
            text="🧺 سبد خرید",
            callback_data="cart",
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


async def show_category(message, category):
    await message.reply(
        f"{CATEGORY_NAMES.get(category, '📦 محصولات')}\n\n"
        "محصول موردنظر را انتخاب کنید:",
        components=category_keyboard(category),
    )


def product_keyboard(product_id, category):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="➕ افزودن به سبد",
            callback_data=f"add_{product_id}",
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
            text="⬅️ بازگشت",
            callback_data=f"category_{category}",
        ),
        row=3,
    )

    return keyboard


# =========================================================
# سبد خرید
# =========================================================

def cart_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    row = 1

    for product_id, quantity in carts.get(user_id, {}).items():
        product = PRODUCTS.get(product_id)

        if not product:
            continue

        keyboard.add(
            InlineKeyboardButton(
                text=f"➕ {product['name']} ({quantity})",
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

    if carts.get(user_id):
        keyboard.add(
            InlineKeyboardButton(
                text="📦 ثبت سفارش",
                callback_data="start_order",
            ),
            row=row,
        )
        row += 1

    keyboard.add(
        InlineKeyboardButton(
            text="➕ ادامه خرید",
            callback_data="shop",
        ),
        row=row,
    )
    row += 1

    keyboard.add(
        InlineKeyboardButton(
            text="❌ لغو خرید",
            callback_data="cancel_cart",
        ),
        row=row,
    )

    return keyboard


async def show_cart(message, user_id):
    cart = carts.get(user_id, {})

    if not cart:
        await message.reply(
            "🧺 سبد خرید شما خالی است.",
            components=back_keyboard("shop"),
        )
        return

    lines = ["🧾 فاکتور خرید تا این لحظه\n"]
    subtotal = 0

    for product_id, quantity in cart.items():
        product = PRODUCTS.get(product_id)

        if not product:
            continue

        item_total = product["price"] * quantity
        subtotal += item_total

        lines.append(
            f"• {product['name']}\n"
            f"  {product['size']} × {quantity}\n"
            f"  {money(item_total)}\n"
        )

    lines.append(f"💰 مبلغ کالاها: {money(subtotal)}")

    await message.reply(
        "\n".join(lines),
        components=cart_keyboard(user_id),
    )


# =========================================================
# مشتری
# =========================================================

def customer_start_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    customers = get_user_customers(user_id)

    if customers:
        keyboard.add(
            InlineKeyboardButton(
                text="👤 مشتری قدیمی",
                callback_data="old_customer",
            ),
            row=1,
        )

        keyboard.add(
            InlineKeyboardButton(
                text="➕ مشتری جدید",
                callback_data="new_customer",
            ),
            row=2,
        )

        keyboard.add(
            InlineKeyboardButton(
                text="⬅️ بازگشت",
                callback_data="cart",
            ),
            row=3,
        )
    else:
        keyboard.add(
            InlineKeyboardButton(
                text="👤 ثبت مشخصات",
                callback_data="new_customer",
            ),
            row=1,
        )

        keyboard.add(
            InlineKeyboardButton(
                text="⬅️ بازگشت",
                callback_data="cart",
            ),
            row=2,
        )

    return keyboard


async def show_customer_start(message, user_id):
    customers = get_user_customers(user_id)

    if customers:
        text = (
            "👤 مشخصات مشتری\n\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:"
        )
    else:
        text = (
            "👤 ثبت مشخصات مشتری\n\n"
            "برای ادامه سفارش ابتدا مشخصات خود را ثبت کنید:"
        )

    await message.reply(
        text,
        components=customer_start_keyboard(user_id),
    )


def customer_list_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    row = 1

    for customer_id, customer in get_user_customers(user_id):
        keyboard.add(
            InlineKeyboardButton(
                text=f"👤 {customer.get('name', 'بدون نام')}",
                callback_data=f"select_customer_{customer_id}",
            ),
            row=row,
        )
        row += 1

    keyboard.add(
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="customer_start",
        ),
        row=row,
    )

    return keyboard


async def show_customer_list(message, user_id):
    await message.reply(
        "👤 مشتریان ثبت‌شده\n\n"
        "مشتری موردنظر را انتخاب کنید:",
        components=customer_list_keyboard(user_id),
    )


def customer_profile_keyboard(customer_id):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="🛒 انتخاب این مشتری",
            callback_data=f"use_customer_{customer_id}",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="✏️ اصلاح مشخصات",
            callback_data=f"edit_customer_{customer_id}",
        ),
        row=2,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🗑 حذف مشتری",
            callback_data=f"delete_customer_{customer_id}",
        ),
        row=3,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="📍 مدیریت آدرس‌ها",
            callback_data=f"addresses_profile_{customer_id}",
        ),
        row=4,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="old_customer",
        ),
        row=5,
    )

    return keyboard


async def show_customer_profile(message, customer_id):
    customer = DATA["customers"].get(customer_id)

    if not customer:
        await message.reply("❌ مشتری پیدا نشد.")
        return

    addresses_count = len(customer.get("addresses", []))

    await message.reply(
        f"👤 نام: {customer.get('name', '')}\n"
        f"📱 تلفن: {customer.get('phone', '')}\n"
        f"📍 تعداد آدرس‌ها: {addresses_count}\n\n"
        "عملیات موردنظر:",
        components=customer_profile_keyboard(customer_id),
    )


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
# آدرس‌ها
# =========================================================

def address_list_keyboard(customer_id, back_callback=None):
    keyboard = InlineKeyboardMarkup()

    customer = DATA["customers"].get(customer_id, {})
    addresses = customer.get("addresses", [])

    row = 1

    for index, address in enumerate(addresses):
        keyboard.add(
            InlineKeyboardButton(
                text=f"📍 {address.get('title', 'آدرس')}",
                callback_data=f"select_address_{customer_id}_{index}",
            ),
            row=row,
        )
        row += 1

    keyboard.add(
        InlineKeyboardButton(
            text="➕ افزودن آدرس",
            callback_data=f"add_address_{customer_id}",
        ),
        row=row,
    )
    row += 1

    if back_callback is None:
        back_callback = f"profile_{customer_id}"

    keyboard.add(
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data=back_callback,
        ),
        row=row,
    )

    return keyboard


async def show_addresses(
    message,
    customer_id,
    back_callback=None,
):
    customer = DATA["customers"].get(customer_id)

    if not customer:
        await message.reply("❌ مشتری پیدا نشد.")
        return

    addresses = customer.get("addresses", [])

    if addresses:
        text = (
            "📍 آدرس‌های ذخیره‌شده\n\n"
            "آدرس موردنظر را انتخاب کنید:"
        )
    else:
        text = (
            "📍 آدرس‌های من\n\n"
            "هنوز آدرسی ثبت نشده است.\n\n"
            "می‌توانید یک آدرس جدید اضافه کنید."
        )

    await message.reply(
        text,
        components=address_list_keyboard(
            customer_id,
            back_callback,
        ),
    )


def address_management_keyboard(
    customer_id,
    index,
    back_callback,
):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="🛒 انتخاب این آدرس",
            callback_data=f"use_address_{customer_id}_{index}",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="✏️ اصلاح آدرس",
            callback_data=f"edit_address_{customer_id}_{index}",
        ),
        row=2,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🗑 حذف آدرس",
            callback_data=f"delete_address_{customer_id}_{index}",
        ),
        row=3,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data=back_callback,
        ),
        row=4,
    )

    return keyboard


# =========================================================
# ثبت مشتری
# =========================================================

async def start_new_customer(message, user_id):
    customers = get_user_customers(user_id)
    number = len(customers) + 1

    while f"{user_id}_customer_{number}" in DATA["customers"]:
        number += 1

    customer_id = f"{user_id}_customer_{number}"

    DATA["customers"][customer_id] = {
        "name": "",
        "phone": "",
        "addresses": [],
    }

    active_customer[user_id] = customer_id

    user_states[user_id] = {
        "type": "customer_name",
        "customer_id": customer_id,
    }

    save_data()

    await message.reply(
        "👤 ثبت مشخصات مشتری\n\n"
        "لطفاً نام و نام خانوادگی را وارد کنید:"
    )


async def start_new_address(message, user_id, customer_id):
    if customer_id not in DATA["customers"]:
        await message.reply("❌ مشتری پیدا نشد.")
        return

    active_customer[user_id] = customer_id

    user_states[user_id] = {
        "type": "address_title",
        "customer_id": customer_id,
    }

    await message.reply(
        "➕ افزودن آدرس جدید\n\n"
        "یک نام برای آدرس وارد کنید.\n"
        "مثلاً: خانه، محل کار، فروشگاه"
    )


# =========================================================
# تحویل
# =========================================================

def free_delivery_keyboard():
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="🚶 تحویل حضوری",
            callback_data="delivery_pickup",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🏢 تحویل در هیأت امنا",
            callback_data="delivery_heyat",
        ),
        row=2,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="delivery",
        ),
        row=3,
    )

    return keyboard


def delivery_keyboard():
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="🆓 تحویل رایگان / حضوری",
            callback_data="free_delivery",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="📍 آدرس‌های من",
            callback_data="delivery_saved",
        ),
        row=2,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="➕ افزودن آدرس جدید",
            callback_data="delivery_new_address",
        ),
        row=3,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="cart",
        ),
        row=4,
    )

    return keyboard


async def show_delivery(message, user_id):
    await message.reply(
        "📍 محل تحویل سفارش\n\n"
        "روش تحویل را انتخاب کنید:",
        components=delivery_keyboard(),
    )


def shipping_keyboard():
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="🚕 الوپیک",
            callback_data="shipping_alopik",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🛵 اسنپ‌باکس",
            callback_data="shipping_snapp",
        ),
        row=2,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="delivery_saved",
        ),
        row=3,
    )

    return keyboard


# =========================================================
# فاکتور نهایی
# =========================================================

def final_invoice_keyboard():
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="💳 پرداخت",
            callback_data="payment",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="✏️ اصلاح کالاهای انتخاب‌شده",
            callback_data="edit_cart",
        ),
        row=2,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="📍 اصلاح نحوه تحویل",
            callback_data="delivery",
        ),
        row=3,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="➕ ادامه خرید",
            callback_data="shop",
        ),
        row=4,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="❌ لغو خرید",
            callback_data="cancel_cart",
        ),
        row=5,
    )

    return keyboard


async def show_final_invoice(message, user_id):
    delivery = current_delivery.get(user_id, {})
    customer_id = active_customer.get(user_id)
    customer = DATA["customers"].get(customer_id, {})

    if not carts.get(user_id):
        await show_cart(message, user_id)
        return

    subtotal = cart_total(user_id)
    fee = delivery_fee(delivery)
    total = subtotal + fee

    lines = []

    for product_id, quantity in carts.get(user_id, {}).items():
        product = PRODUCTS.get(product_id)

        if not product:
            continue

        item_total = product["price"] * quantity

        lines.append(
            f"• {product['name']}\n"
            f"  {product['size']} × {quantity}\n"
            f"  {money(item_total)}"
        )

    text = (
        "🧾 فاکتور خرید\n\n"
        f"👤 نام: {customer.get('name', '')}\n"
        f"📱 تلفن: {customer.get('phone', '')}\n\n"
        "🛍 محصولات:\n"
        + "\n".join(lines)
        + "\n\n"
        f"💰 مبلغ کالاها: {money(subtotal)}\n"
        f"🚚 هزینه ارسال: {money(fee)}\n"
        f"💳 مبلغ نهایی: {money(total)}\n\n"
        f"📍 محل تحویل: {delivery.get('title', '')}\n"
    )

    if delivery.get("address"):
        text += f"🏠 آدرس: {delivery['address']}\n"

    if delivery.get("shipping_method"):
        text += f"🚚 روش ارسال: {delivery['shipping_method']}\n"

    await message.reply(
        text,
        components=final_invoice_keyboard(),
    )


# =========================================================
# ثبت سفارش
# =========================================================

async def start_order(message, user_id):
    if not carts.get(user_id):
        await message.reply(
            "🧺 سبد خرید شما خالی است.",
            components=back_keyboard("shop"),
        )
        return

    customer_id = active_customer.get(user_id)

    if customer_id and customer_id in DATA["customers"]:
        await show_customer_profile(
            message,
            customer_id,
        )
        return

    await show_customer_start(message, user_id)


async def create_order(message, user_id):
    customer_id = active_customer.get(user_id)

    if not customer_id or customer_id not in DATA["customers"]:
        await show_customer_start(message, user_id)
        return

    delivery = current_delivery.get(user_id, {})

    if not delivery.get("title"):
        await show_delivery(message, user_id)
        return

    customer = DATA["customers"].get(customer_id, {})

    subtotal = cart_total(user_id)
    fee = delivery_fee(delivery)
    total = subtotal + fee

    order_number = DATA["next_order_number"]
    DATA["next_order_number"] += 1

    items = []

    for product_id, quantity in carts.get(user_id, {}).items():
        product = PRODUCTS.get(product_id)

        if not product:
            continue

        items.append({
            "product_id": product_id,
            "name": product["name"],
            "size": product["size"],
            "quantity": quantity,
            "unit_price": product["price"],
            "subtotal": product["price"] * quantity,
        })

    order = {
        "order_number": order_number,
        "user_id": user_id,
        "customer_id": customer_id,
        "date": now_text(),
        "created_at": datetime.now().isoformat(),
        "customer_name": customer.get("name", ""),
        "phone": customer.get("phone", ""),
        "items": items,
        "subtotal": subtotal,
        "delivery_fee": fee,
        "total": total,
        "delivery_place": delivery.get("title", ""),
        "address": delivery.get("address", ""),
        "shipping_method": delivery.get("shipping_method", ""),
        "payment_status": "در انتظار پرداخت",
        "receipt": "",
    }

    DATA["orders"].append(order)
    save_data()

    payment_text = (
        "🎉 سفارش شما ثبت شد.\n\n"
        f"🔢 شماره سفارش: #{order_number}\n"
        f"💳 مبلغ قابل پرداخت: {money(total)}\n\n"
        "لطفاً مبلغ بالا را به شماره کارت زیر واریز کنید:\n\n"
        f"💳 {PAYMENT_CARD}\n"
    )

    if PAYMENT_OWNER:
        payment_text += f"👤 به نام: {PAYMENT_OWNER}\n"

    payment_text += "\n📸 سپس تصویر رسید پرداخت را ارسال کنید."

    user_states[user_id] = {
        "type": "payment_receipt",
        "order_number": order_number,
    }

    carts.pop(user_id, None)
    current_delivery.pop(user_id, None)

    await message.reply(payment_text)

    admin_text = (
        "🆕 سفارش جدید سبزی‌یو\n\n"
        f"🔢 شماره سفارش: #{order_number}\n"
        f"📅 تاریخ: {order['date']}\n"
        f"👤 مشتری: {order['customer_name']}\n"
        f"📱 تلفن: {order['phone']}\n"
        f"📍 تحویل: {order['delivery_place']}\n"
    )

    if order["address"]:
        admin_text += f"🏠 آدرس: {order['address']}\n"

    if order["shipping_method"]:
        admin_text += f"🚚 ارسال: {order['shipping_method']}\n"

    admin_text += (
        f"\n💰 مبلغ نهایی: {money(total)}\n"
        f"🆔 Bale ID: {user_id}"
    )

    for admin_id in ADMIN_CHAT_IDS:
        try:
            await bot.send_message(
                chat_id=int(admin_id),
                text=admin_text,
            )
        except Exception as e:
            logging.error(
                f"ارسال سفارش به مدیر ناموفق بود: {e}"
            )


# =========================================================
# پیام‌ها
# =========================================================

@bot.event
async def on_message(message: Message):
    user_id = str(message.author.user_id)

    print(
        f"USER_ID: {user_id}",
        flush=True,
    )

    state = user_states.get(user_id)

    # -----------------------------------------------------
    # رسید پرداخت
    # -----------------------------------------------------

    if (
        isinstance(state, dict)
        and state.get("type") == "payment_receipt"
    ):
        order_number = state.get("order_number")

        if getattr(message, "photo", None):
            order = None

            for item in DATA["orders"]:
                if str(item["order_number"]) == str(order_number):
                    item["receipt"] = "ارسال شد"
                    item["payment_status"] = "رسید ارسال شد"
                    order = item
                    break

            save_data()

            user_states.pop(user_id, None)

            await message.reply(
                "✅ رسید پرداخت شما دریافت شد.\n\n"
                f"شماره سفارش: #{order_number}\n\n"
                "سفارش شما پس از بررسی پرداخت آماده خواهد شد. 🌿"
            )

            receipt_caption = (
                "📸 رسید پرداخت دریافت شد.\n\n"
                f"🔢 سفارش: #{order_number}\n"
                f"🆔 مشتری: {user_id}"
            )

            if order:
                receipt_caption += (
                    f"\n👤 مشتری: {order.get('customer_name', '')}"
                    f"\n📱 تلفن: {order.get('phone', '')}"
                    f"\n💰 مبلغ: {money(order.get('total', 0))}"
                )

            photo = getattr(message, "photo", None)

            for admin_id in ADMIN_CHAT_IDS:
                try:
                    await bot.send_photo(
                        chat_id=int(admin_id),
                        photo=photo,
                        caption=receipt_caption,
                    )

                except Exception as e:
                    logging.error(
                        f"ارسال عکس رسید به مدیر ناموفق بود: {e}"
                    )

                    try:
                        photo_file_id = getattr(
                            photo,
                            "file_id",
                            None,
                        )

                        if photo_file_id:
                            await bot.send_photo(
                                chat_id=int(admin_id),
                                photo=photo_file_id,
                                caption=receipt_caption,
                            )

                    except Exception as e2:
                        logging.error(
                            f"ارسال مجدد عکس با file_id نیز ناموفق بود: {e2}"
                        )

            return

    # -----------------------------------------------------
    # شماره تلفن
    # -----------------------------------------------------

    if message.contact:
        phone = message.contact.phone_number
        state = user_states.get(user_id)

        if (
            isinstance(state, dict)
            and state.get("type") == "customer_phone"
        ):
            customer_id = state["customer_id"]

        else:
            customer_id = active_customer.get(user_id)

        if not customer_id or customer_id not in DATA["customers"]:
            return

        DATA["customers"][customer_id]["phone"] = phone
        save_data()

        user_states.pop(user_id, None)

        await message.reply(
            "✅ شماره تلفن ثبت شد.\n\n"
            "📍 حالا محل تحویل سفارش را انتخاب کنید."
        )

        await show_delivery(
            message,
            user_id,
        )

        return

    # -----------------------------------------------------
    # متن
    # -----------------------------------------------------

    if not message.content:
        return

    text = message.content.strip()

    # -----------------------------------------------------
    # /start
    # -----------------------------------------------------

    if text == "/start":
        user_states.pop(user_id, None)
        active_customer.pop(user_id, None)
        current_delivery.pop(user_id, None)
        carts.pop(user_id, None)

        await show_home(message)
        return

    state = user_states.get(user_id)

    # -----------------------------------------------------
    # نام مشتری
    # -----------------------------------------------------

    if (
        isinstance(state, dict)
        and state.get("type") == "customer_name"
    ):
        customer_id = state["customer_id"]

        if customer_id not in DATA["customers"]:
            user_states.pop(user_id, None)

            await message.reply(
                "❌ خطا در ثبت مشتری. دوباره تلاش کنید."
            )
            return

        DATA["customers"][customer_id]["name"] = text

        user_states[user_id] = {
            "type": "customer_phone",
            "customer_id": customer_id,
        }

        save_data()

        await message.reply(
            "👤 نام ثبت شد.\n\n"
            "📱 لطفاً شماره تلفن خود را با دکمه زیر ارسال کنید:",
            components=phone_keyboard(),
        )

        return

    # -----------------------------------------------------
    # شماره تلفن متنی
    # -----------------------------------------------------

    if (
        isinstance(state, dict)
        and state.get("type") == "customer_phone"
    ):
        customer_id = state["customer_id"]

        if customer_id not in DATA["customers"]:
            user_states.pop(user_id, None)
            return

        DATA["customers"][customer_id]["phone"] = text
        save_data()

        user_states.pop(user_id, None)

        await message.reply(
            "✅ شماره تلفن ثبت شد.\n\n"
            "📍 حالا محل تحویل سفارش را انتخاب کنید."
        )

        await show_delivery(
            message,
            user_id,
        )

        return

    # -----------------------------------------------------
    # نام آدرس
    # -----------------------------------------------------

    if (
        isinstance(state, dict)
        and state.get("type") == "address_title"
    ):
        customer_id = state["customer_id"]

        if customer_id not in DATA["customers"]:
            user_states.pop(user_id, None)

            await message.reply(
                "❌ مشتری پیدا نشد."
            )
            return

        user_states[user_id] = {
            "type": "address_text",
            "customer_id": customer_id,
            "title": text,
        }

        await message.reply(
            "🏠 حالا آدرس کامل را وارد کنید:"
        )

        return

    # -----------------------------------------------------
    # متن آدرس
    # -----------------------------------------------------

    if (
        isinstance(state, dict)
        and state.get("type") == "address_text"
    ):
        customer_id = state["customer_id"]
        title = state["title"]

        if customer_id not in DATA["customers"]:
            user_states.pop(user_id, None)

            await message.reply(
                "❌ مشتری پیدا نشد."
            )
            return

        DATA["customers"][customer_id].setdefault(
            "addresses",
            [],
        )

        new_address = {
            "title": title,
            "address": text,
        }

        DATA["customers"][customer_id]["addresses"].append(
            new_address
        )

        save_data()

        user_states.pop(user_id, None)
        active_customer[user_id] = customer_id

        # آدرس جدید همان لحظه برای سفارش انتخاب می‌شود.
        current_delivery[user_id] = {
            "title": title,
            "address": text,
            "fee": 0,
        }

        # مستقیماً انتخاب روش ارسال
        await message.reply(
            "✅ آدرس با موفقیت ثبت شد.\n\n"
            f"📍 {title}\n"
            f"🏠 {text}\n\n"
            "🚚 حالا روش ارسال را انتخاب کنید:",
            components=shipping_keyboard(),
        )

        return

    # -----------------------------------------------------
    # اصلاح نام
    # -----------------------------------------------------

    if (
        isinstance(state, dict)
        and state.get("type") == "edit_customer_name"
    ):
        customer_id = state["customer_id"]

        if customer_id not in DATA["customers"]:
            user_states.pop(user_id, None)
            return

        DATA["customers"][customer_id]["name"] = text
        save_data()

        user_states.pop(user_id, None)

        await show_customer_profile(
            message,
            customer_id,
        )

        return

    # -----------------------------------------------------
    # اصلاح تلفن
    # -----------------------------------------------------

    if (
        isinstance(state, dict)
        and state.get("type") == "edit_customer_phone"
    ):
        customer_id = state["customer_id"]

        if customer_id not in DATA["customers"]:
            user_states.pop(user_id, None)
            return

        DATA["customers"][customer_id]["phone"] = text
        save_data()

        user_states.pop(user_id, None)

        await show_customer_profile(
            message,
            customer_id,
        )

        return

    # -----------------------------------------------------
    # اصلاح عنوان آدرس
    # -----------------------------------------------------

    if (
        isinstance(state, dict)
        and state.get("type") == "edit_address_title"
    ):
        customer_id = state["customer_id"]
        index = state["index"]

        customer = DATA["customers"].get(customer_id)

        if not customer:
            user_states.pop(user_id, None)
            return

        addresses = customer.get("addresses", [])

        if index < 0 or index >= len(addresses):
            user_states.pop(user_id, None)
            return

        addresses[index]["title"] = text

        user_states[user_id] = {
            "type": "edit_address_text",
            "customer_id": customer_id,
            "index": index,
        }

        save_data()

        await message.reply(
            "🏠 آدرس کامل جدید را وارد کنید:"
        )

        return

    # -----------------------------------------------------
    # اصلاح متن آدرس
    # -----------------------------------------------------

    if (
        isinstance(state, dict)
        and state.get("type") == "edit_address_text"
    ):
        customer_id = state["customer_id"]
        index = state["index"]

        customer = DATA["customers"].get(customer_id)

        if not customer:
            user_states.pop(user_id, None)
            return

        addresses = customer.get("addresses", [])

        if index < 0 or index >= len(addresses):
            user_states.pop(user_id, None)
            return

        addresses[index]["address"] = text

        save_data()

        user_states.pop(user_id, None)

        await show_addresses(
            message,
            customer_id,
            back_callback=f"addresses_profile_{customer_id}",
        )

        return


# =========================================================
# Callback
# =========================================================

@bot.event
async def on_callback(callback: CallbackQuery):
    user_id = str(callback.from_user.user_id)
    data = callback.data

    # -----------------------------------------------------
    # صفحه اول
    # -----------------------------------------------------

    if data == "home":
        clear_state(user_id)

        await show_home(callback.message)
        return

    # -----------------------------------------------------
    # خریدهای قبلی
    # -----------------------------------------------------

    if data == "previous_orders":
        clear_state(user_id)

        await show_previous_orders(
            callback.message,
            user_id,
        )
        return

    if data.startswith("order_history_"):
        order_number = data[len("order_history_"):]

        await show_order_history(
            callback.message,
            user_id,
            order_number,
        )
        return

    # -----------------------------------------------------
    # فروشگاه
    # -----------------------------------------------------

    if data == "shop":
        clear_state(user_id)

        await show_shop(callback.message)
        return

    # -----------------------------------------------------
    # دسته‌بندی
    # -----------------------------------------------------

    if data.startswith("category_"):
        category = data[len("category_"):]

        await show_category(
            callback.message,
            category,
        )
        return

    # -----------------------------------------------------
    # محصول
    # -----------------------------------------------------

    if data.startswith("product_"):
        product_id = data[len("product_"):]
        product = PRODUCTS.get(product_id)

        if not product:
            return

        category = product.get("category", "")

        await callback.message.reply(
            f"🌿 {product['name']}\n\n"
            f"📦 {product['size']}\n"
            f"💰 {money(product['price'])}",
            components=product_keyboard(
                product_id,
                category,
            ),
        )
        return

    # -----------------------------------------------------
    # افزودن
    # -----------------------------------------------------

    if data.startswith("add_"):
        product_id = data[len("add_"):]

        product = PRODUCTS.get(product_id)

        if not product:
            return

        if product.get("active", True) is False:
            await callback.message.reply(
                "❌ این محصول در حال حاضر موجود نیست."
            )
            return

        carts.setdefault(user_id, {})

        carts[user_id][product_id] = (
            carts[user_id].get(product_id, 0) + 1
        )

        await show_cart(
            callback.message,
            user_id,
        )
        return

    # -----------------------------------------------------
    # افزایش
    # -----------------------------------------------------

    if data.startswith("plus_"):
        product_id = data[len("plus_"):]

        product = PRODUCTS.get(product_id)

        if not product:
            return

        carts.setdefault(user_id, {})

        carts[user_id][product_id] = (
            carts[user_id].get(product_id, 0) + 1
        )

        await show_cart(
            callback.message,
            user_id,
        )
        return

    # -----------------------------------------------------
    # کاهش
    # -----------------------------------------------------

    if data.startswith("minus_"):
        product_id = data[len("minus_"):]

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
    # شروع سفارش
    # -----------------------------------------------------

    if data == "start_order":
        await start_order(
            callback.message,
            user_id,
        )
        return

    # -----------------------------------------------------
    # مشتری جدید
    # -----------------------------------------------------

    if data == "new_customer":
        await start_new_customer(
            callback.message,
            user_id,
        )
        return

    # -----------------------------------------------------
    # مشتری قدیمی
    # -----------------------------------------------------

    if data == "old_customer":
        await show_customer_list(
            callback.message,
            user_id,
        )
        return

    if data == "customer_start":
        await show_customer_start(
            callback.message,
            user_id,
        )
        return

    # -----------------------------------------------------
    # انتخاب مشتری
    # -----------------------------------------------------

    if data.startswith("select_customer_"):
        customer_id = data[len("select_customer_"):]

        if customer_id not in DATA["customers"]:
            return

        await show_customer_profile(
            callback.message,
            customer_id,
        )
        return

    # -----------------------------------------------------
    # استفاده از مشتری
    # -----------------------------------------------------

    if data.startswith("use_customer_"):
        customer_id = data[len("use_customer_"):]

        if customer_id not in DATA["customers"]:
            return

        active_customer[user_id] = customer_id

        # تحویل قبلی مربوط به مشتری قبلی نباید باقی بماند.
        current_delivery.pop(user_id, None)

        await show_delivery(
            callback.message,
            user_id,
        )
        return

    # -----------------------------------------------------
    # پروفایل
    # -----------------------------------------------------

    if data.startswith("profile_"):
        customer_id = data[len("profile_"):]

        if customer_id not in DATA["customers"]:
            return

        await show_customer_profile(
            callback.message,
            customer_id,
        )
        return

    # -----------------------------------------------------
    # اصلاح مشتری
    # -----------------------------------------------------

    if data.startswith("edit_customer_"):
        customer_id = data[len("edit_customer_"):]

        if customer_id not in DATA["customers"]:
            return

        keyboard = InlineKeyboardMarkup()

        keyboard.add(
            InlineKeyboardButton(
                text="👤 اصلاح نام",
                callback_data=f"edit_name_{customer_id}",
            ),
            row=1,
        )

        keyboard.add(
            InlineKeyboardButton(
                text="📱 اصلاح شماره",
                callback_data=f"edit_phone_{customer_id}",
            ),
            row=2,
        )

        keyboard.add(
            InlineKeyboardButton(
                text="⬅️ بازگشت",
                callback_data=f"profile_{customer_id}",
            ),
            row=3,
        )

        await callback.message.reply(
            "✏️ اصلاح مشخصات",
            components=keyboard,
        )
        return

    if data.startswith("edit_name_"):
        customer_id = data[len("edit_name_"):]

        if customer_id not in DATA["customers"]:
            return

        user_states[user_id] = {
            "type": "edit_customer_name",
            "customer_id": customer_id,
        }

        await callback.message.reply(
            "👤 نام و نام خانوادگی جدید را وارد کنید:"
        )
        return

    if data.startswith("edit_phone_"):
        customer_id = data[len("edit_phone_"):]

        if customer_id not in DATA["customers"]:
            return

        user_states[user_id] = {
            "type": "edit_customer_phone",
            "customer_id": customer_id,
        }

        await callback.message.reply(
            "📱 شماره تلفن جدید را وارد کنید:"
        )
        return

    # -----------------------------------------------------
    # حذف مشتری
    # -----------------------------------------------------

    if data.startswith("delete_customer_"):
        customer_id = data[len("delete_customer_"):]

        DATA["customers"].pop(
            customer_id,
            None,
        )

        if active_customer.get(user_id) == customer_id:
            active_customer.pop(user_id, None)

        current_delivery.pop(user_id, None)
        save_data()

        await show_customer_list(
            callback.message,
            user_id,
        )
        return

    # -----------------------------------------------------
    # آدرس‌ها از پروفایل
    # -----------------------------------------------------

    if data.startswith("addresses_profile_"):
        customer_id = data[len("addresses_profile_"):]

        if customer_id not in DATA["customers"]:
            return

        await show_addresses(
            callback.message,
            customer_id,
            back_callback=f"profile_{customer_id}",
        )
        return

    # -----------------------------------------------------
    # آدرس‌ها از مسیر سفارش
    # -----------------------------------------------------

    if data == "addresses_order":
        customer_id = active_customer.get(user_id)

        if not customer_id:
            await show_customer_start(
                callback.message,
                user_id,
            )
            return

        await show_addresses(
            callback.message,
            customer_id,
            back_callback="delivery",
        )
        return

    if data.startswith("addresses_order_"):
        customer_id = data[len("addresses_order_"):]

        if customer_id not in DATA["customers"]:
            return

        await show_addresses(
            callback.message,
            customer_id,
            back_callback="delivery",
        )
        return

    # -----------------------------------------------------
    # افزودن آدرس
    # -----------------------------------------------------

    if data.startswith("add_address_"):
        customer_id = data[len("add_address_"):]

        if customer_id not in DATA["customers"]:
            return

        await start_new_address(
            callback.message,
            user_id,
            customer_id,
        )
        return

    # -----------------------------------------------------
    # انتخاب آدرس برای مشاهده / مدیریت
    # -----------------------------------------------------

    if data.startswith("select_address_"):
        payload = data[len("select_address_"):]

        try:
            customer_id, index_text = payload.rsplit("_", 1)
            index = int(index_text)
        except (ValueError, TypeError):
            return

        customer = DATA["customers"].get(customer_id)

        if not customer:
            return

        addresses = customer.get("addresses", [])

        if index < 0 or index >= len(addresses):
            return

        address = addresses[index]

        # تشخیص مسیر برگشت بر اساس state/session
        if current_delivery.get(user_id):
            back_callback = "delivery"
        else:
            back_callback = f"addresses_profile_{customer_id}"

        await callback.message.reply(
            f"📍 {address.get('title', 'آدرس')}\n\n"
            f"🏠 {address.get('address', '')}",
            components=address_management_keyboard(
                customer_id,
                index,
                back_callback,
            ),
        )
        return

    # -----------------------------------------------------
    # انتخاب آدرس برای سفارش
    # -----------------------------------------------------

    if data.startswith("use_address_"):
        payload = data[len("use_address_"):]

        try:
            customer_id, index_text = payload.rsplit("_", 1)
            index = int(index_text)
        except (ValueError, TypeError):
            return

        customer = DATA["customers"].get(customer_id)

        if not customer:
            return

        addresses = customer.get("addresses", [])

        if index < 0 or index >= len(addresses):
            return

        address = addresses[index]

        active_customer[user_id] = customer_id

        current_delivery[user_id] = {
            "title": address.get("title", "آدرس"),
            "address": address.get("address", ""),
            "fee": 0,
        }

        # انتخاب آدرس = پایان مرحله آدرس
        # و ورود مستقیم به مرحله روش ارسال
        await callback.message.reply(
            "✅ این آدرس برای سفارش انتخاب شد.\n\n"
            f"📍 {address.get('title', 'آدرس')}\n"
            f"🏠 {address.get('address', '')}\n\n"
            "🚚 حالا روش ارسال را انتخاب کنید:",
            components=shipping_keyboard(),
        )
        return

    # -----------------------------------------------------
    # اصلاح آدرس
    # -----------------------------------------------------

    if data.startswith("edit_address_"):
        payload = data[len("edit_address_"):]

        try:
            customer_id, index_text = payload.rsplit("_", 1)
            index = int(index_text)
        except (ValueError, TypeError):
            return

        customer = DATA["customers"].get(customer_id)

        if not customer:
            return

        addresses = customer.get("addresses", [])

        if index < 0 or index >= len(addresses):
            return

        user_states[user_id] = {
            "type": "edit_address_title",
            "customer_id": customer_id,
            "index": index,
        }

        await callback.message.reply(
            "✏️ نام این آدرس را وارد کنید:"
        )
        return

    # -----------------------------------------------------
    # حذف آدرس
    # -----------------------------------------------------

    if data.startswith("delete_address_"):
        payload = data[len("delete_address_"):]

        try:
            customer_id, index_text = payload.rsplit("_", 1)
            index = int(index_text)
        except (ValueError, TypeError):
            return

        customer = DATA["customers"].get(customer_id)

        if not customer:
            return

        addresses = customer.get("addresses", [])

        if index < 0 or index >= len(addresses):
            return

        del addresses[index]

        # اگر آدرس حذف‌شده همان آدرس فعال بود،
        # تحویل فعلی هم پاک شود.
        if (
            active_customer.get(user_id) == customer_id
            and current_delivery.get(user_id, {}).get("address")
        ):
            current_delivery.pop(user_id, None)

        save_data()

        await show_addresses(
            callback.message,
            customer_id,
            back_callback=f"profile_{customer_id}",
        )
        return

    # -----------------------------------------------------
    # تحویل
    # -----------------------------------------------------

    if data == "delivery":
        await show_delivery(
            callback.message,
            user_id,
        )
        return

    # -----------------------------------------------------
    # تحویل رایگان
    # -----------------------------------------------------

    if data == "free_delivery":
        await callback.message.reply(
            "📍 تحویل رایگان / حضوری را انتخاب کنید:",
            components=free_delivery_keyboard(),
        )
        return

    # -----------------------------------------------------
    # تحویل حضوری
    # -----------------------------------------------------

    if data == "delivery_pickup":
        current_delivery[user_id] = {
            "title": "تحویل حضوری",
            "address": "",
            "fee": 0,
            "shipping_method": "",
        }

        await show_final_invoice(
            callback.message,
            user_id,
        )
        return

    # -----------------------------------------------------
    # تحویل هیأت
    # -----------------------------------------------------

    if data == "delivery_heyat":
        current_delivery[user_id] = {
            "title": "تحویل در هیأت امنا",
            "address": "",
            "fee": 0,
            "shipping_method": "",
        }

        await show_final_invoice(
            callback.message,
            user_id,
        )
        return

    # -----------------------------------------------------
    # آدرس‌های ذخیره‌شده
    # -----------------------------------------------------

    if data == "delivery_saved":
        customer_id = active_customer.get(user_id)

        if not customer_id:
            await show_customer_start(
                callback.message,
                user_id,
            )
            return

        customer = DATA["customers"].get(customer_id, {})
        addresses = customer.get("addresses", [])

        if not addresses:
            keyboard = InlineKeyboardMarkup()

            keyboard.add(
                InlineKeyboardButton(
                    text="➕ افزودن آدرس",
                    callback_data=f"add_address_{customer_id}",
                ),
                row=1,
            )

            keyboard.add(
                InlineKeyboardButton(
                    text="⬅️ بازگشت",
                    callback_data="delivery",
                ),
                row=2,
            )

            await callback.message.reply(
                "📍 آدرس‌های من\n\n"
                "هنوز آدرسی برای شما ثبت نشده است.",
                components=keyboard,
            )
            return

        await show_addresses(
            callback.message,
            customer_id,
            back_callback="delivery",
        )
        return

    # -----------------------------------------------------
    # افزودن آدرس جدید از سفارش
    # -----------------------------------------------------

    if data == "delivery_new_address":
        customer_id = active_customer.get(user_id)

        if not customer_id:
            await show_customer_start(
                callback.message,
                user_id,
            )
            return

        await start_new_address(
            callback.message,
            user_id,
            customer_id,
        )
        return

    # -----------------------------------------------------
    # ارسال الوپیک
    # -----------------------------------------------------

    if data == "shipping_alopik":
        delivery = current_delivery.setdefault(
            user_id,
            {},
        )

        delivery["shipping_method"] = "الوپیک"

        # فعلاً مبلغ ارسال صفر است
        delivery["fee"] = 0

        await show_final_invoice(
            callback.message,
            user_id,
        )
        return

    # -----------------------------------------------------
    # ارسال اسنپ‌باکس
    # -----------------------------------------------------

    if data == "shipping_snapp":
        delivery = current_delivery.setdefault(
            user_id,
            {},
        )

        delivery["shipping_method"] = "اسنپ‌باکس"

        # فعلاً مبلغ ارسال صفر است
        delivery["fee"] = 0

        await show_final_invoice(
            callback.message,
            user_id,
        )
        return

    # -----------------------------------------------------
    # اصلاح سبد
    # -----------------------------------------------------

    if data == "edit_cart":
        await show_cart(
            callback.message,
            user_id,
        )
        return

    # -----------------------------------------------------
    # پرداخت
    # -----------------------------------------------------

    if data == "payment":
        await create_order(
            callback.message,
            user_id,
        )
        return

    # -----------------------------------------------------
    # لغو خرید
    # -----------------------------------------------------

    if data == "cancel_cart":
        carts.pop(user_id, None)
        current_delivery.pop(user_id, None)
        user_states.pop(user_id, None)

        await show_home(callback.message)
        return


# =========================================================
# اجرا
# =========================================================

@bot.event
async def on_ready():
    print(
        "=== BALE BOT CONNECTED ===",
        flush=True,
    )

    print(
        "SabziU Bale Store is ready!",
        flush=True,
    )


bot.run()
