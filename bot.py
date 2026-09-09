import os
import json
import logging
import requests
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================================================
# تنظیمات
# =========================================================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

ADMIN_CHAT_IDS = [
    x.strip()
    for x in os.getenv(
        "TELEGRAM_ADMIN_CHAT_IDS",
        "",
    ).split(",")
    if x.strip()
]

PAYMENT_CARD = "6219861967021642"

PAYMENT_OWNER = os.getenv(
    "TELEGRAM_PAYMENT_OWNER",
    "",
)

BALE_BOT_TOKEN = os.getenv(
    "BALE_BOT_TOKEN",
)

BALE_ADMIN_CHAT_ID = os.getenv(
    "BALE_ADMIN_CHAT_ID",
)

STATE_FILE = "telegram_data.json"


if not TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN تنظیم نشده است."
    )


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# =========================================================
# اتصال به ربات بله
# =========================================================

def send_message_to_bale(text):
    if not BALE_BOT_TOKEN:
        logging.error(
            "❌ BALE_BOT_TOKEN تنظیم نشده است."
        )
        return False

    if not BALE_ADMIN_CHAT_ID:
        logging.error(
            "❌ BALE_ADMIN_CHAT_ID تنظیم نشده است."
        )
        return False

    url = (
        f"https://tapi.bale.ai/bot"
        f"{BALE_BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": BALE_ADMIN_CHAT_ID,
        "text": text,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15,
        )

        if response.ok:
            logging.info(
                "✅ پیام با موفقیت به بله ارسال شد."
            )
            return True

        logging.error(
            "❌ ارسال پیام به بله ناموفق بود: "
            f"{response.status_code} - {response.text}"
        )
        return False

    except Exception as e:
        logging.exception(
            f"❌ خطا در اتصال به بله: {e}"
        )
        return False


# =========================================================
# DATA
# =========================================================


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

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        data.setdefault(
            "customers",
            {},
        )

        data.setdefault(
            "orders",
            [],
        )

        data.setdefault(
            "next_order_number",
            1000,
        )

        for customer in data["customers"].values():

            customer.setdefault(
                "addresses",
                [],
            )

        # هر اکانت فقط یک مشتری دارد.
        customers = {}

        for customer_id, customer in data["customers"].items():

            if "_customer_" in customer_id:

                user_id = customer_id.split(
                    "_customer_",
                    1,
                )[0]

            else:

                user_id = customer_id

            if user_id not in customers:

                customers[user_id] = {
                    "name": customer.get(
                        "name",
                        "",
                    ),
                    "phone": customer.get(
                        "phone",
                        "",
                    ),
                    "addresses": list(
                        customer.get(
                            "addresses",
                            [],
                        )
                    ),
                }

                continue

            current = customers[user_id]

            if (
                not current.get("name")
                and customer.get("name")
            ):

                current["name"] = customer[
                    "name"
                ]

            if (
                not current.get("phone")
                and customer.get("phone")
            ):

                current["phone"] = customer[
                    "phone"
                ]

            current["addresses"].extend(
                customer.get(
                    "addresses",
                    [],
                )
            )

        data["customers"] = customers

        return data

    except Exception as e:

        logging.error(
            f"خطا در خواندن داده‌ها: {e}"
        )

        return default


DATA = load_data()

user_states = {}
active_customer = {}
carts = {}
current_delivery = {}

# پیام فعال ربات برای هر کاربر
last_bot_message = {}


def save_data():

    temp = STATE_FILE + ".tmp"

    try:

        with open(
            temp,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                DATA,
                f,
                ensure_ascii=False,
                indent=2,
            )

        os.replace(
            temp,
            STATE_FILE,
        )

    except Exception as e:

        logging.error(
            f"خطا در ذخیره اطلاعات: {e}"
        )


# =========================================================
# مدیریت صفحه‌های ربات
# =========================================================

async def delete_last_bot_message(
    user_id,
):

    old_message = last_bot_message.get(
        user_id
    )

    if not old_message:
        return

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


async def send_screen(
    message,
    text,
    components=None,
    user_id=None,
):

    if user_id is None:

        user_id = str(
            message.from_user.id
        )

    old_message = last_bot_message.get(
        user_id
    )

    if old_message:

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

        new_message = await message.reply_text(
            text,
            reply_markup=components,
        )

        last_bot_message[user_id] = (
            new_message
        )

        return new_message

    except Exception as e:

        logging.error(
            f"ارسال صفحه ناموفق بود: {e}"
        )

        return None


async def send_screen_callback(
    query,
    text,
    components=None,
):

    user_id = str(
        query.from_user.id
    )

    callback_message = query.message

    old_message = last_bot_message.get(
        user_id
    )

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

        await query.answer()

    except Exception:

        pass

    try:

        new_message = await callback_message.reply_text(
            text,
            reply_markup=components,
        )

        last_bot_message[user_id] = (
            new_message
        )

        return new_message

    except Exception as e:

        logging.error(
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


def cart_total(user_id):

    total = 0

    for product_id, quantity in carts.get(
        user_id,
        {},
    ).items():

        product = PRODUCTS.get(
            product_id
        )

        if product:

            total += (
                product["price"]
                * quantity
            )

    return total


def delivery_fee(delivery):

    return int(
        delivery.get(
            "fee",
            0,
        )
    )


def find_order(
    user_id,
    order_number,
):

    for order in DATA["orders"]:

        if (
            str(order.get("user_id"))
            == str(user_id)
            and str(
                order.get("order_number")
            )
            == str(order_number)
        ):

            return order

    return None


# =========================================================
# محصولات
# =========================================================

PRODUCTS = {

    "fried_1": {
        "name": "بادمجان سرخ شده",
        "category": "fried",
        "size": "1 کیلوگرم",
        "price": 370000,
        "image": "",
        "active": True,
    },

    "fried_2": {
        "name": "بادمجان کبابی",
        "category": "fried",
        "size": "1 کیلوگرم",
        "price": 310000,
        "image": "",
        "active": True,
    },

    "fried_3": {
        "name": "بامیه سرخ شده",
        "category": "fried",
        "size": "500 گرم",
        "price": 290000,
        "image": "",
        "active": True,
    },

    "fried_4": {
        "name": "پیاز داغ",
        "category": "fried",
        "size": "500 گرم",
        "price": 400000,
        "image": "",
        "active": True,
    },

    "fried_5": {
        "name": "پیاز داغ ممتاز سبزی‌یو",
        "category": "fried",
        "size": "500 گرم",
        "price": 650000,
        "image": "",
        "active": True,
    },

    "fried_6": {
        "name": "خوراک لوبیا سرخ‌شده",
        "category": "fried",
        "size": "500 گرم",
        "price": 280000,
        "image": "",
        "active": True,
    },

    "fried_7": {
        "name": "لوبیا سرخ شده",
        "category": "fried",
        "size": "500 گرم",
        "price": 290000,
        "image": "",
        "active": True,
    },

    "fried_8": {
        "name": "لوبیا گوجه سرخ شده",
        "category": "fried",
        "size": "500 گرم",
        "price": 290000,
        "image": "",
        "active": True,
    },

    "fried_9": {
        "name": "میرزا قاسمی نیمه‌آماده",
        "category": "fried",
        "size": "500 گرم",
        "price": 200000,
        "image": "",
        "active": True,
    },

    "fried_10": {
        "name": "ساقه کرفس سرخ شده",
        "category": "fried",
        "size": "500 گرم",
        "price": 290000,
        "image": "",
        "active": True,
    },

    "fried_11": {
        "name": "سبزی کرفس سرخ‌شده",
        "category": "fried",
        "size": "500 گرم",
        "price": 290000,
        "image": "",
        "active": True,
    },

    "fried_12": {
        "name": "سبزی و ساقه کرفس سرخ‌شده",
        "category": "fried",
        "size": "500 گرم",
        "price": 290000,
        "image": "",
        "active": True,
    },

    "fried_13": {
        "name": "اسفناج",
        "category": "fried",
        "size": "500 گرم",
        "price": 290000,
        "image": "",
        "active": True,
    },

    "fried_14": {
        "name": "سبزی قلیه ماهی",
        "category": "fried",
        "size": "500 گرم",
        "price": 290000,
        "image": "",
        "active": True,
    },

    "fried_15": {
        "name": "سبزی قرمه",
        "category": "fried",
        "size": "500 گرم",
        "price": 290000,
        "image": "",
        "active": True,
    },

    "raw_1": {
        "name": "سبزی آش",
        "category": "raw",
        "size": "500 گرم",
        "price": 70000,
        "image": "",
        "active": True,
    },

    "raw_2": {
        "name": "سبزی کوکو و سبزی پلو",
        "category": "raw",
        "size": "500 گرم",
        "price": 70000,
        "image": "",
        "active": True,
    },

    "raw_3": {
        "name": "ذرت تازه و آماده پخت",
        "category": "raw",
        "size": "500 گرم",
        "price": 210000,
        "image": "",
        "active": True,
    },

    "raw_4": {
        "name": "نخود فرنگی آماده پخت",
        "category": "raw",
        "size": "500 گرم",
        "price": 230000,
        "image": "",
        "active": True,
    },

    "pickle_1": {
        "name": "ترشی آلبالو",
        "category": "pickles",
        "size": "500 گرم",
        "price": 350000,
        "image": "",
        "active": True,
    },

    "pickle_2": {
        "name": "ترشی بادمجان شکم‌پر",
        "category": "pickles",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "pickle_3": {
        "name": "ترشی بندری / سالادی",
        "category": "pickles",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "pickle_4": {
        "name": "ترشی ساقه سبزی رژیمی",
        "category": "pickles",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "pickle_5": {
        "name": "ترشی لبو",
        "category": "pickles",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "pickle_6": {
        "name": "ترشی لیته بادمجان",
        "category": "pickles",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "pickle_7": {
        "name": "ترشی مخلوط درشت",
        "category": "pickles",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "pickle_8": {
        "name": "ترشی مخلوط ریز",
        "category": "pickles",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "pickle_9": {
        "name": "ترشی مکزیکی",
        "category": "pickles",
        "size": "500 گرم",
        "price": 400000,
        "image": "",
        "active": True,
    },

    "pickle_10": {
        "name": "ترشی نازخاتون",
        "category": "pickles",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "pickle_11": {
        "name": "شور",
        "category": "pickles",
        "size": "500 گرم",
        "price": 150000,
        "image": "",
        "active": True,
    },

    "syrup_1": {
        "name": "شربت آلبالو",
        "category": "syrup",
        "size": "1 لیتر",
        "price": 400000,
        "image": "",
        "active": True,
    },

    "syrup_2": {
        "name": "شربت انبه زعفران",
        "category": "syrup",
        "size": "1 لیتر",
        "price": 400000,
        "image": "",
        "active": True,
    },

    "syrup_3": {
        "name": "شربت بالنگو",
        "category": "syrup",
        "size": "1 لیتر",
        "price": 400000,
        "image": "",
        "active": True,
    },

    "syrup_4": {
        "name": "شربت سکنجبین",
        "category": "syrup",
        "size": "1 لیتر",
        "price": 300000,
        "image": "",
        "active": True,
    },

    "syrup_5": {
        "name": "شربت هل زعفران",
        "category": "syrup",
        "size": "1 لیتر",
        "price": 400000,
        "image": "",
        "active": True,
    },

    "jam_1": {
        "name": "مربای آلبالو",
        "category": "jam",
        "size": "500 گرم",
        "price": 350000,
        "image": "",
        "active": True,
    },

    "jam_2": {
        "name": "مربای بالنگ",
        "category": "jam",
        "size": "500 گرم",
        "price": 350000,
        "image": "",
        "active": True,
    },

    "jam_3": {
        "name": "مربای پرتقال",
        "category": "jam",
        "size": "500 گرم",
        "price": 280000,
        "image": "",
        "active": True,
    },

    "jam_4": {
        "name": "مربای توت‌فرنگی",
        "category": "jam",
        "size": "500 گرم",
        "price": 350000,
        "image": "",
        "active": True,
    },

    "jam_5": {
        "name": "مربای هویج",
        "category": "jam",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "spice_1": {
        "name": "زردچوبه",
        "category": "spices",
        "size": "500 گرم",
        "price": 300000,
        "image": "",
        "active": True,
    },

    "spice_2": {
        "name": "فلفل سیاه",
        "category": "spices",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "spice_3": {
        "name": "نعنا خشک",
        "category": "spices",
        "size": "500 گرم",
        "price": 650000,
        "image": "",
        "active": True,
    },

    "condiment_1": {
        "name": "عرق نعنا",
        "category": "condiments",
        "size": "1 لیتر",
        "price": 220000,
        "image": "",
        "active": True,
    },

    "condiment_2": {
        "name": "گلاب",
        "category": "condiments",
        "size": "1 لیتر",
        "price": 300000,
        "image": "",
        "active": True,
    },

    "condiment_3": {
        "name": "سرکه انگور",
        "category": "condiments",
        "size": "1 لیتر",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "condiment_4": {
        "name": "سرکه سیب",
        "category": "condiments",
        "size": "1 لیتر",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "condiment_5": {
        "name": "آبغوره",
        "category": "condiments",
        "size": "1 لیتر",
        "price": 400000,
        "image": "",
        "active": True,
    },

    "condiment_6": {
        "name": "رب انار",
        "category": "condiments",
        "size": "500 گرم",
        "price": 350000,
        "image": "",
        "active": True,
    },

    "condiment_7": {
        "name": "رب گوجه فرنگی",
        "category": "condiments",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },
}


CATEGORY_NAMES = {
    "fried": "🌿 سبزی‌های سرخ‌شده",
    "raw": "🥬 سبزی‌های خام و تازه",
    "pickles": "🥒 ترشیجات",
    "syrup": "🥭 شربت‌ها",
    "jam": "🍓 مرباها",
    "spices": "🧂 ادویه‌ها",
    "condiments": "🌱 چاشنی‌ها و عرقیات",
}


# =========================================================
# صفحه اول
# =========================================================

def home_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🧾 خریدهای قبلی",
                callback_data="previous_orders",
            )
        ],
        [
            InlineKeyboardButton(
                "🛒 فروشگاه سبزی‌یو",
                callback_data="shop",
            )
        ],
    ])


async def show_home(
    message,
    user_id=None,
):

    if user_id is None:
        user_id = str(message.from_user.id)

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

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data=callback_data,
            )
        ]
    ])


# =========================================================
# خریدهای قبلی
# =========================================================

def previous_orders_keyboard(user_id):

    buttons = []

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

    for order in orders:

        buttons.append([
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
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "⬅️ بازگشت",
            callback_data="home",
        )
    ])

    return InlineKeyboardMarkup(buttons)


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

    if (
        order.get("latitude") is not None
        and order.get("longitude") is not None
    ):

        text += (
            f"🌐 لوکیشن: "
            f"{order['latitude']}, "
            f"{order['longitude']}\n"
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

    buttons = []

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

    for category in categories:

        buttons.append([
            InlineKeyboardButton(
                text=CATEGORY_NAMES.get(
                    category,
                    f"📦 {category}",
                ),
                callback_data=(
                    f"category_{category}"
                ),
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "⬅️ بازگشت",
            callback_data="home",
        )
    ])

    return InlineKeyboardMarkup(buttons)


async def show_shop(
    message,
    user_id=None,
):

    if user_id is None:
        user_id = str(message.from_user.id)

    await send_screen(
        message,
        "🛒 فروشگاه سبزی‌یو\n\n"
        "دسته‌بندی کالاها را انتخاب کنید:",
        components=categories_keyboard(),
        user_id=user_id,
    )


def category_keyboard(category):

    buttons = []

    for product_id, product in PRODUCTS.items():

        if product.get("category") != category:
            continue

        if product.get("active", True) is False:
            continue

        buttons.append([
            InlineKeyboardButton(
                text=(
                    f"{product['name']} | "
                    f"{product['size']}"
                ),
                callback_data=(
                    f"product_{product_id}"
                ),
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "⬅️ بازگشت",
            callback_data="shop",
        )
    ])

    return InlineKeyboardMarkup(buttons)


def product_keyboard(product_id):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ افزودن به سبد",
                callback_data=f"add_{product_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="shop",
            )
        ],
    ])


# =========================================================
# سبد خرید
# =========================================================

def cart_keyboard(user_id):

    buttons = []

    for product_id, quantity in carts.get(
        user_id,
        {},
    ).items():

        product = PRODUCTS.get(
            product_id
        )

        if not product:
            continue

        buttons.append([
            InlineKeyboardButton(
                text=(
                    f"➕ افزایش | {product['name']} "
                    f"({quantity})"
                ),
                callback_data=(
                    f"plus_{product_id}"
                ),
            )
        ])

        buttons.append([
            InlineKeyboardButton(
                text=(
                    f"➖ کاهش | {product['name']}"
                ),
                callback_data=(
                    f"minus_{product_id}"
                ),
            )
        ])

    if carts.get(user_id):

        buttons.append([
            InlineKeyboardButton(
                "📦 ثبت سفارش",
                callback_data="start_order",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "➕ ادامه خرید",
            callback_data="shop",
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "❌ لغو خرید",
            callback_data="cancel_cart",
        )
    ])

    return InlineKeyboardMarkup(buttons)

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
            product["price"]
            * quantity
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

def get_user_customer(user_id):

    return DATA["customers"].get(
        user_id
    )


def customer_start_keyboard(user_id):

    customer = get_user_customer(
        user_id
    )

    if customer:

        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✏️ اصلاح مشخصات",
                    callback_data=(
                        f"edit_customer_{user_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "📍 مدیریت آدرس‌ها",
                    callback_data=(
                        f"addresses_profile_{user_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="cart",
                )
            ],
        ])

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "👤 ثبت مشخصات",
                callback_data="new_customer",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="cart",
            )
        ],
    ])


async def show_customer_start(
    message,
    user_id,
):

    customer = get_user_customer(
        user_id
    )

    if customer:

        await show_customer_profile(
            message,
            user_id,
            user_id,
        )

        return

    await send_screen(
        message,
        "👤 مشخصات من\n\n"
        "هنوز مشخصات شما ثبت نشده است.",
        components=customer_start_keyboard(
            user_id
        ),
        user_id=user_id,
    )


def customer_profile_keyboard(
    customer_id
):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✏️ اصلاح مشخصات",
                callback_data=(
                    f"edit_customer_{customer_id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "📍 مدیریت آدرس‌ها",
                callback_data=(
                    f"addresses_profile_{customer_id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="cart",
            )
        ],
    ])


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
        user_id = str(message.from_user.id)

    active_customer[user_id] = customer_id

    await send_screen(
        message,
        "👤 مشخصات من\n\n"
        f"👤 نام: {customer.get('name', '')}\n"
        f"📱 تلفن: {customer.get('phone', '')}\n\n"
        "عملیات موردنظر:",
        components=customer_profile_keyboard(
            customer_id
        ),
        user_id=user_id,
    )


# =========================================================
# ثبت مشتری
# =========================================================

async def start_new_customer(
    message,
    user_id,
):

    customer_id = user_id

    if customer_id in DATA["customers"]:

        await show_customer_profile(
            message,
            customer_id,
            user_id,
        )

        return

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
        "👤 ثبت مشخصات من\n\n"
        "لطفاً نام و نام خانوادگی را وارد کنید:",
        user_id=user_id,
    )


# =========================================================
# شماره تلفن و لوکیشن
# =========================================================

def phone_keyboard():

    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton(
                    "📱 ارسال شماره تلفن",
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def location_keyboard():

    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton(
                    "📍 ارسال لوکیشن فعلی",
                    request_location=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# =========================================================
# آدرس‌ها
# =========================================================

def address_list_keyboard(
    customer_id,
    back_callback=None,
):

    buttons = []

    customer = DATA["customers"].get(
        customer_id,
        {},
    )

    addresses = customer.get(
        "addresses",
        [],
    )

    for index, address in enumerate(
        addresses
    ):

        buttons.append([
            InlineKeyboardButton(
                text=(
                    f"📍 "
                    f"{address.get('title', 'آدرس')}"
                ),
                callback_data=(
                    f"select_address_"
                    f"{customer_id}_{index}"
                ),
            )
        ])

    add_callback = (
        f"add_address_order_{customer_id}"
        if back_callback == "delivery"
        else f"add_address_{customer_id}"
    )

    buttons.append([
        InlineKeyboardButton(
            "➕ افزودن آدرس",
            callback_data=add_callback,
        )
    ])

    if back_callback is None:
        back_callback = f"profile_{customer_id}"

    buttons.append([
        InlineKeyboardButton(
            "⬅️ بازگشت",
            callback_data=back_callback,
        )
    ])

    return InlineKeyboardMarkup(buttons)


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
        user_id = str(message.from_user.id)

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


# =========================================================
# شروع ثبت آدرس جدید
# =========================================================

async def start_new_address(
    message,
    user_id,
    customer_id,
    context="profile",
):

    if customer_id not in DATA["customers"]:

        user_states[user_id] = None

        await send_screen(
            message,
            "❌ مشتری پیدا نشد.",
            user_id=user_id,
        )

        return

    active_customer[user_id] = customer_id

    user_states[user_id] = {
        "type": "address_location",
        "customer_id": customer_id,
        "context": context,
    }

    await send_screen(
        message,
        "📍 ثبت آدرس جدید\n\n"
        "لطفاً لوکیشن آدرس موردنظر را "
        "با دکمه زیر ارسال کنید:",
        components=location_keyboard(),
        user_id=user_id,
    )


def address_management_keyboard(
    customer_id,
    index,
    back_callback,
):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🛒 انتخاب این آدرس",
                callback_data=(
                    f"use_address_"
                    f"{customer_id}_{index}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "✏️ اصلاح آدرس",
                callback_data=(
                    f"edit_address_"
                    f"{customer_id}_{index}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 حذف آدرس",
                callback_data=(
                    f"delete_address_"
                    f"{customer_id}_{index}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data=back_callback,
            )
        ],
    ])


# =========================================================
# تحویل
# =========================================================

def delivery_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🚶 تحویل حضوری",
                callback_data="delivery_pickup",
            )
        ],
        [
            InlineKeyboardButton(
                "📍 آدرس‌های من",
                callback_data="delivery_saved",
            )
        ],
        [
            InlineKeyboardButton(
                "➕ افزودن آدرس جدید",
                callback_data="delivery_new_address",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="cart",
            )
        ],
    ])


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

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🚕 الوپیک",
                callback_data="shipping_alopik",
            )
        ],
        [
            InlineKeyboardButton(
                "🛵 اسنپ‌باکس",
                callback_data="shipping_snapp",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="delivery_saved",
            )
        ],
    ])


# =========================================================
# فاکتور نهایی
# =========================================================

def final_invoice_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💳 پرداخت",
                callback_data="payment",
            )
        ],
        [
            InlineKeyboardButton(
                "✏️ اصلاح کالاهای انتخاب‌شده",
                callback_data="edit_cart",
            )
        ],
        [
            InlineKeyboardButton(
                "➕ ادامه خرید",
                callback_data="shop",
            )
        ],
        [
            InlineKeyboardButton(
                "❌ لغو خرید",
                callback_data="cancel_cart",
            )
        ],
    ])


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

    subtotal = cart_total(
        user_id
    )

    fee = delivery_fee(
        delivery
    )

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
            product["price"]
            * quantity
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
# ارسال رسید به مدیر
# =========================================================

async def send_receipt_to_admin(
    message,
    order_number,
    user_id,
    order,
):

    try:

        if not message.photo:

            logging.error(
                f"❌ رسید سفارش #{order_number}: "
                f"عکس وجود ندارد."
            )

            return False

        if not ADMIN_CHAT_IDS:

            logging.error(
                "❌ TELEGRAM_ADMIN_CHAT_IDS تنظیم نشده است."
            )

            return False

        photo = message.photo[-1]

        caption = (
            "📸 رسید پرداخت دریافت شد.\n\n"
            f"🔢 سفارش: #{order_number}\n"
            f"🆔 Telegram ID: {user_id}"
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

        success_count = 0

        for admin_id in ADMIN_CHAT_IDS:

            try:

                await message.get_bot().send_photo(
                    chat_id=int(
                        str(admin_id).strip()
                    ),
                    photo=photo.file_id,
                    caption=caption,
                )

                logging.info(
                    f"✅ رسید سفارش #{order_number} "
                    f"برای مدیر {admin_id} ارسال شد."
                )

                success_count += 1

            except Exception as e:

                logging.exception(
                    f"❌ ارسال رسید سفارش "
                    f"#{order_number} به مدیر "
                    f"{admin_id} ناموفق بود: {e}"
                )

        return success_count > 0

    except Exception as e:

        logging.exception(
            f"❌ خطای کلی ارسال رسید "
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

    subtotal = cart_total(
        user_id
    )

    fee = delivery_fee(
        delivery
    )

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
        "latitude": delivery.get(
            "latitude"
        ),
        "longitude": delivery.get(
            "longitude"
        ),
        "shipping_method": delivery.get(
            "shipping_method",
            "",
        ),
        "payment_status": "در انتظار پرداخت",
        "receipt": "",
    }

    DATA["orders"].append(
        order
    )

    save_data()

    payment_text = (
        "🎉 سفارش شما ثبت شد.\n\n"
        f"🔢 شماره سفارش: "
        f"#{order_number}\n"
        f"💳 مبلغ قابل پرداخت: "
        f"{money(total)}\n\n"
        "لطفاً مبلغ بالا را به شماره کارت "
        "زیر واریز کنید:\n\n"
        f"💳 {PAYMENT_CARD}\n"
        f"👤 به نام: {PAYMENT_OWNER}\n"
        "\n📸 سپس تصویر رسید پرداخت را "
        "ارسال کنید."
    )

    user_states[user_id] = {
        "type": "payment_receipt",
        "order_number": order_number,
    }

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
    # اطلاع مدیر
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
        f"🆔 Telegram ID: {user_id}"
    )

    bot = message.get_bot()

    for admin_id in ADMIN_CHAT_IDS:

        try:

            admin_id_int = int(
                str(admin_id).strip()
            )

            await bot.send_message(
                chat_id=admin_id_int,
                text=admin_text,
            )

            if (
                order.get("latitude")
                is not None
                and order.get("longitude")
                is not None
            ):

                await bot.send_location(
                    chat_id=admin_id_int,
                    latitude=order["latitude"],
                    longitude=order["longitude"],
                )

        except Exception as e:

            logging.error(
                f"ارسال سفارش به مدیر "
                f"{admin_id} ناموفق بود: {e}"
            )


# =========================================================
# پیام‌های کاربر
# =========================================================

async def on_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    user_id = str(
        update.effective_user.id
    )

    print(
        "=" * 60,
        flush=True,
    )

    print(
        "🔎 TELEGRAM MESSAGE RECEIVED",
        flush=True,
    )

    print(
        f"👤 USER_ID: {user_id}",
        flush=True,
    )

    print(
        f"💬 CONTENT: {message.text}",
        flush=True,
    )

    print(
        "=" * 60,
        flush=True,
    )

    # =====================================================
    # لوکیشن
    # =====================================================

    if message.location:

        latitude = float(
            message.location.latitude
        )

        longitude = float(
            message.location.longitude
        )

        state = user_states.get(
            user_id
        )

        # -------------------------------------------------
        # لوکیشن آدرس جدید
        # -------------------------------------------------

        if (
            isinstance(state, dict)
            and state.get("type")
            == "address_location"
        ):

            customer_id = state[
                "customer_id"
            ]

            context_type = state.get(
                "context",
                "profile",
            )

            if customer_id not in DATA["customers"]:

                user_states[user_id] = None

                await send_screen(
                    message,
                    "❌ مشتری پیدا نشد.",
                    user_id=user_id,
                )

                return

            user_states[user_id] = {
                "type": "address_title_after_location",
                "customer_id": customer_id,
                "context": context_type,
                "latitude": latitude,
                "longitude": longitude,
            }

            await send_screen(
                message,
                "📍 لوکیشن دریافت شد.\n\n"
                "✏️ حالا یک نام برای این آدرس وارد کنید.\n\n"
                "مثلاً: خانه، محل کار، فروشگاه",
                user_id=user_id,
            )

            return

        # -------------------------------------------------
        # اصلاح لوکیشن
        # -------------------------------------------------

        if (
            isinstance(state, dict)
            and state.get("type")
            == "edit_address_location"
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

                await send_screen(
                    message,
                    "❌ مشتری پیدا نشد.",
                    user_id=user_id,
                )

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

                await send_screen(
                    message,
                    "❌ آدرس پیدا نشد.",
                    user_id=user_id,
                )

                return

            addresses[index].update(
                {
                    "address": "لوکیشن ثبت‌شده",
                    "latitude": latitude,
                    "longitude": longitude,
                }
            )

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

    # =====================================================
    # رسید پرداخت
    # =====================================================

    state = user_states.get(
        user_id
    )

    if (
        isinstance(state, dict)
        and state.get("type")
        == "payment_receipt"
    ):

        order_number = state.get(
            "order_number"
        )

        if message.photo:

            order = find_order(
                user_id,
                order_number,
            )

            if not order:

                await send_screen(
                    message,
                    "❌ سفارش پیدا نشد.\n\n"
                    "لطفاً با پشتیبانی تماس بگیرید.",
                    user_id=user_id,
                )

                return

            sent = await send_receipt_to_admin(
                message,
                order_number,
                user_id,
                order,
            )

            if sent:

                order["receipt"] = (
                    message.photo[-1].file_id
                )

                order["payment_status"] = (
                    "رسید ارسال شد"
                )

                order["receipt_received_at"] = (
                    now_text()
                )

                save_data()

                user_states[user_id] = None

                await send_screen(
                    message,
                    "✅ رسید پرداخت شما دریافت شد.\n\n"
                    f"شماره سفارش: #{order_number}\n\n"
                    "رسید برای مدیریت ارسال شد و "
                    "پس از بررسی پرداخت، سفارش شما "
                    "آماده خواهد شد. 🌿",
                    user_id=user_id,
                )

            else:

                await send_screen(
                    message,
                    "⚠️ عکس رسید دریافت شد، "
                    "اما ارسال آن برای مدیریت "
                    "ناموفق بود.\n\n"
                    "لطفاً چند لحظه بعد دوباره "
                    "همین رسید را ارسال کنید.",
                    user_id=user_id,
                )

            return

        await send_screen(
            message,
            "📸 لطفاً تصویر رسید پرداخت را "
            "به صورت عکس ارسال کنید.",
            user_id=user_id,
        )

        return

    # =====================================================
    # شماره تلفن
    # =====================================================

    if message.contact:

        phone = message.contact.phone_number

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

        await send_screen(
            message,
            "✅ شماره تلفن ثبت شد.",
            user_id=user_id,
        )

        await show_delivery(
            message,
            user_id,
        )

        return

    # =====================================================
    # متن
    # =====================================================

    if not message.text:
        return

    text = message.text.strip()

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

        await send_screen(
            message,
            "✅ شماره تلفن ثبت شد.",
            user_id=user_id,
        )

        await show_delivery(
            message,
            user_id,
        )

        return

    # =====================================================
    # نام آدرس بعد از لوکیشن
    # =====================================================

    if (
        isinstance(state, dict)
        and state.get("type")
        == "address_title_after_location"
    ):

        customer_id = state[
            "customer_id"
        ]

        context_type = state.get(
            "context",
            "profile",
        )

        latitude = state[
            "latitude"
        ]

        longitude = state[
            "longitude"
        ]

        title = text.strip()

        if not title:

            await send_screen(
                message,
                "⚠️ نام آدرس نمی‌تواند خالی باشد.\n\n"
                "مثلاً: خانه، محل کار، فروشگاه",
                user_id=user_id,
            )

            return

        if customer_id not in DATA["customers"]:

            user_states[user_id] = None

            await send_screen(
                message,
                "❌ مشتری پیدا نشد.",
                user_id=user_id,
            )

            return

        customer = DATA["customers"][
            customer_id
        ]

        customer.setdefault(
            "addresses",
            [],
        )

        customer["addresses"].append(
            {
                "title": title,
                "address": "لوکیشن ثبت‌شده",
                "latitude": latitude,
                "longitude": longitude,
            }
        )

        save_data()

        user_states[user_id] = None

        active_customer[user_id] = (
            customer_id
        )

        if context_type == "profile":

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

        if context_type == "order":

            current_delivery[user_id] = {
                "title": title,
                "address": "لوکیشن ثبت‌شده",
                "latitude": latitude,
                "longitude": longitude,
                "fee": 0,
            }

            await show_shipping_or_invoice(
                message,
                user_id,
            )

            return

    # =====================================================
    # اگر در حالت لوکیشن متن فرستاد
    # =====================================================

    if (
        isinstance(state, dict)
        and state.get("type")
        == "address_location"
    ):

        await send_screen(
            message,
            "📍 لطفاً لوکیشن را با دکمه زیر ارسال کنید.",
            components=location_keyboard(),
            user_id=user_id,
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
            "type": "edit_address_location",
            "customer_id": customer_id,
            "index": index,
        }

        save_data()

        await send_screen(
            message,
            "📍 لوکیشن جدید را با دکمه زیر ارسال کنید:",
            components=location_keyboard(),
            user_id=user_id,
        )

        return

    # =====================================================
    # اصلاح متن آدرس قدیمی
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

async def on_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user_id = str(
        query.from_user.id
    )

    data = query.data or ""

    try:
        await query.answer()
    except Exception:
        pass

    # =====================================================
    # صفحه اول
    # =====================================================

    if data == "home":

        user_states[user_id] = None

        await show_home(
            query.message,
            user_id,
        )

        return

    # =====================================================
    # خریدهای قبلی
    # =====================================================

    if data == "previous_orders":

        user_states[user_id] = None

        await show_previous_orders(
            query.message,
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
            query.message,
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
            query.message,
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
            query,
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
            query,
            f"🌿 {product['name']}\n\n"
            f"📦 {product['size']}\n"
            f"💰 {money(product['price'])}",
            components=product_keyboard(
                product_id
            ),
        )

        return

    # =====================================================
    # افزودن به سبد
    # =====================================================

    if (
        data.startswith("add_")
        and not data.startswith("add_address_")
    ):

        product_id = data[
            len("add_"):
        ]

        product = PRODUCTS.get(
            product_id
        )

        if not product:
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
            query.message,
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
            query.message,
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

            if (
                carts[user_id][product_id]
                <= 0
            ):

                del carts[user_id][
                    product_id
                ]

        await show_cart(
            query.message,
            user_id,
        )

        return

    # =====================================================
    # سبد
    # =====================================================

    if data == "cart":

        await show_cart(
            query.message,
            user_id,
        )

        return

    # =====================================================
    # شروع سفارش
    # =====================================================

    if data == "start_order":

        await start_order(
            query.message,
            user_id,
        )

        return

    # =====================================================
    # ثبت مشخصات
    # =====================================================

    if data == "new_customer":

        await start_new_customer(
            query.message,
            user_id,
        )

        return

    # =====================================================
    # نمایش مشخصات
    # =====================================================

    if data == "customer_start":

        await show_customer_start(
            query.message,
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
            query.message,
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

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "👤 اصلاح نام",
                    callback_data=(
                        f"edit_name_{customer_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "📱 اصلاح شماره",
                    callback_data=(
                        f"edit_phone_{customer_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data=(
                        f"profile_{customer_id}"
                    ),
                )
            ],
        ])

        await send_screen_callback(
            query,
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
            query,
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
            query,
            "📱 شماره تلفن جدید را وارد کنید:",
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
            query.message,
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
                query.message,
                user_id,
            )

            return

        await show_addresses(
            query.message,
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
            query.message,
            customer_id,
            back_callback="delivery",
            user_id=user_id,
        )

        return

    # =====================================================
    # افزودن آدرس از سفارش
    # =====================================================

    if data.startswith(
        "add_address_order_"
    ):

        customer_id = data[
            len("add_address_order_"):
        ]

        if customer_id != user_id:
            return

        await start_new_address(
            query.message,
            user_id,
            customer_id,
            context="order",
        )

        return

    # =====================================================
    # افزودن آدرس از پروفایل
    # =====================================================

    if data.startswith(
        "add_address_"
    ):

        customer_id = data[
            len("add_address_"):
        ]

        if customer_id != user_id:
            return

        await start_new_address(
            query.message,
            user_id,
            customer_id,
            context="profile",
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

        back_callback = (
            f"addresses_profile_{customer_id}"
        )

        await send_screen_callback(
            query,
            f"📍 "
            f"{address.get('title', 'آدرس')}\n\n"
            f"🏠 {address.get('address', '')}"
            + (
                f"\n🌐 مختصات: "
                f"{address.get('latitude')}, "
                f"{address.get('longitude')}"
                if address.get("latitude") is not None
                else ""
            ),
            components=address_management_keyboard(
                customer_id,
                index,
                back_callback,
            ),
        )

        return

    # =====================================================
    # انتخاب آدرس برای سفارش
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
                "لوکیشن ثبت‌شده",
            ),
            "latitude": address.get(
                "latitude"
            ),
            "longitude": address.get(
                "longitude"
            ),
            "fee": 0,
        }

        await show_shipping_or_invoice(
            query.message,
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
            query,
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
            query.message,
            customer_id,
            back_callback=(
                f"addresses_profile_"
                f"{customer_id}"
            ),
            user_id=user_id,
        )

        return

    # =====================================================
    # تحویل
    # =====================================================

    if data == "delivery":

        await show_delivery(
            query.message,
            user_id,
        )

        return

    # =====================================================
    # تحویل حضوری
    # =====================================================

    if data == "delivery_pickup":

        current_delivery[user_id] = {
            "title": "تحویل حضوری",
            "address": "",
            "fee": 0,
        }

        await show_final_invoice(
            query.message,
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
                query.message,
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

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "➕ افزودن آدرس",
                        callback_data=(
                            f"add_address_order_"
                            f"{customer_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ بازگشت",
                        callback_data="delivery",
                    )
                ],
            ])

            await send_screen_callback(
                query,
                "📍 آدرس‌های من\n\n"
                "هنوز آدرسی برای شما "
                "ثبت نشده است.\n\n"
                "برای ثبت آدرس جدید روی "
                "گزینه زیر بزنید.",
                components=keyboard,
            )

            return

        await show_addresses(
            query.message,
            customer_id,
            back_callback="delivery",
            user_id=user_id,
        )

        return

    # =====================================================
    # آدرس جدید از سفارش
    # =====================================================

    if data == "delivery_new_address":

        customer_id = active_customer.get(
            user_id
        )

        if not customer_id:

            await show_customer_start(
                query.message,
                user_id,
            )

            return

        await start_new_address(
            query.message,
            user_id,
            customer_id,
            context="order",
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
            query.message,
            user_id,
        )

        return

    # =====================================================
    # اسنپ
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
            query.message,
            user_id,
        )

        return

    # =====================================================
    # اصلاح سبد
    # =====================================================

    if data == "edit_cart":

        await show_cart(
            query.message,
            user_id,
        )

        return

    # =====================================================
    # پرداخت
    # =====================================================

    if data == "payment":

        await create_order(
            query.message,
            user_id,
        )

        return

    # =====================================================
    # لغو خرید
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
            query.message,
            user_id,
        )

        return


# =========================================================
# روش ارسال برای آدرس
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
# /start
# =========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = str(
        update.effective_user.id
    )

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
        update.effective_message,
        user_id,
    )


# =========================================================
# اجرا
# =========================================================

def main():

    print(
        "=== TELEGRAM BOT STARTING ===",
        flush=True,
    )

    print(
        "SabziU Telegram Store is starting...",
        flush=True,
    )

    print(
        f"ADMIN_CHAT_IDS: {ADMIN_CHAT_IDS}",
        flush=True,
    )

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            on_callback,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.ALL
            & ~filters.COMMAND,
            on_message,
        )
    )

    print(
        "=== TELEGRAM BOT READY ===",
        flush=True,
    )

    application.run_polling()


if __name__ == "__main__":
    main()
