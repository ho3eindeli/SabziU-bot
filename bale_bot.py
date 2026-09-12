import os
import json
import logging
from datetime import datetime

from bale import (
    Bot,
    Message,
    CallbackQuery,
    Location,
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

PAYMENT_CARD = "6219861967021642"

PAYMENT_OWNER = os.getenv(
    "BALE_PAYMENT_OWNER",
    "",
)

STATE_FILE = "bale_data.json"


if not TOKEN:
    raise RuntimeError(
        "BALE_BOT_TOKEN تنظیم نشده است."
    )


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
            message.author.user_id
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

        new_message = await message.reply(
            text,
            components=components,
        )

        last_bot_message[user_id] = (
            new_message
        )

        return new_message

    except Exception as e:

        logging.error(
            f"ارسال صفحه ناموفق بود: {e}"
        )

        try:

            new_message = await bot.send_message(
                chat_id=int(user_id),
                text=text,
                components=components,
            )

            last_bot_message[user_id] = (
                new_message
            )

            return new_message

        except Exception as e2:

            logging.error(
                f"ارسال مستقیم صفحه ناموفق بود: {e2}"
            )

            return None


async def send_screen_callback(
    callback,
    text,
    components=None,
):

    user_id = str(
        callback.from_user.user_id
    )

    callback_message = callback.message

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

        if hasattr(
            callback,
            "answer",
        ):

            await callback.answer()

    except Exception:

        pass

    try:

        new_message = await callback_message.reply(
            text,
            components=components,
        )

        last_bot_message[user_id] = (
            new_message
        )

        return new_message

    except Exception as e:

        logging.error(
            f"ارسال صفحه callback ناموفق بود: {e}"
        )

        try:

            new_message = await bot.send_message(
                chat_id=int(user_id),
                text=text,
                components=components,
            )

            last_bot_message[user_id] = (
                new_message
            )

            return new_message

        except Exception as e2:

            logging.error(
                f"ارسال مستقیم callback ناموفق بود: {e2}"
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
        "name": "ترشی نازخاتون",
        "category": "pickles",
        "size": "500 گرم",
        "price": 300000,
        "image": "",
        "active": True,
    },

    "pickle_5": {
        "name": "ترشی لیته",
        "category": "pickles",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "pickle_6": {
        "name": "ترشی مخلوط",
        "category": "pickles",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "pickle_7": {
        "name": "ترشی سیر",
        "category": "pickles",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "pickle_8": {
        "name": "ترشی فلفل",
        "category": "pickles",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "pickle_9": {
        "name": "خیارشور",
        "category": "pickles",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },

    "pickle_10": {
        "name": "زیتون پرورده",
        "category": "pickles",
        "size": "500 گرم",
        "price": 350000,
        "image": "",
        "active": True,
    },

    "syrup_1": {
        "name": "شربت آلبالو",
        "category": "syrup",
        "size": "1 لیتر",
        "price": 350000,
        "image": "",
        "active": True,
    },

    "syrup_2": {
        "name": "شربت به‌لیمو",
        "category": "syrup",
        "size": "1 لیتر",
        "price": 350000,
        "image": "",
        "active": True,
    },

    "syrup_3": {
        "name": "شربت سکنجبین",
        "category": "syrup",
        "size": "1 لیتر",
        "price": 350000,
        "image": "",
        "active": True,
    },

    "syrup_4": {
        "name": "شربت نعناع",
        "category": "syrup",
        "size": "1 لیتر",
        "price": 350000,
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
        "name": "مربای به",
        "category": "jam",
        "size": "500 گرم",
        "price": 300000,
        "image": "",
        "active": True,
    },

    "jam_3": {
        "name": "مربای هویج",
        "category": "jam",
        "size": "500 گرم",
        "price": 300000,
        "image": "",
        "active": True,
    },

    "spice_1": {
        "name": "سبزی خشک آش",
        "category": "spices",
        "size": "100 گرم",
        "price": 150000,
        "image": "",
        "active": True,
    },

    "spice_2": {
        "name": "سبزی خشک قورمه",
        "category": "spices",
        "size": "100 گرم",
        "price": 150000,
        "image": "",
        "active": True,
    },

    "spice_3": {
        "name": "نعناع خشک",
        "category": "spices",
        "size": "100 گرم",
        "price": 150000,
        "image": "",
        "active": True,
    },

    "condiment_1": {
        "name": "رب گوجه خانگی",
        "category": "condiments",
        "size": "500 گرم",
        "price": 250000,
        "image": "",
        "active": True,
    },
}


# =========================================================
# کیبوردها
# =========================================================

def main_menu_keyboard():

    return MenuKeyboardMarkup(
        keyboard=[
            [
                MenuKeyboardButton("🛍 فروشگاه"),
                MenuKeyboardButton("👤 مشخصات من"),
            ],
            [
                MenuKeyboardButton("🛒 سبد خرید"),
                MenuKeyboardButton("📦 سفارش‌های من"),
            ],
        ],
        resize_keyboard=True,
    )


def categories_keyboard():

    rows = [
        [
            InlineKeyboardButton(
                text="🥘 سرخ‌شده‌ها",
                callback_data="category_fried",
            ),
            InlineKeyboardButton(
                text="🥬 تازه و آماده پخت",
                callback_data="category_raw",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🥒 ترشی و شور",
                callback_data="category_pickles",
            ),
            InlineKeyboardButton(
                text="🥤 شربت‌ها",
                callback_data="category_syrup",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🍓 مرباها",
                callback_data="category_jam",
            ),
            InlineKeyboardButton(
                text="🌿 ادویه و خشکبار",
                callback_data="category_spices",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🍅 رب و چاشنی",
                callback_data="category_condiments",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⬅️ بازگشت",
                callback_data="home",
            )
        ],
    ]

    return InlineKeyboardMarkup(
        keyboard=rows
    )


def product_list_keyboard(category):

    rows = []

    for product_id, product in PRODUCTS.items():

        if (
            product["active"]
            and product["category"] == category
        ):

            rows.append([
                InlineKeyboardButton(
                    text=(
                        f"{product['name']} | "
                        f"{product['size']} | "
                        f"{money(product['price'])}"
                    ),
                    callback_data=f"product_{product_id}",
                )
            ])

    rows.append([
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="shop",
        )
    ])

    return InlineKeyboardMarkup(
        keyboard=rows
    )


def product_keyboard(product_id, user_id):

    quantity = carts.get(
        user_id,
        {},
    ).get(
        product_id,
        0,
    )

    return InlineKeyboardMarkup(
        keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ افزودن",
                    callback_data=f"add_{product_id}",
                ),
                InlineKeyboardButton(
                    text=f"تعداد: {quantity}",
                    callback_data="noop",
                ),
                InlineKeyboardButton(
                    text="➖ کاستن",
                    callback_data=f"remove_{product_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🛒 سبد خرید",
                    callback_data="cart",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ بازگشت به محصولات",
                    callback_data=(
                        f"category_{PRODUCTS[product_id]['category']}"
                    ),
                )
            ],
        ]
    )


def cart_keyboard(user_id):

    rows = []

    for product_id, quantity in carts.get(
        user_id,
        {},
    ).items():

        product = PRODUCTS.get(
            product_id
        )

        if not product or quantity <= 0:
            continue

        rows.append([
            InlineKeyboardButton(
                text=f"➕ افزودن {product['name']}",
                callback_data=f"add_{product_id}",
            ),
            InlineKeyboardButton(
                text=f"{quantity} عدد",
                callback_data="noop",
            ),
            InlineKeyboardButton(
                text=f"➖ کاستن {product['name']}",
                callback_data=f"remove_{product_id}",
            ),
        ])

    if carts.get(user_id):

        rows.append([
            InlineKeyboardButton(
                text="💳 ادامه ثبت سفارش",
                callback_data="checkout",
            )
        ])

    rows.append([
        InlineKeyboardButton(
            text="🛍 ادامه خرید",
            callback_data="shop",
        )
    ])

    rows.append([
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="home",
        )
    ])

    return InlineKeyboardMarkup(
        keyboard=rows
    )


def customer_start_keyboard(user_id):

    customer = get_user_customer(
        user_id
    )

    if customer:

        return InlineKeyboardMarkup(
            keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ اصلاح مشخصات",
                        callback_data=f"edit_customer_{user_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📍 مدیریت آدرس‌ها",
                        callback_data=f"addresses_{user_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ بازگشت",
                        callback_data="home",
                    )
                ],
            ]
        )

    return InlineKeyboardMarkup(
        keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 ثبت مشخصات",
                    callback_data="new_customer",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ بازگشت",
                    callback_data="home",
                )
            ],
        ]
    )


def customer_profile_keyboard(user_id):

    return InlineKeyboardMarkup(
        keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ اصلاح مشخصات",
                    callback_data=f"edit_customer_{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📍 مدیریت آدرس‌ها",
                    callback_data=f"addresses_{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ بازگشت",
                    callback_data="customer_start",
                )
            ],
        ]
    )


def edit_customer_keyboard(user_id):

    return InlineKeyboardMarkup(
        keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ نام",
                    callback_data=f"edit_name_{user_id}",
                ),
                InlineKeyboardButton(
                    text="📱 شماره موبایل",
                    callback_data=f"edit_phone_{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ بازگشت",
                    callback_data=f"profile_{user_id}",
                )
            ],
        ]
    )


def address_list_keyboard(
    user_id,
    back_callback="profile",
):

    customer = get_user_customer(
        user_id
    )

    addresses = customer.get(
        "addresses",
        [],
    ) if customer else []

    rows = []

    for index, address in enumerate(
        addresses
    ):

        title = address.get(
            "title",
            f"آدرس {index + 1}",
        )

        rows.append([
            InlineKeyboardButton(
                text=f"📍 {title}",
                callback_data=(
                    f"address_{user_id}_{index}"
                ),
            )
        ])

    add_callback = (
        f"add_address_order_{user_id}"
        if back_callback == "delivery"
        else f"add_address_{user_id}"
    )

    rows.append([
        InlineKeyboardButton(
            text="➕ افزودن آدرس",
            callback_data=add_callback,
        )
    ])

    rows.append([
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data=back_callback,
        )
    ])

    return InlineKeyboardMarkup(
        keyboard=rows
    )


def address_detail_keyboard(
    user_id,
    index,
):

    return InlineKeyboardMarkup(
        keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ انتخاب این آدرس",
                    callback_data=(
                        f"select_address_{user_id}_{index}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ ویرایش",
                    callback_data=(
                        f"edit_address_{user_id}_{index}"
                    ),
                ),
                InlineKeyboardButton(
                    text="🗑 حذف",
                    callback_data=(
                        f"delete_address_{user_id}_{index}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ بازگشت",
                    callback_data=f"addresses_{user_id}",
                )
            ],
        ]
    )


def delivery_keyboard():

    return InlineKeyboardMarkup(
        keyboard=[
            [
                InlineKeyboardButton(
                    text="🚶 تحویل حضوری",
                    callback_data="delivery_pickup",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏛 هیأت امنا",
                    callback_data="delivery_heiat",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📍 ارسال با لوکیشن",
                    callback_data="delivery_location",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ بازگشت",
                    callback_data="cart",
                )
            ],
        ]
    )


def order_confirm_keyboard():

    return InlineKeyboardMarkup(
        keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ تأیید و پرداخت",
                    callback_data="confirm_order",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ بازگشت",
                    callback_data="delivery",
                )
            ],
        ]
    )


def orders_keyboard(user_id):

    orders = [
        order
        for order in DATA["orders"]
        if str(order.get("user_id"))
        == str(user_id)
    ]

    rows = []

    for order in reversed(orders):

        number = order.get(
            "order_number",
            "-",
        )

        rows.append([
            InlineKeyboardButton(
                text=f"📦 سفارش #{number}",
                callback_data=f"order_{number}",
            )
        ])

    rows.append([
        InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="home",
        )
    ])

    return InlineKeyboardMarkup(
        keyboard=rows
    )


def receipt_keyboard():

    return InlineKeyboardMarkup(
        keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="cancel_order",
                )
            ]
        ]
    )


# =========================================================
# مشتری
# =========================================================

def get_user_customer(user_id):

    return DATA["customers"].get(
        str(user_id)
    )


async def show_customer_start(
    message,
    user_id=None,
):

    if user_id is None:
        user_id = str(message.author.user_id)

    customer = get_user_customer(
        user_id
    )

    if customer:

        await show_customer_profile(
            message,
            user_id,
        )

        return

    await send_screen(
        message,
        "👤 مشخصات من\n\n"
        "هنوز مشخصات شما ثبت نشده است.",
        customer_start_keyboard(user_id),
        user_id,
    )


async def show_customer_profile(
    message,
    user_id,
):

    customer = get_user_customer(
        user_id
    )

    if not customer:

        await show_customer_start(
            message,
            user_id,
        )

        return

    active_customer[user_id] = user_id

    name = customer.get(
        "name",
        "",
    ) or "ثبت نشده"

    phone = customer.get(
        "phone",
        "",
    ) or "ثبت نشده"

    addresses = customer.get(
        "addresses",
        [],
    )

    text = (
        "👤 مشخصات من\n\n"
        f"نام: {name}\n"
        f"شماره موبایل: {phone}\n"
        f"تعداد آدرس‌های ثبت‌شده: {len(addresses)}"
    )

    await send_screen(
        message,
        text,
        customer_profile_keyboard(user_id),
        user_id,
    )


async def start_new_customer(
    message,
    user_id,
):

    customer_id = str(user_id)

    if get_user_customer(user_id):

        await show_customer_profile(
            message,
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
        "state": "new_customer_name",
    }

    save_data()

    await send_screen(
        message,
        "📝 ثبت مشخصات\n\n"
        "لطفاً نام و نام خانوادگی خود را ارسال کنید.",
        None,
        user_id,
    )


# =========================================================
# آدرس‌ها
# =========================================================

async def show_addresses(
    message,
    user_id,
    back_callback="profile",
):

    customer = get_user_customer(
        user_id
    )

    if not customer:

        await show_customer_start(
            message,
            user_id,
        )

        return

    addresses = customer.get(
        "addresses",
        [],
    )

    if addresses:

        text = (
            "📍 آدرس‌های من\n\n"
            "آدرس موردنظر را انتخاب کنید:"
        )

    else:

        text = (
            "📍 آدرس‌های من\n\n"
            "هنوز آدرسی ثبت نشده است."
        )

    await send_screen(
        message,
        text,
        address_list_keyboard(
            user_id,
            back_callback,
        ),
        user_id,
    )


async def show_address_detail(
    message,
    user_id,
    index,
):

    customer = get_user_customer(
        user_id
    )

    if not customer:
        return

    addresses = customer.get(
        "addresses",
        [],
    )

    if index < 0 or index >= len(addresses):
        return

    address = addresses[index]

    title = address.get(
        "title",
        f"آدرس {index + 1}",
    )

    text = (
        "📍 جزئیات آدرس\n\n"
        f"عنوان: {title}\n"
        "آدرس: لوکیشن ثبت‌شده"
    )

    await send_screen(
        message,
        text,
        address_detail_keyboard(
            user_id,
            index,
        ),
        user_id,
    )


async def start_new_address(
    message,
    user_id,
    context="profile",
):

    if not get_user_customer(user_id):
        return

    user_states[user_id] = {
        "state": "new_address_location",
        "context": context,
    }

    await send_screen(
        message,
        "📍 ثبت آدرس جدید\n\n"
        "ابتدا لوکیشن آدرس را ارسال کنید.",
        None,
        user_id,
    )


async def start_edit_address(
    message,
    user_id,
    index,
):

    customer = get_user_customer(
        user_id
    )

    if not customer:
        return

    addresses = customer.get(
        "addresses",
        [],
    )

    if index < 0 or index >= len(addresses):
        return

    user_states[user_id] = {
        "state": "edit_address_title",
        "index": index,
    }

    current_title = addresses[index].get(
        "title",
        f"آدرس {index + 1}",
    )

    await send_screen(
        message,
        "✏️ ویرایش آدرس\n\n"
        f"عنوان فعلی: {current_title}\n\n"
        "عنوان جدید را ارسال کنید.",
        None,
        user_id,
    )


# =========================================================
# نمایش فروشگاه و سفارش
# =========================================================

async def show_home(
    message,
    user_id=None,
):

    if user_id is None:
        user_id = str(message.author.user_id)

    await send_screen(
        message,
        "🌿 به سبزی‌یو خوش آمدید.\n\n"
        "محصول موردنظر خود را انتخاب کنید.",
        main_menu_keyboard(),
        user_id,
    )


async def show_shop(
    message,
    user_id,
):

    await send_screen(
        message,
        "🛍 فروشگاه\n\n"
        "دسته‌بندی موردنظر را انتخاب کنید:",
        categories_keyboard(),
        user_id,
    )


async def show_category(
    message,
    category,
    user_id,
):

    await send_screen(
        message,
        "🛍 محصولات\n\n"
        "محصول موردنظر را انتخاب کنید:",
        product_list_keyboard(category),
        user_id,
    )


async def show_product(
    message,
    product_id,
    user_id,
):

    product = PRODUCTS.get(product_id)

    if not product:
        return

    quantity = carts.get(
        user_id,
        {},
    ).get(
        product_id,
        0,
    )

    text = (
        f"🥘 {product['name']}\n\n"
        f"وزن: {product['size']}\n"
        f"قیمت: {money(product['price'])}\n"
        f"تعداد در سبد: {quantity}"
    )

    await send_screen(
        message,
        text,
        product_keyboard(
            product_id,
            user_id,
        ),
        user_id,
    )


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
            "🛒 سبد خرید شما خالی است.",
            cart_keyboard(user_id),
            user_id,
        )

        return

    lines = [
        "🛒 سبد خرید",
        "",
    ]

    for product_id, quantity in cart.items():

        product = PRODUCTS.get(
            product_id
        )

        if not product or quantity <= 0:
            continue

        subtotal = (
            product["price"]
            * quantity
        )

        lines.append(
            f"• {product['name']} × {quantity}"
            f" — {money(subtotal)}"
        )

    lines.extend([
        "",
        f"جمع کالاها: {money(cart_total(user_id))}",
    ])

    await send_screen(
        message,
        "\n".join(lines),
        cart_keyboard(user_id),
        user_id,
    )


async def show_delivery(
    message,
    user_id,
):

    if not carts.get(user_id):

        await show_cart(
            message,
            user_id,
        )

        return

    await send_screen(
        message,
        "🚚 روش تحویل را انتخاب کنید:",
        delivery_keyboard(),
        user_id,
    )


async def show_order_preview(
    message,
    user_id,
):

    delivery = current_delivery.get(
        user_id,
        {},
    )

    customer = get_user_customer(
        user_id
    ) or {}

    lines = [
        "🧾 پیش‌فاکتور سفارش",
        "",
        f"نام: {customer.get('name') or 'ثبت نشده'}",
        f"موبایل: {customer.get('phone') or 'ثبت نشده'}",
        "",
    ]

    for product_id, quantity in carts.get(
        user_id,
        {},
    ).items():

        product = PRODUCTS.get(
            product_id
        )

        if not product or quantity <= 0:
            continue

        lines.append(
            f"• {product['name']} × {quantity}"
            f" — {money(product['price'] * quantity)}"
        )

    products_total = cart_total(user_id)
    fee = delivery_fee(delivery)
    total = products_total + fee

    lines.extend([
        "",
        f"جمع کالاها: {money(products_total)}",
        f"هزینه ارسال: {money(fee)}",
        f"مبلغ نهایی: {money(total)}",
        "",
        f"روش تحویل: {delivery.get('title', 'ثبت نشده')}",
    ])

    if delivery.get("title") == "ارسال با لوکیشن":
        lines.append("آدرس: لوکیشن ثبت‌شده")

    await send_screen(
        message,
        "\n".join(lines),
        order_confirm_keyboard(),
        user_id,
    )


async def show_orders(
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

        await send_screen(
            message,
            "📦 سفارش‌های من\n\n"
            "هنوز سفارشی ثبت نکرده‌اید.",
            orders_keyboard(user_id),
            user_id,
        )

        return

    await send_screen(
        message,
        "📦 سفارش‌های من\n\n"
        "سفارش موردنظر را انتخاب کنید:",
        orders_keyboard(user_id),
        user_id,
    )


async def show_order_detail(
    message,
    user_id,
    order_number,
):

    order = find_order(
        user_id,
        order_number,
    )

    if not order:
        return

    lines = [
        f"📦 سفارش #{order.get('order_number')}",
        "",
        f"تاریخ: {order.get('created_at', '-')}",
        f"وضعیت: {order.get('status', '-')}",
        "",
    ]

    for item in order.get("items", []):

        lines.append(
            f"• {item.get('name', '-') } × "
            f"{item.get('quantity', 0)}"
        )

    lines.extend([
        "",
        f"مبلغ: {money(order.get('total', 0))}",
        f"روش تحویل: {order.get('delivery', {}).get('title', '-')}",
    ])

    await send_screen(
        message,
        "\n".join(lines),
        InlineKeyboardMarkup(
            keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ بازگشت",
                        callback_data="orders",
                    )
                ]
            ]
        ),
        user_id,
    )


# =========================================================
# ساخت سفارش و رسید
# =========================================================

async def create_order(
    user_id,
):

    customer = get_user_customer(
        user_id
    )

    delivery = current_delivery.get(
        user_id,
        {},
    )

    if not customer or not carts.get(user_id):
        return None

    order_number = DATA.get(
        "next_order_number",
        1000,
    )

    items = []

    for product_id, quantity in carts.get(
        user_id,
        {},
    ).items():

        product = PRODUCTS.get(
            product_id
        )

        if not product or quantity <= 0:
            continue

        items.append({
            "product_id": product_id,
            "name": product["name"],
            "size": product["size"],
            "price": product["price"],
            "quantity": quantity,
        })

    products_total = sum(
        item["price"] * item["quantity"]
        for item in items
    )

    fee = delivery_fee(delivery)

    order = {
        "order_number": order_number,
        "user_id": str(user_id),
        "customer_id": str(user_id),
        "customer": {
            "name": customer.get("name", ""),
            "phone": customer.get("phone", ""),
        },
        "items": items,
        "products_total": products_total,
        "delivery": dict(delivery),
        "delivery_fee": fee,
        "total": products_total + fee,
        "status": "در انتظار رسید پرداخت",
        "created_at": now_text(),
        "receipt_sent": False,
    }

    DATA["orders"].append(order)
    DATA["next_order_number"] = (
        int(order_number) + 1
    )

    save_data()

    return order


async def send_order_to_admins(
    order,
):

    text_lines = [
        "🆕 سفارش جدید سبزی‌یو",
        "",
        f"شماره سفارش: #{order.get('order_number')}",
        f"نام: {order.get('customer', {}).get('name', '-')}",
        f"موبایل: {order.get('customer', {}).get('phone', '-')}",
        f"تاریخ: {order.get('created_at', '-')}",
        "",
    ]

    for item in order.get("items", []):

        text_lines.append(
            f"• {item.get('name', '-') } × "
            f"{item.get('quantity', 0)}"
            f" — {money(item.get('price', 0) * item.get('quantity', 0))}"
        )

    delivery = order.get(
        "delivery",
        {},
    )

    text_lines.extend([
        "",
        f"جمع کالاها: {money(order.get('products_total', 0))}",
        f"هزینه ارسال: {money(order.get('delivery_fee', 0))}",
        f"مبلغ نهایی: {money(order.get('total', 0))}",
        f"روش تحویل: {delivery.get('title', '-')}",
    ])

    if delivery.get("latitude") is not None:
        text_lines.append(
            "لوکیشن مشتری: ثبت شده"
        )

    text = "\n".join(text_lines)

    for admin_id in ADMIN_CHAT_IDS:

        try:

            await bot.send_message(
                chat_id=int(admin_id),
                text=text,
            )

            if (
                delivery.get("latitude") is not None
                and delivery.get("longitude") is not None
            ):

                try:

                    await bot.send_location(
                        chat_id=int(admin_id),
                        latitude=delivery["latitude"],
                        longitude=delivery["longitude"],
                    )

                except Exception as e:

                    logging.error(
                        f"ارسال لوکیشن به مدیر ناموفق بود: {e}"
                    )

        except Exception as e:

            logging.error(
                f"ارسال سفارش به مدیر {admin_id} ناموفق بود: {e}"
            )


async def ask_for_receipt(
    message,
    user_id,
):

    order = find_order(
        user_id,
        DATA["orders"][-1]["order_number"]
        if DATA["orders"]
        else None,
    )

    if not order:
        return

    user_states[user_id] = {
        "state": "waiting_receipt",
        "order_number": order["order_number"],
    }

    await send_screen(
        message,
        "💳 پرداخت کارت‌به‌کارت\n\n"
        f"شماره کارت:\n{PAYMENT_CARD}\n\n"
        f"به نام: {PAYMENT_OWNER or 'سبزی‌یو'}\n\n"
        "پس از پرداخت، تصویر رسید را ارسال کنید.",
        receipt_keyboard(),
        user_id,
    )


# =========================================================
# Callbackها
# =========================================================

@bot.event
async def on_callback(
    callback: CallbackQuery,
):

    data = callback.data or ""
    user_id = str(
        callback.from_user.user_id
    )

    message = callback.message

    try:
        await callback.answer()
    except Exception:
        pass

    if data == "noop":
        return

    if data == "home":

        await show_home(
            message,
            user_id,
        )

        return

    if data == "shop":

        await show_shop(
            message,
            user_id,
        )

        return

    if data == "cart":

        await show_cart(
            message,
            user_id,
        )

        return

    if data == "checkout":

        await show_delivery(
            message,
            user_id,
        )

        return

    if data == "customer_start":

        await show_customer_start(
            message,
            user_id,
        )

        return

    if data == "new_customer":

        await start_new_customer(
            message,
            user_id,
        )

        return

    if data.startswith("category_"):

        category = data.split(
            "category_",
            1,
        )[1]

        await show_category(
            message,
            category,
            user_id,
        )

        return

    if data.startswith("product_"):

        product_id = data.split(
            "product_",
            1,
        )[1]

        await show_product(
            message,
            product_id,
            user_id,
        )

        return

    if data.startswith("add_") and not data.startswith("add_address_"):

        product_id = data.split(
            "add_",
            1,
        )[1]

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

        await show_product(
            message,
            product_id,
            user_id,
        )

        return

    if data.startswith("remove_"):

        product_id = data.split(
            "remove_",
            1,
        )[1]

        cart = carts.setdefault(
            user_id,
            {},
        )

        if product_id in cart:

            cart[product_id] -= 1

            if cart[product_id] <= 0:
                cart.pop(
                    product_id,
                    None,
                )

        if product_id in PRODUCTS:

            await show_product(
                message,
                product_id,
                user_id,
            )

        else:

            await show_cart(
                message,
                user_id,
            )

        return

    if data.startswith("profile_"):

        target_user_id = data.split(
            "profile_",
            1,
        )[1]

        if target_user_id != user_id:
            return

        await show_customer_profile(
            message,
            user_id,
        )

        return

    if data.startswith("edit_customer_"):

        target_user_id = data.split(
            "edit_customer_",
            1,
        )[1]

        if target_user_id != user_id:
            return

        await send_screen(
            message,
            "✏️ اصلاح مشخصات\n\n"
            "موردی را که می‌خواهید اصلاح کنید انتخاب کنید:",
            edit_customer_keyboard(user_id),
            user_id,
        )

        return

    if data.startswith("edit_name_"):

        target_user_id = data.split(
            "edit_name_",
            1,
        )[1]

        if target_user_id != user_id:
            return

        user_states[user_id] = {
            "state": "edit_name",
        }

        await send_screen(
            message,
            "✏️ اصلاح نام\n\n"
            "نام و نام خانوادگی جدید را ارسال کنید.",
            None,
            user_id,
        )

        return

    if data.startswith("edit_phone_"):

        target_user_id = data.split(
            "edit_phone_",
            1,
        )[1]

        if target_user_id != user_id:
            return

        user_states[user_id] = {
            "state": "edit_phone",
        }

        await send_screen(
            message,
            "📱 اصلاح شماره موبایل\n\n"
            "شماره موبایل جدید را ارسال کنید.",
            None,
            user_id,
        )

        return

    if data.startswith("addresses_"):

        target_user_id = data.split(
            "addresses_",
            1,
        )[1]

        if target_user_id != user_id:
            return

        await show_addresses(
            message,
            user_id,
        )

        return

    if data.startswith("add_address_order_"):

        target_user_id = data.split(
            "add_address_order_",
            1,
        )[1]

        if target_user_id != user_id:
            return

        await start_new_address(
            message,
            user_id,
            context="order",
        )

        return

    if data.startswith("add_address_"):

        target_user_id = data.split(
            "add_address_",
            1,
        )[1]

        if target_user_id != user_id:
            return

        await start_new_address(
            message,
            user_id,
            context="profile",
        )

        return

    if data.startswith("address_"):

        parts = data.split("_")

        if len(parts) != 3:
            return

        target_user_id = parts[1]

        if target_user_id != user_id:
            return

        try:
            index = int(parts[2])
        except ValueError:
            return

        await show_address_detail(
            message,
            user_id,
            index,
        )

        return

    if data.startswith("select_address_"):

        parts = data.split("_")

        if len(parts) != 4:
            return

        target_user_id = parts[2]

        if target_user_id != user_id:
            return

        try:
            index = int(parts[3])
        except ValueError:
            return

        customer = get_user_customer(
            user_id
        )

        if not customer:
            return

        addresses = customer.get(
            "addresses",
            [],
        )

        if index < 0 or index >= len(addresses):
            return

        address = addresses[index]

        current_delivery[user_id] = {
            "title": address.get(
                "title",
                f"آدرس {index + 1}",
            ),
            "address": "لوکیشن ثبت‌شده",
            "latitude": address.get(
                "latitude"
            ),
            "longitude": address.get(
                "longitude"
            ),
            "fee": 0,
        }

        await show_order_preview(
            message,
            user_id,
        )

        return

    if data.startswith("edit_address_"):

        parts = data.split("_")

        if len(parts) != 3:
            return

        target_user_id = parts[2]

        if target_user_id != user_id:
            return

        try:
            index = int(parts[2])
        except ValueError:
            return

        return

    if data.startswith("delete_address_"):

        parts = data.split("_")

        if len(parts) != 4:
            return

        target_user_id = parts[2]

        if target_user_id != user_id:
            return

        try:
            index = int(parts[3])
        except ValueError:
            return

        customer = get_user_customer(
            user_id
        )

        if not customer:
            return

        addresses = customer.get(
            "addresses",
            [],
        )

        if index < 0 or index >= len(addresses):
            return

        addresses.pop(index)
        save_data()

        await show_addresses(
            message,
            user_id,
        )

        return

    if data == "delivery_pickup":

        current_delivery[user_id] = {
            "title": "تحویل حضوری",
            "address": "تحویل حضوری",
            "latitude": None,
            "longitude": None,
            "fee": 0,
        }

        await show_order_preview(
            message,
            user_id,
        )

        return

    if data == "delivery_heiat":

        current_delivery[user_id] = {
            "title": "هیأت امنا",
            "address": "هیأت امنا",
            "latitude": None,
            "longitude": None,
            "fee": 0,
        }

        await show_order_preview(
            message,
            user_id,
        )

        return

    if data == "delivery_location":

        customer = get_user_customer(
            user_id
        )

        if not customer:

            await show_customer_start(
                message,
                user_id,
            )

            return

        await show_addresses(
            message,
            user_id,
            back_callback="delivery",
        )

        return

    if data == "delivery":

        await show_delivery(
            message,
            user_id,
        )

        return

    if data == "confirm_order":

        order = await create_order(
            user_id
        )

        if not order:
            return

        await send_order_to_admins(
            order
        )

        await ask_for_receipt(
            message,
            user_id,
        )

        return

    if data == "cancel_order":

        user_states.pop(
            user_id,
            None,
        )

        current_delivery.pop(
            user_id,
            None,
        )

        await show_cart(
            message,
            user_id,
        )

        return

    if data == "orders":

        await show_orders(
            message,
            user_id,
        )

        return

    if data.startswith("order_"):

        order_number = data.split(
            "order_",
            1,
        )[1]

        await show_order_detail(
            message,
            user_id,
            order_number,
        )

        return


# =========================================================
# پیام‌ها
# =========================================================

@bot.event
async def on_message(
    message: Message,
):

    if not message.author:
        return

    user_id = str(
        message.author.user_id
    )

    content = getattr(
        message,
        "content",
        None,
    )

    if content == "🛍 فروشگاه":

        await show_shop(
            message,
            user_id,
        )

        return

    if content == "👤 مشخصات من":

        await show_customer_start(
            message,
            user_id,
        )

        return

    if content == "🛒 سبد خرید":

        await show_cart(
            message,
            user_id,
        )

        return

    if content == "📦 سفارش‌های من":

        await show_orders(
            message,
            user_id,
        )

        return

    state_data = user_states.get(
        user_id,
        {},
    )

    state = state_data.get(
        "state"
    )

    if state == "new_customer_name":

        customer = get_user_customer(
            user_id
        )

        if not customer:
            return

        customer["name"] = (
            content or ""
        ).strip()

        user_states[user_id] = {
            "state": "new_customer_phone",
        }

        save_data()

        await send_screen(
            message,
            "📱 لطفاً شماره موبایل خود را ارسال کنید.",
            None,
            user_id,
        )

        return

    if state == "new_customer_phone":

        customer = get_user_customer(
            user_id
        )

        if not customer:
            return

        customer["phone"] = (
            content or ""
        ).strip()

        user_states.pop(
            user_id,
            None,
        )

        save_data()

        await show_customer_profile(
            message,
            user_id,
        )

        return

    if state == "edit_name":

        customer = get_user_customer(
            user_id
        )

        if not customer:
            return

        customer["name"] = (
            content or ""
        ).strip()

        user_states.pop(
            user_id,
            None,
        )

        save_data()

        await show_customer_profile(
            message,
            user_id,
        )

        return

    if state == "edit_phone":

        customer = get_user_customer(
            user_id
        )

        if not customer:
            return

        customer["phone"] = (
            content or ""
        ).strip()

        user_states.pop(
            user_id,
            None,
        )

        save_data()

        await show_customer_profile(
            message,
            user_id,
        )

        return

    if state == "new_address_location":

        location = getattr(
            message,
            "location",
            None,
        )

        if not location:

            await send_screen(
                message,
                "📍 لطفاً لوکیشن خود را از طریق گزینه ارسال لوکیشن بفرستید.",
                None,
                user_id,
            )

            return

        user_states[user_id] = {
            "state": "new_address_title",
            "context": state_data.get(
                "context",
                "profile",
            ),
            "latitude": location.latitude,
            "longitude": location.longitude,
        }

        await send_screen(
            message,
            "🏷 یک عنوان برای این آدرس ارسال کنید.\n\n"
            "مثلاً: خانه، محل کار، مادر",
            None,
            user_id,
        )

        return

    if state == "new_address_title":

        customer = get_user_customer(
            user_id
        )

        if not customer:
            return

        title = (
            content or ""
        ).strip()

        if not title:

            await send_screen(
                message,
                "🏷 عنوان آدرس نمی‌تواند خالی باشد.",
                None,
                user_id,
            )

            return

        customer.setdefault(
            "addresses",
            [],
        ).append({
            "title": title,
            "address": "لوکیشن ثبت‌شده",
            "latitude": state_data.get("latitude"),
            "longitude": state_data.get("longitude"),
        })

        context = state_data.get(
            "context",
            "profile",
        )

        user_states.pop(
            user_id,
            None,
        )

        save_data()

        if context == "order":

            await show_addresses(
                message,
                user_id,
                back_callback="delivery",
            )

        else:

            await show_addresses(
                message,
                user_id,
            )

        return

    if state == "edit_address_title":

        customer = get_user_customer(
            user_id
        )

        if not customer:
            return

        index = state_data.get(
            "index",
            -1,
        )

        addresses = customer.get(
            "addresses",
            [],
        )

        if index < 0 or index >= len(addresses):
            return

        addresses[index]["title"] = (
            content or ""
        ).strip()

        user_states[user_id] = {
            "state": "edit_address_location",
            "index": index,
        }

        save_data()

        await send_screen(
            message,
            "📍 لوکیشن جدید این آدرس را ارسال کنید.",
            None,
            user_id,
        )

        return

    if state == "edit_address_location":

        customer = get_user_customer(
            user_id
        )

        if not customer:
            return

        location = getattr(
            message,
            "location",
            None,
        )

        if not location:

            await send_screen(
                message,
                "📍 لطفاً لوکیشن جدید را از طریق گزینه ارسال لوکیشن بفرستید.",
                None,
                user_id,
            )

            return

        index = state_data.get(
            "index",
            -1,
        )

        addresses = customer.get(
            "addresses",
            [],
        )

        if index < 0 or index >= len(addresses):
            return

        addresses[index]["latitude"] = (
            location.latitude
        )
        addresses[index]["longitude"] = (
            location.longitude
        )
        addresses[index]["address"] = (
            "لوکیشن ثبت‌شده"
        )

        user_states.pop(
            user_id,
            None,
        )

        save_data()

        await show_address_detail(
            message,
            user_id,
            index,
        )

        return

    if state == "waiting_receipt":

        photos = getattr(
            message,
            "photos",
            None,
        )

        if not photos:

            await send_screen(
                message,
                "🧾 لطفاً تصویر رسید پرداخت را ارسال کنید.",
                receipt_keyboard(),
                user_id,
            )

            return

        order_number = state_data.get(
            "order_number"
        )

        order = find_order(
            user_id,
            order_number,
        )

        if not order:
            return

        photo = photos[-1]

        order["receipt_sent"] = True
        order["status"] = "رسید ارسال شد"

        save_data()

        for admin_id in ADMIN_CHAT_IDS:

            try:

                await bot.send_photo(
                    chat_id=int(admin_id),
                    photo=photo,
                    caption=(
                        f"🧾 رسید پرداخت سفارش #{order_number}\n"
                        f"نام: {order.get('customer', {}).get('name', '-') }\n"
                        f"موبایل: {order.get('customer', {}).get('phone', '-') }\n"
                        f"مبلغ: {money(order.get('total', 0))}"
                    ),
                )

            except Exception as e:

                logging.error(
                    f"ارسال رسید به مدیر {admin_id} ناموفق بود: {e}"
                )

        carts.pop(
            user_id,
            None,
        )

        current_delivery.pop(
            user_id,
            None,
        )

        user_states.pop(
            user_id,
            None,
        )

        await send_screen(
            message,
            "✅ رسید پرداخت شما دریافت شد.\n\n"
            f"شماره سفارش شما: #{order_number}\n\n"
            "سفارش شما برای بررسی و آماده‌سازی ارسال شد.",
            InlineKeyboardMarkup(
                keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📦 سفارش‌های من",
                            callback_data="orders",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🏠 منوی اصلی",
                            callback_data="home",
                        )
                    ],
                ]
            ),
            user_id,
        )

        return


# =========================================================
# شروع ربات
# =========================================================

@bot.event
async def on_ready():

    print("=== BALE BOT CONNECTED ===")
    print("SabziU Bale Store is ready!")
    print("ADMIN_CHAT_IDS:", ADMIN_CHAT_IDS)


bot.run()
