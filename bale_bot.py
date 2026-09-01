import os
import json
import logging
from datetime import datetime

from bale import (
    Bot,
    Message,
    CallbackQuery,
    InputFile,
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
        logging.error(f"خطا در خواندن داده‌ها: {e}")
        return default


DATA = load_data()

user_states = {}
active_customer = {}
carts = {}
current_delivery = {}

# آخرین پیام صفحه‌ای ربات برای هر کاربر
last_bot_message = {}


# =========================================================
# ذخیره اطلاعات
# =========================================================

def save_data():
    temp = STATE_FILE + ".tmp"

    try:
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(
                DATA,
                f,
                ensure_ascii=False,
                indent=2,
            )

        os.replace(temp, STATE_FILE)

    except Exception as e:
        logging.error(f"خطا در ذخیره اطلاعات: {e}")


# =========================================================
# مدیریت صفحه‌های ربات
# =========================================================

async def delete_last_bot_message(user_id):
    old_message = last_bot_message.get(user_id)

    if not old_message:
        return

    try:
        await old_message.delete()
    except Exception as e:
        logging.debug(
            f"حذف پیام قبلی ناموفق بود: {e}"
        )

    last_bot_message.pop(user_id, None)


async def send_screen(
    message,
    text,
    components=None,
    user_id=None,
):
    """
    هر صفحه فقط یک پیام فعال از ربات دارد.
    پیام‌های کاربر هرگز حذف نمی‌شوند.
    """

    if user_id is None:
        user_id = str(message.author.user_id)

    await delete_last_bot_message(user_id)

    try:
        new_message = await bot.send_message(
            chat_id=int(user_id),
            text=text,
            components=components,
        )

        last_bot_message[user_id] = new_message

        return new_message

    except Exception as e:
        logging.exception(
            f"ارسال صفحه ناموفق بود: {e}"
        )

        return None


async def send_screen_callback(
    callback,
    text,
    components=None,
):
    """
    نمایش صفحه جدید بعد از کلیک روی دکمه.
    """

    user_id = str(
        callback.from_user.user_id
    )

    callback_message = callback.message
    old_message = last_bot_message.get(user_id)

    # اگر پیام فعلی همان پیام callback است،
    # فقط از حافظه حذفش می‌کنیم.
    if old_message is callback_message:

        last_bot_message.pop(
            user_id,
            None,
        )

    elif old_message:

        try:
            await old_message.delete()

        except Exception as e:
            logging.debug(
                f"حذف پیام قبلی ناموفق بود: {e}"
            )

        last_bot_message.pop(
            user_id,
            None,
        )

    try:
        if hasattr(callback, "answer"):
            await callback.answer()

    except Exception:
        pass

    try:
        new_message = await bot.send_message(
            chat_id=int(user_id),
            text=text,
            components=components,
        )

        last_bot_message[user_id] = new_message

        return new_message

    except Exception as e:
        logging.exception(
            f"ارسال صفحه callback ناموفق بود: {e}"
        )

        return None


# =========================================================
# ابزارها
# =========================================================

def now_text():
    return datetime.now().strftime(
        "%Y/%m/%d - %H:%M"
    )


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

    for product_id, quantity in carts.get(
        user_id,
        {},
    ).items():

        product = PRODUCTS.get(product_id)

        if product:
            total += (
                product["price"] * quantity
            )

    return total


def delivery_fee(delivery):
    return int(
        delivery.get("fee", 0)
    )


def find_order(user_id, order_number):
    for order in DATA["orders"]:

        if (
            str(order.get("user_id"))
            == str(user_id)
            and str(order.get("order_number"))
            == str(order_number)
        ):
            return order

    return None


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
# صفحه اصلی
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


async def show_home(
    message,
    user_id=None,
):

    if user_id is None:
        user_id = str(
            message.author.user_id
        )

    await send_screen(
        message,
        "سلام 👋\n\n"
        "به فروشگاه سبزی‌یو خوش آمدید 🌿\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        components=home_keyboard(),
        user_id=user_id,
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
        if str(order.get("user_id"))
        == str(user_id)
    ]

    orders.sort(
        key=lambda x: x.get(
            "created_at",
            "",
        ),
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
                callback_data=(
                    f"order_history_"
                    f"{order['order_number']}"
                ),
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


async def show_previous_orders(
    message,
    user_id,
):

    orders = [
        order
        for order in DATA["orders"]
        if str(order.get("user_id"))
        == str(user_id)
    ]

    if not orders:

        text = (
            "🧾 خریدهای قبلی\n\n"
            "هنوز سفارشی برای شما ثبت نشده است."
        )

    else:

        text = (
            "🧾 خریدهای قبلی\n\n"
            "سفارش‌های شما:"
        )

    await send_screen(
        message,
        text,
        components=previous_orders_keyboard(
            user_id
        ),
        user_id=user_id,
    )


async def show_order_history(
    message,
    user_id,
    order_number,
):

    order = find_order(
        user_id,
        order_number,
    )

    if not order:

        await send_screen(
            message,
            "❌ سفارش پیدا نشد.",
            components=back_keyboard(
                "previous_orders"
            ),
            user_id=user_id,
        )

        return

    lines = []

    for item in order.get(
        "items",
        [],
    ):

        lines.append(
            f"• {item['name']}\n"
            f"  {item['size']} × "
            f"{item['quantity']}\n"
            f"  {money(item['subtotal'])}"
        )

    text = (
        "🧾 جزئیات سفارش\n\n"
        f"🔢 شماره سفارش: "
        f"#{order['order_number']}\n"
        f"📅 تاریخ خرید: "
        f"{order['date']}\n\n"
        "🛍 ریز سفارش:\n"
        + "\n".join(lines)
        + "\n\n"
        f"💰 مبلغ کالاها: "
        f"{money(order['subtotal'])}\n"
        f"🚚 هزینه ارسال: "
        f"{money(order['delivery_fee'])}\n"
        f"💳 مبلغ نهایی: "
        f"{money(order['total'])}\n\n"
        f"📍 محل تحویل: "
        f"{order.get('delivery_place', '')}\n"
    )

    if order.get("address"):

        text += (
            f"🏠 آدرس: "
            f"{order['address']}\n"
        )

    if order.get("shipping_method"):

        text += (
            f"🚚 روش ارسال: "
            f"{order['shipping_method']}\n"
        )

    await send_screen(
        message,
        text,
        components=back_keyboard(
            "previous_orders"
        ),
        user_id=user_id,
    )


# =========================================================
# فروشگاه
# =========================================================

def categories_keyboard():
    keyboard = InlineKeyboardMarkup()

    categories = []

    for product in PRODUCTS.values():

        category = product.get(
            "category"
        )

        if (
            category
            and category not in categories
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
                callback_data=(
                    f"category_{category}"
                ),
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


async def show_shop(
    message,
    user_id=None,
):

    if user_id is None:
        user_id = str(
            message.author.user_id
        )

    await send_screen(
        message,
        "🛒 فروشگاه سبزی‌یو\n\n"
        "دسته‌بندی کالاها را انتخاب کنید:",
        components=categories_keyboard(),
        user_id=user_id,
    )


def category_keyboard(category):
    keyboard = InlineKeyboardMarkup()

    row = 1

    for product_id, product in PRODUCTS.items():

        if product.get("category") != category:
            continue

        if product.get(
            "active",
            True,
        ) is False:
            continue

        keyboard.add(
            InlineKeyboardButton(
                text=(
                    f"{product['name']} | "
                    f"{product['size']}"
                ),
                callback_data=(
                    f"product_{product_id}"
                ),
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


def product_keyboard(product_id):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="➕ افزودن به سبد",
            callback_data=(
                f"add_{product_id}"
            ),
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="shop",
        ),
        row=2,
    )

    return keyboard


# =========================================================
# سبد خرید
# =========================================================

def cart_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()

    row = 1

    for product_id, quantity in carts.get(
        user_id,
        {},
    ).items():

        product = PRODUCTS.get(
            product_id
        )

        if not product:
            continue

        keyboard.add(
            InlineKeyboardButton(
                text=(
                    f"➕ {product['name']} "
                    f"({quantity})"
                ),
                callback_data=(
                    f"plus_{product_id}"
                ),
            ),
            row=row,
        )

        row += 1

        keyboard.add(
            InlineKeyboardButton(
                text=(
                    f"➖ {product['name']}"
                ),
                callback_data=(
                    f"minus_{product_id}"
                ),
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


async def show_cart(
    message,
    user_id,
):

    cart = carts.get(
        user_id,
        {},
    )

    if not cart:

        await send_screen(
            message,
            "🧺 سبد خرید شما خالی است.",
            components=back_keyboard(
                "shop"
            ),
            user_id=user_id,
        )

        return

    lines = [
        "🧾 فاکتور خرید تا این لحظه\n"
    ]

    subtotal = 0

    for product_id, quantity in cart.items():

        product = PRODUCTS.get(
            product_id
        )

        if not product:
            continue

        item_total = (
            product["price"] * quantity
        )

        subtotal += item_total

        lines.append(
            f"• {product['name']}\n"
            f"  {product['size']} × "
            f"{quantity}\n"
            f"  {money(item_total)}\n"
        )

    lines.append(
        f"💰 مبلغ کالاها: "
        f"{money(subtotal)}"
    )

    await send_screen(
        message,
        "\n".join(lines),
        components=cart_keyboard(
            user_id
        ),
        user_id=user_id,
    )


# =========================================================
# مشتری
# =========================================================

def customer_start_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()

    customers = get_user_customers(
        user_id
    )

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


async def show_customer_start(
    message,
    user_id,
):

    customers = get_user_customers(
        user_id
    )

    if customers:

        text = (
            "👤 مشخصات مشتری\n\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:"
        )

    else:

        text = (
            "👤 ثبت مشخصات مشتری\n\n"
            "برای ادامه سفارش ابتدا مشخصات "
            "خود را ثبت کنید:"
        )

    await send_screen(
        message,
        text,
        components=customer_start_keyboard(
            user_id
        ),
        user_id=user_id,
    )


def customer_list_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()

    row = 1

    for customer_id, customer in get_user_customers(
        user_id
    ):

        keyboard.add(
            InlineKeyboardButton(
                text=(
                    f"👤 "
                    f"{customer.get('name', 'بدون نام')}"
                ),
                callback_data=(
                    f"select_customer_"
                    f"{customer_id}"
                ),
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


async def show_customer_list(
    message,
    user_id,
):

    await send_screen(
        message,
        "👤 مشتریان ثبت‌شده\n\n"
        "مشتری موردنظر را انتخاب کنید:",
        components=customer_list_keyboard(
            user_id
        ),
        user_id=user_id,
    )


def customer_profile_keyboard(customer_id):

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text="🛒 انتخاب این مشتری",
            callback_data=(
                f"use_customer_{customer_id}"
            ),
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="✏️ اصلاح مشخصات",
            callback_data=(
                f"edit_customer_{customer_id}"
            ),
        ),
        row=2,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🗑 حذف مشتری",
            callback_data=(
                f"delete_customer_{customer_id}"
            ),
        ),
        row=3,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="📍 مدیریت آدرس‌ها",
            callback_data=(
                f"addresses_profile_{customer_id}"
            ),
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


async def show_customer_profile(
    message,
    customer_id,
    user_id=None,
):

    customer = DATA["customers"].get(
        customer_id
    )

    if not customer:
        return

    if user_id is None:
        user_id = str(
            message.author.user_id
        )

    await send_screen(
        message,
        f"👤 نام: "
        f"{customer.get('name', '')}\n"
        f"📱 تلفن: "
        f"{customer.get('phone', '')}\n\n"
        "عملیات موردنظر:",
        components=customer_profile_keyboard(
            customer_id
        ),
        user_id=user_id,
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

def address_list_keyboard(
    customer_id,
    back_callback=None,
):

    keyboard = InlineKeyboardMarkup()

    customer = DATA["customers"].get(
        customer_id,
        {},
    )

    addresses = customer.get(
        "addresses",
        [],
    )

    row = 1

    for index, address in enumerate(
        addresses
    ):

        keyboard.add(
            InlineKeyboardButton(
                text=(
                    f"📍 "
                    f"{address.get('title', 'آدرس')}"
                ),
                callback_data=(
                    f"select_address_"
                    f"{customer_id}_{index}"
                ),
            ),
            row=row,
        )

        row += 1

    keyboard.add(
        InlineKeyboardButton(
            text="➕ افزودن آدرس",
            callback_data=(
                f"add_address_{customer_id}"
            ),
        ),
        row=row,
    )

    row += 1

    if back_callback is None:
        back_callback = (
            f"profile_{customer_id}"
        )

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
    user_id=None,
):

    customer = DATA["customers"].get(
        customer_id,
        {},
    )

    if not customer:

        await send_screen(
            message,
            "❌ مشتری پیدا نشد.",
            user_id=user_id,
        )

        return

    if user_id is None:
        user_id = str(
            message.author.user_id
        )

    addresses = customer.get(
        "addresses",
        [],
    )

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

    await send_screen(
        message,
        text,
        components=address_list_keyboard(
            customer_id,
            back_callback,
        ),
        user_id=user_id,
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
            callback_data=(
                f"use_address_"
                f"{customer_id}_{index}"
            ),
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="✏️ اصلاح آدرس",
            callback_data=(
                f"edit_address_"
                f"{customer_id}_{index}"
            ),
        ),
        row=2,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="🗑 حذف آدرس",
            callback_data=(
                f"delete_address_"
                f"{customer_id}_{index}"
            ),
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

async def start_new_customer(
    message,
    user_id,
):

    customers = get_user_customers(
        user_id
    )

    number = len(customers) + 1

    while (
        f"{user_id}_customer_{number}"
        in DATA["customers"]
    ):
        number += 1

    customer_id = (
        f"{user_id}_customer_{number}"
    )

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

    await send_screen(
        message,
        "👤 ثبت مشخصات مشتری\n\n"
        "لطفاً نام و نام خانوادگی را وارد کنید:",
        user_id=user_id,
    )


async def start_new_address(
    message,
    user_id,
    customer_id,
):

    if customer_id not in DATA["customers"]:

        await send_screen(
            message,
            "❌ مشتری پیدا نشد.",
            user_id=user_id,
        )

        return

    active_customer[user_id] = customer_id

    user_states[user_id] = {
        "type": "address_title",
        "customer_id": customer_id,
    }

    await send_screen(
        message,
        "➕ افزودن آدرس جدید\n\n"
        "یک نام برای آدرس وارد کنید.\n"
        "مثلاً: خانه، محل کار، فروشگاه",
        user_id=user_id,
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


async def show_delivery(
    message,
    user_id,
):

    await send_screen(
        message,
        "📍 محل تحویل سفارش\n\n"
        "روش تحویل را انتخاب کنید:",
        components=delivery_keyboard(),
        user_id=user_id,
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
            text="➕ ادامه خرید",
            callback_data="shop",
        ),
        row=3,
    )

    keyboard.add(
        InlineKeyboardButton(
            text="❌ لغو خرید",
            callback_data="cancel_cart",
        ),
        row=4,
    )

    return keyboard


async def show_final_invoice(
    message,
    user_id,
):

    delivery = current_delivery.get(
        user_id,
        {},
    )

    customer_id = active_customer.get(
        user_id
    )

    customer = DATA["customers"].get(
        customer_id,
        {},
    )

    subtotal = cart_total(user_id)
    fee = delivery_fee(delivery)
    total = subtotal + fee

    lines = []

    for product_id, quantity in carts.get(
        user_id,
        {},
    ).items():

        product = PRODUCTS.get(
            product_id
        )

        if not product:
            continue

        item_total = (
            product["price"] * quantity
        )

        lines.append(
            f"• {product['name']}\n"
            f"  {product['size']} × "
            f"{quantity}\n"
            f"  {money(item_total)}"
        )

    text = (
        "🧾 فاکتور خرید\n\n"
        f"👤 نام: "
        f"{customer.get('name', '')}\n"
        f"📱 تلفن: "
        f"{customer.get('phone', '')}\n\n"
        "🛍 محصولات:\n"
        + "\n".join(lines)
        + "\n\n"
        f"💰 مبلغ کالاها: "
        f"{money(subtotal)}\n"
        f"🚚 هزینه ارسال: "
        f"{money(fee)}\n"
        f"💳 مبلغ نهایی: "
        f"{money(total)}\n\n"
        f"📍 محل تحویل: "
        f"{delivery.get('title', '')}\n"
    )

    if delivery.get("address"):

        text += (
            f"🏠 آدرس: "
            f"{delivery['address']}\n"
        )

    if delivery.get("shipping_method"):

        text += (
            f"🚚 روش ارسال: "
            f"{delivery['shipping_method']}\n"
        )

    await send_screen(
        message,
        text,
        components=final_invoice_keyboard(),
        user_id=user_id,
    )


# =========================================================
# شروع سفارش
# =========================================================

async def start_order(
    message,
    user_id,
):

    if not carts.get(user_id):

        await send_screen(
            message,
            "🧺 سبد خرید شما خالی است.",
            components=back_keyboard(
                "shop"
            ),
            user_id=user_id,
        )

        return

    customer_id = active_customer.get(
        user_id
    )

    if (
        customer_id
        and customer_id in DATA["customers"]
    ):

        await show_customer_profile(
            message,
            customer_id,
            user_id,
        )

        return

    await show_customer_start(
        message,
        user_id,
    )


# =========================================================
# پیدا کردن عکس در پیام
# =========================================================

def get_message_photos(message):
    """
    در نسخه‌های مختلف کتابخانه ممکن است
    عکس با نام photos یا photo در Message
    در دسترس باشد.

    این تابع هر دو حالت را بررسی می‌کند.
    """

    photos = getattr(
        message,
        "photos",
        None,
    )

    if photos:
        return photos

    photo = getattr(
        message,
        "photo",
        None,
    )

    if photo:

        if isinstance(photo, (list, tuple)):
            return photo

        return [photo]

    return []


def get_photo_file_id(photo):
    """
    پیدا کردن file_id از شیء عکس.
    """

    file_id = getattr(
        photo,
        "file_id",
        None,
    )

    if file_id:
        return file_id

    # بعضی نسخه‌ها ممکن است file_id
    # داخل object دیگری داشته باشند.
    if isinstance(photo, dict):

        file_id = photo.get(
            "file_id"
        )

        if file_id:
            return file_id

    return None


# =========================================================
# ارسال رسید به مدیر
# =========================================================

async def send_receipt_to_admin(
    message,
    order_number,
    user_id,
    order,
):
    """
    دریافت رسید پرداخت از کاربر و ارسال مستقیم همان
    فایل به مدیران.

    سازگار با python-bale-bot 2.5.0
    """

    try:
        photos = getattr(
            message,
            "photos",
            None,
        )

        if not photos:
            logging.error(
                f"❌ رسید سفارش #{order_number}: "
                "message.photos خالی است."
            )
            return False

        if not ADMIN_CHAT_IDS:
            logging.error(
                "❌ BALE_ADMIN_CHAT_IDS تنظیم نشده است."
            )
            return False

        # -------------------------------------------------
        # بزرگ‌ترین/بهترین نسخه عکس
        # -------------------------------------------------

        photo = photos[-1]

        logging.info(
            f"📸 رسید سفارش #{order_number} دریافت شد."
        )

        logging.info(
            f"📸 file_id={getattr(photo, 'file_id', None)}"
        )

        logging.info(
            f"📸 file_size={getattr(photo, 'file_size', None)}"
        )

        # -------------------------------------------------
        # تبدیل PhotoSize به InputFile
        # -------------------------------------------------

        try:
            input_file = photo.to_input_file()

        except Exception as e:
            logging.exception(
                f"❌ تبدیل عکس رسید سفارش "
                f"#{order_number} به InputFile ناموفق بود: {e}"
            )
            return False

        # -------------------------------------------------
        # متن رسید برای مدیر
        # -------------------------------------------------

        caption = (
            "📸 رسید پرداخت دریافت شد.\n\n"
            f"🔢 سفارش: #{order_number}\n"
            f"🆔 Bale ID: {user_id}"
        )

        if order:
            caption += (
                f"\n👤 مشتری: "
                f"{order.get('customer_name', '')}"
                f"\n📱 تلفن: "
                f"{order.get('phone', '')}"
                f"\n💰 مبلغ: "
                f"{money(order.get('total', 0))}"
            )

        # -------------------------------------------------
        # ارسال برای تمام مدیران
        # -------------------------------------------------

        success_count = 0

        for admin_id in ADMIN_CHAT_IDS:

            try:

                logging.info(
                    f"📤 در حال ارسال رسید سفارش "
                    f"#{order_number} به مدیر {admin_id}..."
                )

                sent_message = await bot.send_photo(
                    chat_id=int(admin_id),
                    photo=input_file,
                    caption=caption,
                )

                # -------------------------------------------------
                # بررسی نتیجه واقعی API
                # -------------------------------------------------

                if sent_message:

                    success_count += 1

                    logging.info(
                        f"✅ رسید سفارش #{order_number} "
                        f"به مدیر {admin_id} ارسال شد."
                    )

                    logging.info(
                        f"✅ پیام برگشتی از Bale: "
                        f"{sent_message}"
                    )

                else:

                    logging.error(
                        f"❌ Bale برای رسید سفارش "
                        f"#{order_number} پیام برگشتی نداد."
                    )

            except Exception as e:

                logging.exception(
                    f"❌ ارسال رسید سفارش "
                    f"#{order_number} به مدیر "
                    f"{admin_id} ناموفق بود: {e}"
                )

        # -------------------------------------------------
        # نتیجه نهایی
        # -------------------------------------------------

        if success_count > 0:

            logging.info(
                f"🎉 رسید سفارش #{order_number} "
                f"با موفقیت برای "
                f"{success_count} مدیر ارسال شد."
            )

            return True

        logging.error(
            f"❌ هیچ مدیری رسید سفارش "
            f"#{order_number} را دریافت نکرد."
        )

        return False

    except Exception as e:

        logging.exception(
            f"❌ خطای کلی در ارسال رسید "
            f"#{order_number}: {e}"
        )

        return False


# =========================================================
# ثبت سفارش
# =========================================================

async def create_order(
    message,
    user_id,
):

    customer_id = active_customer.get(
        user_id
    )

    if (
        not customer_id
        or customer_id not in DATA["customers"]
    ):

        await show_customer_start(
            message,
            user_id,
        )

        return

    delivery = current_delivery.get(
        user_id,
        {},
    )

    if not delivery.get("title"):

        await show_delivery(
            message,
            user_id,
        )

        return

    customer = DATA["customers"].get(
        customer_id,
        {},
    )

    subtotal = cart_total(user_id)
    fee = delivery_fee(delivery)
    total = subtotal + fee

    order_number = DATA[
        "next_order_number"
    ]

    DATA["next_order_number"] += 1

    items = []

    for product_id, quantity in carts.get(
        user_id,
        {},
    ).items():

        product = PRODUCTS.get(
            product_id
        )

        if not product:
            continue

        items.append(
            {
                "product_id": product_id,
                "name": product["name"],
                "size": product["size"],
                "quantity": quantity,
                "unit_price": product["price"],
                "subtotal": (
                    product["price"]
                    * quantity
                ),
            }
        )

    order = {
        "order_number": order_number,
        "user_id": user_id,
        "customer_id": customer_id,
        "date": now_text(),
        "created_at": datetime.now().isoformat(),
        "customer_name": customer.get(
            "name",
            "",
        ),
        "phone": customer.get(
            "phone",
            "",
        ),
        "items": items,
        "subtotal": subtotal,
        "delivery_fee": fee,
        "total": total,
        "delivery_place": delivery.get(
            "title",
            "",
        ),
        "address": delivery.get(
            "address",
            "",
        ),
        "shipping_method": delivery.get(
            "shipping_method",
            "",
        ),
        "payment_status": "در انتظار پرداخت",
        "receipt": "",
    }

    DATA["orders"].append(order)

    save_data()

    # =====================================================
    # پیام پرداخت به مشتری
    # =====================================================

    payment_text = (
        "🎉 سفارش شما ثبت شد.\n\n"
        f"🔢 شماره سفارش: "
        f"#{order_number}\n"
        f"💳 مبلغ قابل پرداخت: "
        f"{money(total)}\n\n"
        "لطفاً مبلغ بالا را به شماره کارت "
        "زیر واریز کنید:\n\n"
        f"💳 {PAYMENT_CARD}\n"
    )

    if PAYMENT_OWNER:

        payment_text += (
            f"👤 به نام: "
            f"{PAYMENT_OWNER}\n"
        )

    payment_text += (
        "\n📸 سپس تصویر رسید پرداخت را "
        "ارسال کنید."
    )

    # بسیار مهم:
    # از این لحظه هر عکس دریافتی متعلق به همین سفارش است.
    user_states[user_id] = {
        "type": "payment_receipt",
        "order_number": order_number,
    }

    # سبد سفارش ثبت شده و دیگر لازم نیست در حافظه باشد.
    carts.pop(
        user_id,
        None,
    )

    current_delivery.pop(
        user_id,
        None,
    )

    await send_screen(
        message,
        payment_text,
        user_id=user_id,
    )

    # =====================================================
    # ارسال سفارش به مدیر
    # =====================================================

    admin_text = (
        "🆕 سفارش جدید سبزی‌یو\n\n"
        f"🔢 شماره سفارش: "
        f"#{order_number}\n"
        f"📅 تاریخ: "
        f"{order['date']}\n"
        f"👤 مشتری: "
        f"{order['customer_name']}\n"
        f"📱 تلفن: "
        f"{order['phone']}\n"
        f"📍 تحویل: "
        f"{order['delivery_place']}\n"
    )

    if order["address"]:

        admin_text += (
            f"🏠 آدرس: "
            f"{order['address']}\n"
        )

    if order["shipping_method"]:

        admin_text += (
            f"🚚 ارسال: "
            f"{order['shipping_method']}\n"
        )

    admin_text += (
        f"\n💰 مبلغ نهایی: "
        f"{money(total)}\n"
        f"🆔 Bale ID: {user_id}\n"
        "\n⏳ وضعیت پرداخت: "
        "در انتظار رسید"
    )

    for admin_id in ADMIN_CHAT_IDS:

        try:

            await bot.send_message(
                chat_id=int(admin_id),
                text=admin_text,
            )

        except Exception as e:

            logging.exception(
                f"ارسال سفارش به مدیر "
                f"{admin_id} ناموفق بود: {e}"
            )


# =========================================================
# پردازش رسید
# =========================================================

async def process_payment_receipt(
    message,
    user_id,
    state,
):
    """
    تمام منطق رسید فقط در این تابع انجام می‌شود.
    """

    order_number = state.get(
        "order_number"
    )

    if not order_number:

        logging.error(
            f"برای کاربر {user_id} شماره سفارش رسید وجود ندارد."
        )

        user_states[user_id] = None

        await send_screen(
            message,
            "❌ اطلاعات سفارش پیدا نشد.\n\n"
            "لطفاً دوباره سفارش دهید.",
            user_id=user_id,
        )

        return True

    order = find_order(
        user_id,
        order_number,
    )

    if not order:

        logging.error(
            f"سفارش #{order_number} برای کاربر "
            f"{user_id} پیدا نشد."
        )

        user_states[user_id] = None

        await send_screen(
            message,
            "❌ سفارش پیدا نشد.\n\n"
            "لطفاً با پشتیبانی تماس بگیرید.",
            user_id=user_id,
        )

        return True

    photos = get_message_photos(
        message
    )

    # -----------------------------------------------------
    # عکس نیست
    # -----------------------------------------------------

    if not photos:

        await send_screen(
            message,
            "📸 لطفاً تصویر رسید پرداخت را "
            "به صورت عکس ارسال کنید.",
            user_id=user_id,
        )

        return True

    # -----------------------------------------------------
    # ارسال رسید به مدیر
    # -----------------------------------------------------

    sent = await send_receipt_to_admin(
        message,
        order_number,
        user_id,
        order,
    )

    # -----------------------------------------------------
    # ارسال موفق
    # -----------------------------------------------------

    if sent:

        order["receipt"] = "ارسال شد"

        order["payment_status"] = (
            "رسید ارسال شد"
        )

        order["receipt_received_at"] = (
            now_text()
        )

        save_data()

        # بسیار مهم:
        # حالت رسید همین‌جا پاک می‌شود.
        # بنابراین عکس بعدی دوباره رسید تلقی نمی‌شود.
        user_states[user_id] = None

        await send_screen(
            message,
            "✅ رسید پرداخت شما دریافت شد.\n\n"
            f"🔢 شماره سفارش: #{order_number}\n\n"
            "رسید برای مدیریت ارسال شد و "
            "پس از بررسی پرداخت، سفارش شما "
            "آماده خواهد شد. 🌿",
            user_id=user_id,
        )

        return True

    # -----------------------------------------------------
    # ارسال ناموفق
    # -----------------------------------------------------

    order["payment_status"] = (
        "خطا در ارسال رسید"
    )

    save_data()

    # حالت رسید را نگه می‌داریم تا کاربر
    # همان رسید را دوباره ارسال کند.

    await send_screen(
        message,
        "⚠️ عکس رسید دریافت شد، اما "
        "ارسال آن برای مدیریت ناموفق بود.\n\n"
        "لطفاً چند لحظه بعد دوباره همین "
        "رسید را ارسال کنید.",
        user_id=user_id,
    )

    return True


# =========================================================
# پیام‌های کاربر
# =========================================================

@bot.event
async def on_message(
    message: Message
):

    user_id = str(
        message.author.user_id
    )

    print(
        f"USER_ID: {user_id}",
        flush=True,
    )

    # =====================================================
    # /start
    # =====================================================

    if message.content:

        text = message.content.strip()

        if text == "/start":

            user_states[user_id] = None

            active_customer.pop(
                user_id,
                None,
            )

            current_delivery.pop(
                user_id,
                None,
            )

            carts.pop(
                user_id,
                None,
            )

            await show_home(
                message,
                user_id,
            )

            return

    # =====================================================
    # رسید پرداخت
    #
    # این بخش باید قبل از تمام منطق‌های متنی باشد.
    # =====================================================

    state = user_states.get(
        user_id
    )

    if (
        isinstance(state, dict)
        and state.get("type")
        == "payment_receipt"
    ):

        await process_payment_receipt(
            message,
            user_id,
            state,
        )

        return

    # =====================================================
    # شماره تلفن
    # =====================================================

    contact = getattr(
        message,
        "contact",
        None,
    )

    if contact:

        phone = getattr(
            contact,
            "phone_number",
            None,
        )

        if phone:

            state = user_states.get(
                user_id
            )

            if (
                isinstance(state, dict)
                and state.get("type")
                == "customer_phone"
            ):

                customer_id = state[
                    "customer_id"
                ]

            else:

                customer_id = active_customer.get(
                    user_id
                )

            if (
                not customer_id
                or customer_id not in DATA["customers"]
            ):

                return

            DATA["customers"][
                customer_id
            ]["phone"] = phone

            save_data()

            user_states[user_id] = None

            await show_delivery(
                message,
                user_id,
            )

            return

    # =====================================================
    # متن
    # =====================================================

    if not message.content:
        return

    text = message.content.strip()

    if not text:
        return

    state = user_states.get(
        user_id
    )

    # =====================================================
    # نام مشتری
    # =====================================================

    if (
        isinstance(state, dict)
        and state.get("type")
        == "customer_name"
    ):

        customer_id = state[
            "customer_id"
        ]

        if customer_id not in DATA["customers"]:

            user_states[user_id] = None

            await send_screen(
                message,
                "❌ خطا در ثبت مشتری. "
                "دوباره تلاش کنید.",
                user_id=user_id,
            )

            return

        DATA["customers"][
            customer_id
        ]["name"] = text

        user_states[user_id] = {
            "type": "customer_phone",
            "customer_id": customer_id,
        }

        save_data()

        await send_screen(
            message,
            "👤 نام ثبت شد.\n\n"
            "📱 لطفاً شماره تلفن خود را "
            "با دکمه زیر ارسال کنید:",
            components=phone_keyboard(),
            user_id=user_id,
        )

        return

    # =====================================================
    # شماره تلفن متنی
    # =====================================================

    if (
        isinstance(state, dict)
        and state.get("type")
        == "customer_phone"
    ):

        customer_id = state[
            "customer_id"
        ]

        if customer_id not in DATA["customers"]:

            user_states[user_id] = None
            return

        DATA["customers"][
            customer_id
        ]["phone"] = text

        save_data()

        user_states[user_id] = None

        await show_delivery(
            message,
            user_id,
        )

        return

    # =====================================================
    # عنوان آدرس
    # =====================================================

    if (
        isinstance(state, dict)
        and state.get("type")
        == "address_title"
    ):

        customer_id = state[
            "customer_id"
        ]

        if customer_id not in DATA["customers"]:

            user_states[user_id] = None

            await send_screen(
                message,
                "❌ مشتری پیدا نشد.",
                user_id=user_id,
            )

            return

        user_states[user_id] = {
            "type": "address_text",
            "customer_id": customer_id,
            "title": text,
        }

        await send_screen(
            message,
            "🏠 حالا آدرس کامل را وارد کنید:",
            user_id=user_id,
        )

        return

    # =====================================================
    # متن آدرس
    # =====================================================

    if (
        isinstance(state, dict)
        and state.get("type")
        == "address_text"
    ):

        customer_id = state[
            "customer_id"
        ]

        title = state[
            "title"
        ]

        if customer_id not in DATA["customers"]:

            user_states[user_id] = None

            await send_screen(
                message,
                "❌ مشتری پیدا نشد.",
                user_id=user_id,
            )

            return

        DATA["customers"][
            customer_id
        ].setdefault(
            "addresses",
            [],
        )

        DATA["customers"][
            customer_id
        ]["addresses"].append(
            {
                "title": title,
                "address": text,
            }
        )

        save_data()

        user_states[user_id] = None

        active_customer[user_id] = (
            customer_id
        )

        current_delivery[user_id] = {
            "title": title,
            "address": text,
            "fee": 0,
        }

        await show_shipping_or_invoice(
            message,
            user_id,
        )

        return

    # =====================================================
    # اصلاح نام مشتری
    # =====================================================

    if (
        isinstance(state, dict)
        and state.get("type")
        == "edit_customer_name"
    ):

        customer_id = state[
            "customer_id"
        ]

        if customer_id not in DATA["customers"]:

            user_states[user_id] = None
            return

        DATA["customers"][
            customer_id
        ]["name"] = text

        save_data()

        user_states[user_id] = None

        await show_customer_profile(
            message,
            customer_id,
            user_id,
        )

        return

    # =====================================================
    # اصلاح تلفن
    # =====================================================

    if (
        isinstance(state, dict)
        and state.get("type")
        == "edit_customer_phone"
    ):

        customer_id = state[
            "customer_id"
        ]

        if customer_id not in DATA["customers"]:

            user_states[user_id] = None
            return

        DATA["customers"][
            customer_id
        ]["phone"] = text

        save_data()

        user_states[user_id] = None

        await show_customer_profile(
            message,
            customer_id,
            user_id,
        )

        return

    # =====================================================
    # اصلاح عنوان آدرس
    # =====================================================

    if (
        isinstance(state, dict)
        and state.get("type")
        == "edit_address_title"
    ):

        customer_id = state[
            "customer_id"
        ]

        index = int(
            state["index"]
        )

        customer = DATA["customers"].get(
            customer_id
        )

        if not customer:

            user_states[user_id] = None
            return

        addresses = customer.get(
            "addresses",
            [],
        )

        if (
            index < 0
            or index >= len(addresses)
        ):

            user_states[user_id] = None
            return

        addresses[index]["title"] = text

        user_states[user_id] = {
            "type": "edit_address_text",
            "customer_id": customer_id,
            "index": index,
        }

        save_data()

        await send_screen(
            message,
            "🏠 آدرس جدید را وارد کنید:",
            user_id=user_id,
        )

        return

    # =====================================================
    # اصلاح متن آدرس
    # =====================================================

    if (
        isinstance(state, dict)
        and state.get("type")
        == "edit_address_text"
    ):

        customer_id = state[
            "customer_id"
        ]

        index = int(
            state["index"]
        )

        customer = DATA["customers"].get(
            customer_id
        )

        if not customer:

            user_states[user_id] = None
            return

        addresses = customer.get(
            "addresses",
            [],
        )

        if (
            index < 0
            or index >= len(addresses)
        ):

            user_states[user_id] = None
            return

        addresses[index]["address"] = text

        save_data()

        user_states[user_id] = None

        await show_addresses(
            message,
            customer_id,
            back_callback=(
                f"addresses_profile_"
                f"{customer_id}"
            ),
            user_id=user_id,
        )

        return


# =========================================================
# Callback
# =========================================================

@bot.event
async def on_callback(
    callback: CallbackQuery
):

    user_id = str(
        callback.from_user.user_id
    )

    data = callback.data or ""

    try:

        if hasattr(callback, "answer"):
            await callback.answer()

    except Exception:
        pass

    # =====================================================
    # صفحه اصلی
    # =====================================================

    if data == "home":

        user_states[user_id] = None

        await show_home(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # خریدهای قبلی
    # =====================================================

    if data == "previous_orders":

        user_states[user_id] = None

        await show_previous_orders(
            callback.message,
            user_id,
        )

        return

    if data.startswith(
        "order_history_"
    ):

        order_number = data[
            len("order_history_"):
        ]

        await show_order_history(
            callback.message,
            user_id,
            order_number,
        )

        return

    # =====================================================
    # فروشگاه
    # =====================================================

    if data == "shop":

        user_states[user_id] = None

        await show_shop(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # دسته‌بندی
    # =====================================================

    if data.startswith(
        "category_"
    ):

        category = data[
            len("category_"):
        ]

        await send_screen_callback(
            callback,
            (
                f"{CATEGORY_NAMES.get(category, '📦 محصولات')}"
                "\n\n"
                "محصول موردنظر را انتخاب کنید:"
            ),
            components=category_keyboard(
                category
            ),
        )

        return

    # =====================================================
    # محصول
    # =====================================================

    if data.startswith(
        "product_"
    ):

        product_id = data[
            len("product_"):
        ]

        product = PRODUCTS.get(
            product_id
        )

        if not product:
            return

        await send_screen_callback(
            callback,
            f"🌿 {product['name']}\n\n"
            f"📦 {product['size']}\n"
            f"💰 {money(product['price'])}",
            components=product_keyboard(
                product_id
            ),
        )

        return

    # =====================================================
    # افزودن
    # =====================================================

    if data.startswith("add_"):

        product_id = data[
            len("add_"):
        ]

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
            )
            + 1
        )

        await show_cart(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # افزایش
    # =====================================================

    if data.startswith("plus_"):

        product_id = data[
            len("plus_"):
        ]

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
            )
            + 1
        )

        await show_cart(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # کاهش
    # =====================================================

    if data.startswith("minus_"):

        product_id = data[
            len("minus_"):
        ]

        if product_id in carts.get(
            user_id,
            {},
        ):

            carts[user_id][product_id] -= 1

            if carts[user_id][product_id] <= 0:

                del carts[user_id][
                    product_id
                ]

        await show_cart(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # سبد
    # =====================================================

    if data == "cart":

        await show_cart(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # شروع سفارش
    # =====================================================

    if data == "start_order":

        await start_order(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # مشتری جدید
    # =====================================================

    if data == "new_customer":

        await start_new_customer(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # مشتری قدیمی
    # =====================================================

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

    # =====================================================
    # انتخاب مشتری
    # =====================================================

    if data.startswith(
        "select_customer_"
    ):

        customer_id = data[
            len("select_customer_"):
        ]

        if customer_id not in DATA["customers"]:
            return

        await show_customer_profile(
            callback.message,
            customer_id,
            user_id,
        )

        return

    # =====================================================
    # استفاده از مشتری
    # =====================================================

    if data.startswith(
        "use_customer_"
    ):

        customer_id = data[
            len("use_customer_"):
        ]

        if customer_id not in DATA["customers"]:
            return

        active_customer[user_id] = (
            customer_id
        )

        await show_delivery(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # پروفایل
    # =====================================================

    if data.startswith(
        "profile_"
    ):

        customer_id = data[
            len("profile_"):
        ]

        if customer_id not in DATA["customers"]:
            return

        await show_customer_profile(
            callback.message,
            customer_id,
            user_id,
        )

        return

    # =====================================================
    # اصلاح مشتری
    # =====================================================

    if data.startswith(
        "edit_customer_"
    ):

        customer_id = data[
            len("edit_customer_"):
        ]

        if customer_id not in DATA["customers"]:
            return

        keyboard = InlineKeyboardMarkup()

        keyboard.add(
            InlineKeyboardButton(
                text="👤 اصلاح نام",
                callback_data=(
                    f"edit_name_{customer_id}"
                ),
            ),
            row=1,
        )

        keyboard.add(
            InlineKeyboardButton(
                text="📱 اصلاح شماره",
                callback_data=(
                    f"edit_phone_{customer_id}"
                ),
            ),
            row=2,
        )

        keyboard.add(
            InlineKeyboardButton(
                text="⬅️ بازگشت",
                callback_data=(
                    f"profile_{customer_id}"
                ),
            ),
            row=3,
        )

        await send_screen_callback(
            callback,
            "✏️ اصلاح مشخصات",
            components=keyboard,
        )

        return

    # =====================================================
    # اصلاح نام
    # =====================================================

    if data.startswith(
        "edit_name_"
    ):

        customer_id = data[
            len("edit_name_"):
        ]

        if customer_id not in DATA["customers"]:
            return

        user_states[user_id] = {
            "type": "edit_customer_name",
            "customer_id": customer_id,
        }

        await send_screen_callback(
            callback,
            "👤 نام و نام خانوادگی جدید "
            "را وارد کنید:",
        )

        return

    # =====================================================
    # اصلاح شماره
    # =====================================================

    if data.startswith(
        "edit_phone_"
    ):

        customer_id = data[
            len("edit_phone_"):
        ]

        if customer_id not in DATA["customers"]:
            return

        user_states[user_id] = {
            "type": "edit_customer_phone",
            "customer_id": customer_id,
        }

        await send_screen_callback(
            callback,
            "📱 شماره تلفن جدید را وارد کنید:",
        )

        return

    # =====================================================
    # حذف مشتری
    # =====================================================

    if data.startswith(
        "delete_customer_"
    ):

        customer_id = data[
            len("delete_customer_"):
        ]

        DATA["customers"].pop(
            customer_id,
            None,
        )

        if (
            active_customer.get(
                user_id
            )
            == customer_id
        ):

            active_customer.pop(
                user_id,
                None,
            )

        save_data()

        await show_customer_list(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # آدرس‌های پروفایل
    # =====================================================

    if data.startswith(
        "addresses_profile_"
    ):

        customer_id = data[
            len("addresses_profile_"):
        ]

        if customer_id not in DATA["customers"]:
            return

        await show_addresses(
            callback.message,
            customer_id,
            back_callback=(
                f"profile_{customer_id}"
            ),
            user_id=user_id,
        )

        return

    # =====================================================
    # آدرس‌های سفارش
    # =====================================================

    if data == "addresses_order":

        customer_id = active_customer.get(
            user_id
        )

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
            user_id=user_id,
        )

        return

    if data.startswith(
        "addresses_order_"
    ):

        customer_id = data[
            len("addresses_order_"):
        ]

        if customer_id not in DATA["customers"]:
            return

        await show_addresses(
            callback.message,
            customer_id,
            back_callback="delivery",
            user_id=user_id,
        )

        return

    # =====================================================
    # افزودن آدرس
    # =====================================================

    if data.startswith(
        "add_address_"
    ):

        customer_id = data[
            len("add_address_"):
        ]

        if customer_id not in DATA["customers"]:
            return

        await start_new_address(
            callback.message,
            user_id,
            customer_id,
        )

        return

    # =====================================================
    # انتخاب آدرس
    # =====================================================

    if data.startswith(
        "select_address_"
    ):

        payload = data[
            len("select_address_"):
        ]

        try:

            customer_id, index_text = (
                payload.rsplit("_", 1)
            )

            index = int(
                index_text
            )

        except (
            ValueError,
            TypeError,
        ):

            return

        customer = DATA["customers"].get(
            customer_id
        )

        if not customer:
            return

        addresses = customer.get(
            "addresses",
            [],
        )

        if (
            index < 0
            or index >= len(addresses)
        ):
            return

        address = addresses[index]

        # آدرس از کدام صفحه آمده؟
        if user_id in active_customer:
            back_callback = (
                f"addresses_profile_"
                f"{customer_id}"
            )
        else:
            back_callback = "delivery"

        await send_screen_callback(
            callback,
            f"📍 "
            f"{address.get('title', 'آدرس')}\n\n"
            f"🏠 "
            f"{address.get('address', '')}",
            components=address_management_keyboard(
                customer_id,
                index,
                back_callback,
            ),
        )

        return

    # =====================================================
    # استفاده از آدرس
    # =====================================================

    if data.startswith(
        "use_address_"
    ):

        payload = data[
            len("use_address_"):
        ]

        try:

            customer_id, index_text = (
                payload.rsplit("_", 1)
            )

            index = int(
                index_text
            )

        except (
            ValueError,
            TypeError,
        ):

            return

        customer = DATA["customers"].get(
            customer_id
        )

        if not customer:
            return

        addresses = customer.get(
            "addresses",
            [],
        )

        if (
            index < 0
            or index >= len(addresses)
        ):
            return

        address = addresses[index]

        active_customer[user_id] = (
            customer_id
        )

        current_delivery[user_id] = {
            "title": address.get(
                "title",
                "آدرس",
            ),
            "address": address.get(
                "address",
                "",
            ),
            "fee": 0,
        }

        await show_shipping_or_invoice(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # اصلاح آدرس
    # =====================================================

    if data.startswith(
        "edit_address_"
    ):

        payload = data[
            len("edit_address_"):
        ]

        try:

            customer_id, index_text = (
                payload.rsplit("_", 1)
            )

            index = int(
                index_text
            )

        except (
            ValueError,
            TypeError,
        ):

            return

        customer = DATA["customers"].get(
            customer_id
        )

        if not customer:
            return

        addresses = customer.get(
            "addresses",
            [],
        )

        if (
            index < 0
            or index >= len(addresses)
        ):
            return

        user_states[user_id] = {
            "type": "edit_address_title",
            "customer_id": customer_id,
            "index": index,
        }

        await send_screen_callback(
            callback,
            "✏️ نام این آدرس را وارد کنید:",
        )

        return

    # =====================================================
    # حذف آدرس
    # =====================================================

    if data.startswith(
        "delete_address_"
    ):

        payload = data[
            len("delete_address_"):
        ]

        try:

            customer_id, index_text = (
                payload.rsplit("_", 1)
            )

            index = int(
                index_text
            )

        except (
            ValueError,
            TypeError,
        ):

            return

        customer = DATA["customers"].get(
            customer_id
        )

        if not customer:
            return

        addresses = customer.get(
            "addresses",
            [],
        )

        if (
            index < 0
            or index >= len(addresses)
        ):
            return

        del addresses[index]

        save_data()

        await show_addresses(
            callback.message,
            customer_id,
            back_callback=(
                f"profile_{customer_id}"
            ),
            user_id=user_id,
        )

        return

    # =====================================================
    # تحویل
    # =====================================================

    if data == "delivery":

        await show_delivery(
            callback.message,
            user_id,
        )

        return

    if data == "free_delivery":

        await send_screen_callback(
            callback,
            "📍 تحویل رایگان / حضوری "
            "را انتخاب کنید:",
            components=free_delivery_keyboard(),
        )

        return

    if data == "delivery_pickup":

        current_delivery[user_id] = {
            "title": "تحویل حضوری",
            "address": "",
            "fee": 0,
        }

        await show_final_invoice(
            callback.message,
            user_id,
        )

        return

    if data == "delivery_heyat":

        current_delivery[user_id] = {
            "title": "تحویل در هیأت امنا",
            "address": "",
            "fee": 0,
        }

        await show_final_invoice(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # آدرس‌های ذخیره‌شده
    # =====================================================

    if data == "delivery_saved":

        customer_id = active_customer.get(
            user_id
        )

        if not customer_id:

            await show_customer_start(
                callback.message,
                user_id,
            )

            return

        customer = DATA["customers"].get(
            customer_id,
            {},
        )

        addresses = customer.get(
            "addresses",
            [],
        )

        if not addresses:

            keyboard = InlineKeyboardMarkup()

            keyboard.add(
                InlineKeyboardButton(
                    text="➕ افزودن آدرس",
                    callback_data=(
                        f"add_address_"
                        f"{customer_id}"
                    ),
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

            await send_screen_callback(
                callback,
                "📍 آدرس‌های من\n\n"
                "هنوز آدرسی برای شما "
                "ثبت نشده است.",
                components=keyboard,
            )

            return

        await show_addresses(
            callback.message,
            customer_id,
            back_callback="delivery",
            user_id=user_id,
        )

        return

    # =====================================================
    # آدرس جدید
    # =====================================================

    if data == "delivery_new_address":

        customer_id = active_customer.get(
            user_id
        )

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

    # =====================================================
    # الوپیک
    # =====================================================

    if data == "shipping_alopik":

        current_delivery.setdefault(
            user_id,
            {},
        )

        current_delivery[user_id][
            "shipping_method"
        ] = "الوپیک"

        current_delivery[user_id][
            "fee"
        ] = 0

        await show_final_invoice(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # اسنپ‌باکس
    # =====================================================

    if data == "shipping_snapp":

        current_delivery.setdefault(
            user_id,
            {},
        )

        current_delivery[user_id][
            "shipping_method"
        ] = "اسنپ‌باکس"

        current_delivery[user_id][
            "fee"
        ] = 0

        await show_final_invoice(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # اصلاح سبد
    # =====================================================

    if data == "edit_cart":

        await show_cart(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # پرداخت
    # =====================================================

    if data == "payment":

        await create_order(
            callback.message,
            user_id,
        )

        return

    # =====================================================
    # لغو
    # =====================================================

    if data == "cancel_cart":

        carts.pop(
            user_id,
            None,
        )

        current_delivery.pop(
            user_id,
            None,
        )

        user_states[user_id] = None

        await show_home(
            callback.message,
            user_id,
        )

        return


# =========================================================
# انتخاب روش ارسال برای آدرس
# =========================================================

async def show_shipping_or_invoice(
    message,
    user_id,
):

    delivery = current_delivery.get(
        user_id,
        {},
    )

    if delivery.get("address"):

        await send_screen(
            message,
            "🚚 روش ارسال را انتخاب کنید:",
            components=shipping_keyboard(),
            user_id=user_id,
        )

        return

    await show_final_invoice(
        message,
        user_id,
    )


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

    print(
        f"ADMIN_CHAT_IDS: {ADMIN_CHAT_IDS}",
        flush=True,
    )


bot.run()
