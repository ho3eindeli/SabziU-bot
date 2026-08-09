import os
import json
import logging
import requests

# =========================================================
# تنظیمات
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

TOKEN = os.getenv("BALE_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("BALE_ADMIN_CHAT_ID")

API_URL = f"https://tapi.bale.ai/bot{TOKEN}"

ORDER_NUMBER = 1000
CUSTOMERS_FILE = "bale_customers.json"

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
# حافظه
# =========================================================

carts = {}
customers = {}


# =========================================================
# خواندن مشتریان
# =========================================================

def load_customers():
    global customers

    try:
        if os.path.exists(CUSTOMERS_FILE):
            with open(
                CUSTOMERS_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                customers = json.load(f)

    except Exception as e:
        logging.error(f"Customer load error: {e}")
        customers = {}


def save_customers():
    try:
        with open(
            CUSTOMERS_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                customers,
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:
        logging.error(f"Customer save error: {e}")


# =========================================================
# ارسال درخواست به بله
# =========================================================

def bale_request(method, data=None):

    url = f"{API_URL}/{method}"

    try:
        response = requests.post(
            url,
            json=data or {},
            timeout=30
        )

        return response.json()

    except Exception as e:

        logging.error(
            f"Bale API error: {e}"
        )

        return {}


# =========================================================
# ارسال پیام
# =========================================================

def send_message(
    chat_id,
    text,
    keyboard=None
):

    data = {
        "chat_id": chat_id,
        "text": text,
    }

    if keyboard:
        data["reply_markup"] = {
            "inline_keyboard": keyboard
        }

    return bale_request(
        "sendMessage",
        data
    )


# =========================================================
# کیبورد اصلی
# =========================================================

def main_menu():

    return [
        [
            {
                "text": "🛒 فروشگاه سبزی‌یو",
                "callback_data": "shop"
            }
        ],
        [
            {
                "text": "🧺 سبد خرید",
                "callback_data": "cart"
            }
        ]
    ]


# =========================================================
# دسته‌بندی
# =========================================================

def categories_keyboard():

    return [
        [
            {
                "text": "🌿 سبزی‌های سرخ‌شده",
                "callback_data": "category_fried"
            }
        ],
        [
            {
                "text": "🥬 سبزی‌های خام",
                "callback_data": "category_raw"
            }
        ],
        [
            {
                "text": "🥒 ترشیجات",
                "callback_data": "category_pickles"
            }
        ],
        [
            {
                "text": "🥭 شربت‌ها و مربا",
                "callback_data": "category_syrup"
            }
        ],
        [
            {
                "text": "🧺 سبد خرید",
                "callback_data": "cart"
            }
        ]
    ]


# =========================================================
# محصولات
# =========================================================

def category_keyboard(category):

    keyboard = []

    for product_id, product in PRODUCTS.items():

        if product["category"] == category:

            keyboard.append([
                {
                    "text":
                        f"{product['name']} | "
                        f"{product['size']}",
                    "callback_data":
                        f"product_{product_id}"
                }
            ])

    keyboard.append([
        {
            "text": "⬅️ بازگشت",
            "callback_data": "shop"
        }
    ])

    keyboard.append([
        {
            "text": "🧺 سبد خرید",
            "callback_data": "cart"
        }
    ])

    return keyboard


# =========================================================
# کیبورد محصول
# =========================================================

def product_keyboard(
    product_id,
    user_id
):

    quantity = carts.get(
        user_id,
        {}
    ).get(
        product_id,
        0
    )

    keyboard = []

    if quantity > 0:

        keyboard.append([
            {
                "text": "➖",
                "callback_data":
                    f"dec_{product_id}"
            },
            {
                "text":
                    f"🛒 {quantity}",
                "callback_data": "cart"
            },
            {
                "text": "➕",
                "callback_data":
                    f"inc_{product_id}"
            }
        ])

    else:

        keyboard.append([
            {
                "text": "➕ افزودن به سبد",
                "callback_data":
                    f"inc_{product_id}"
            }
        ])

    keyboard.append([
        {
            "text": "🛒 ادامه خرید",
            "callback_data": "shop"
        }
    ])

    keyboard.append([
        {
            "text": "🧺 سبد خرید",
            "callback_data": "cart"
        }
    ])

    return keyboard


# =========================================================
# محل تحویل
# =========================================================

def delivery_keyboard():

    return [
        [
            {
                "text":
                    "🏢 هیأت امنا — رایگان",
                "callback_data":
                    "delivery_heyat"
            }
        ],
        [
            {
                "text":
                    "🕌 مسجد مولای متقیان — رایگان",
                "callback_data":
                    "delivery_mola"
            }
        ]
    ]


# =========================================================
# اطلاعات ذخیره شده
# =========================================================

def saved_customer_keyboard():

    return [
        [
            {
                "text":
                    "✅ استفاده از اطلاعات من",
                "callback_data":
                    "use_saved_customer"
            }
        ],
        [
            {
                "text":
                    "✏️ تغییر اطلاعات",
                "callback_data":
                    "change_customer"
            }
        ]
    ]


# =========================================================
# تأیید سفارش
# =========================================================

def final_order_keyboard():

    return [
        [
            {
                "text":
                    "✅ تأیید و ثبت سفارش",
                "callback_data":
                    "confirm_order"
            }
        ],
        [
            {
                "text":
                    "❌ لغو سفارش",
                "callback_data":
                    "cancel_order"
            }
        ]
    ]


# =========================================================
# سبد خرید
# =========================================================

def cart_text(user_id):

    items = carts.get(
        user_id,
        {}
    )

    if not items:
        return "🧺 سبد خرید شما خالی است."

    total = 0

    lines = [
        "🧺 سبد خرید شما:\n"
    ]

    number = 1

    for product_id, quantity in items.items():

        product = PRODUCTS[product_id]

        subtotal = (
            product["price"]
            * quantity
        )

        total += subtotal

        lines.append(
            f"{number}. {product['name']}\n"
            f"   📦 {product['size']}\n"
            f"   🔢 تعداد: {quantity}\n"
            f"   💰 قیمت واحد: "
            f"{product['price']:,} تومان\n"
            f"   💵 مبلغ: "
            f"{subtotal:,} تومان\n"
        )

        number += 1

    lines.append(
        f"💰 جمع کل: {total:,} تومان"
    )

    return "\n".join(lines)


def cart_keyboard(user_id):

    keyboard = []

    items = carts.get(
        user_id,
        {}
    )

    for product_id, quantity in items.items():

        product = PRODUCTS[product_id]

        keyboard.append([
            {
                "text":
                    f"➖ {product['name']}",
                "callback_data":
                    f"dec_{product_id}"
            },
            {
                "text":
                    f"{quantity} عدد",
                "callback_data":
                    f"product_{product_id}"
            },
            {
                "text": "➕",
                "callback_data":
                    f"inc_{product_id}"
            }
        ])

    if items:

        keyboard.append([
            {
                "text":
                    "📦 ثبت سفارش",
                "callback_data":
                    "order"
            }
        ])

    keyboard.append([
        {
            "text":
                "🛒 ادامه خرید",
            "callback_data":
                "shop"
        }
    ])

    return keyboard


# =========================================================
# نمایش سبد
# =========================================================

def show_cart(chat_id, user_id):

    send_message(
        chat_id,
        cart_text(user_id),
        cart_keyboard(user_id)
    )


# =========================================================
# پردازش Callback
# =========================================================

def process_callback(
    callback
):

    callback_id = callback.get(
        "id"
    )

    data = callback.get(
        "data"
    )

    message = callback.get(
        "message",
        {}
    )

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get(
        "id"
    )

    user = callback.get(
        "from",
        {}
    )

    user_id = user.get(
        "id"
    )

    # پاسخ به callback

    bale_request(
        "answerCallbackQuery",
        {
            "callback_query_id":
                callback_id
        }
    )

    # -----------------------------------------------------
    # فروشگاه
    # -----------------------------------------------------

    if data == "shop":

        send_message(
            chat_id,
            "🛒 فروشگاه سبزی‌یو\n\n"
            "دسته‌بندی موردنظر را انتخاب کنید:",
            categories_keyboard()
        )

        return


    # -----------------------------------------------------
    # دسته‌بندی
    # -----------------------------------------------------

    if data.startswith(
        "category_"
    ):

        category = data.replace(
            "category_",
            ""
        )

        names = {
            "fried":
                "🌿 سبزی‌های سرخ‌شده",
            "raw":
                "🥬 سبزی‌های خام",
            "pickles":
                "🥒 ترشیجات",
            "syrup":
                "🥭 شربت‌ها و مربا"
        }

        send_message(
            chat_id,
            f"{names.get(category, 'فروشگاه')}\n\n"
            "محصول موردنظر را انتخاب کنید:",
            category_keyboard(category)
        )

        return


    # -----------------------------------------------------
    # محصول
    # -----------------------------------------------------

    if data.startswith(
        "product_"
    ):

        product_id = data.replace(
            "product_",
            ""
        )

        product = PRODUCTS.get(
            product_id
        )

        if not product:
            return

        quantity = carts.get(
            user_id,
            {}
        ).get(
            product_id,
            0
        )

        send_message(
            chat_id,
            f"🌿 {product['name']}\n\n"
            f"📦 {product['size']}\n"
            f"💰 {product['price']:,} تومان\n"
            f"🔢 تعداد فعلی: {quantity}\n\n"
            "تعداد موردنظر را انتخاب کنید:",
            product_keyboard(
                product_id,
                user_id
            )
        )

        return


    # -----------------------------------------------------
    # افزایش
    # -----------------------------------------------------

    if data.startswith(
        "inc_"
    ):

        product_id = data.replace(
            "inc_",
            ""
        )

        if product_id not in PRODUCTS:
            return

        carts.setdefault(
            user_id,
            {}
        )

        carts[user_id][product_id] = (
            carts[user_id].get(
                product_id,
                0
            ) + 1
        )

        product = PRODUCTS[product_id]

        quantity = carts[user_id][product_id]

        send_message(
            chat_id,
            f"🌿 {product['name']}\n\n"
            f"📦 {product['size']}\n"
            f"💰 قیمت واحد: "
            f"{product['price']:,} تومان\n"
            f"🔢 تعداد: {quantity}\n"
            f"💵 مبلغ: "
            f"{product['price'] * quantity:,} تومان",
            product_keyboard(
                product_id,
                user_id
            )
        )

        return


    # -----------------------------------------------------
    # کاهش
    # -----------------------------------------------------

    if data.startswith(
        "dec_"
    ):

        product_id = data.replace(
            "dec_",
            ""
        )

        if user_id not in carts:
            return

        if product_id not in carts[user_id]:
            return

        carts[user_id][product_id] -= 1

        if carts[user_id][product_id] <= 0:

            del carts[user_id][product_id]

            if not carts[user_id]:

                del carts[user_id]

            send_message(
                chat_id,
                "🗑 محصول از سبد خرید حذف شد.",
                main_menu()
            )

            return

        product = PRODUCTS[product_id]

        quantity = carts[user_id][product_id]

        send_message(
            chat_id,
            f"🌿 {product['name']}\n\n"
            f"📦 {product['size']}\n"
            f"💰 قیمت واحد: "
            f"{product['price']:,} تومان\n"
            f"🔢 تعداد: {quantity}\n"
            f"💵 مبلغ: "
            f"{product['price'] * quantity:,} تومان",
            product_keyboard(
                product_id,
                user_id
            )
        )

        return


    # -----------------------------------------------------
    # سبد
    # -----------------------------------------------------

    if data == "cart":

        show_cart(
            chat_id,
            user_id
        )

        return


    # -----------------------------------------------------
    # ثبت سفارش
    # -----------------------------------------------------

    if data == "order":

        if not carts.get(user_id):

            send_message(
                chat_id,
                "🧺 سبد خرید شما خالی است.",
                categories_keyboard()
            )

            return

        saved = customers.get(
            str(user_id)
        )

        if saved:

            name = saved.get(
                "name",
                ""
            )

            phone = saved.get(
                "phone",
                ""
            )

            user_state[user_id] = {
                "step": "delivery",
                "name": name,
                "phone": phone
            }

            send_message(
                chat_id,
                "📦 ثبت سفارش\n\n"
                "اطلاعات ثبت‌شده شما:\n\n"
                f"👤 نام: {name}\n"
                f"📱 تلفن: {phone}\n\n"
                "آیا می‌خواهید با همین "
                "اطلاعات سفارش دهید؟",
                saved_customer_keyboard()
            )

        else:

            user_state[user_id] = {
                "step": "name"
            }

            send_message(
                chat_id,
                "📦 ثبت سفارش\n\n"
                "لطفاً نام و نام خانوادگی "
                "خود را وارد کنید:"
            )

        return


    # -----------------------------------------------------
    # اطلاعات قبلی
    # -----------------------------------------------------

    if data == "use_saved_customer":

        state = user_state.setdefault(
            user_id,
            {}
        )

        state["step"] = "delivery"

        send_message(
            chat_id,
            "✅ اطلاعات شما انتخاب شد.\n\n"
            "📍 محل تحویل سفارش را انتخاب کنید:",
            delivery_keyboard()
        )

        return


    # -----------------------------------------------------
    # تغییر اطلاعات
    # -----------------------------------------------------

    if data == "change_customer":

        user_state[user_id] = {
            "step": "name"
        }

        send_message(
            chat_id,
            "✏️ تغییر اطلاعات\n\n"
            "لطفاً نام و نام خانوادگی "
            "خود را وارد کنید:"
        )

        return


    # -----------------------------------------------------
    # تحویل هیأت امنا
    # -----------------------------------------------------

    if data == "delivery_heyat":

        state = user_state.setdefault(
            user_id,
            {}
        )

        state["delivery"] = (
            "هیأت امنا"
        )

        show_order_summary(
            chat_id,
            user_id
        )

        return


    # -----------------------------------------------------
    # تحویل مسجد
    # -----------------------------------------------------

    if data == "delivery_mola":

        state = user_state.setdefault(
            user_id,
            {}
        )

        state["delivery"] = (
            "مسجد مولای متقیان"
        )

        show_order_summary(
            chat_id,
            user_id
        )

        return


    # -----------------------------------------------------
    # تأیید
    # -----------------------------------------------------

    if data == "confirm_order":

        confirm_order(
            chat_id,
            user_id
        )

        return


    # -----------------------------------------------------
    # لغو
    # -----------------------------------------------------

    if data == "cancel_order":

        carts.pop(
            user_id,
            None
        )

        user_state.pop(
            user_id,
            None
        )

        send_message(
            chat_id,
            "❌ سفارش لغو شد.",
            main_menu()
        )


# =========================================================
# وضعیت مشتری
# =========================================================

user_state = {}


# =========================================================
# خلاصه سفارش
# =========================================================

def show_order_summary(
    chat_id,
    user_id
):

    state = user_state.get(
        user_id,
        {}
    )

    name = state.get(
        "name",
        ""
    )

    phone = state.get(
        "phone",
        ""
    )

    delivery = state.get(
        "delivery",
        ""
    )

    items = carts.get(
        user_id,
        {}
    )

    total = 0

    lines = []

    for product_id, quantity in items.items():

        product = PRODUCTS[product_id]

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
        f"👤 نام: {name}\n"
        f"📱 تلفن: {phone}\n"
        f"📍 محل تحویل: {delivery}\n"
        "🚚 هزینه تحویل: رایگان\n\n"
        "🛍 محصولات:\n"
        + "\n".join(lines)
        + f"\n\n💰 مبلغ کل: "
        f"{total:,} تومان\n\n"
        "اگر اطلاعات صحیح است، "
        "«تأیید و ثبت سفارش» را بزنید."
    )

    send_message(
        chat_id,
        text,
        final_order_keyboard()
    )


# =========================================================
# ثبت سفارش نهایی
# =========================================================

def confirm_order(
    chat_id,
    user_id
):

    global ORDER_NUMBER

    state = user_state.get(
        user_id,
        {}
    )

    name = state.get(
        "name",
        ""
    )

    phone = state.get(
        "phone",
        ""
    )

    delivery = state.get(
        "delivery",
        ""
    )

    items = carts.get(
        user_id,
        {}
    )

    if not items:

        send_message(
            chat_id,
            "❌ سبد خرید خالی است.",
            main_menu()
        )

        return

    # ذخیره مشتری

    customers[str(user_id)] = {
        "name": name,
        "phone": phone
    }

    save_customers()

    total = 0

    lines = []

    for product_id, quantity in items.items():

        product = PRODUCTS[product_id]

        subtotal = (
            product["price"]
            * quantity
        )

        total += subtotal

        lines.append(
            f"• {product['name']}\n"
            f"  {product['size']} × {quantity}\n"
            f"  مبلغ: {subtotal:,} تومان"
        )

    order_number = ORDER_NUMBER

    ORDER_NUMBER += 1

    # پیام مشتری

    customer_text = (
        "🎉 سفارش شما با موفقیت ثبت شد!\n\n"
        f"🔢 شماره سفارش: #{order_number}\n"
        f"👤 نام: {name}\n"
        f"📱 تلفن: {phone}\n"
        f"📍 محل تحویل: {delivery}\n"
        "🚚 هزینه تحویل: رایگان\n\n"
        "🛍 محصولات:\n"
        + "\n".join(lines)
        + f"\n\n💰 مبلغ کل: "
        f"{total:,} تومان\n\n"
        "از خرید شما از سبزی‌یو سپاسگزاریم 🌿"
    )

    send_message(
        chat_id,
        customer_text,
        main_menu()
    )

    # پیام مدیر

    admin_text = (
        "🆕 سفارش جدید سبزی‌یو\n\n"
        f"🔢 شماره سفارش: #{order_number}\n\n"
        f"👤 مشتری: {name}\n"
        f"📱 تلفن: {phone}\n"
        f"📍 محل تحویل: {delivery}\n"
        "🚚 هزینه تحویل: رایگان\n\n"
        "🛍 محصولات:\n"
        + "\n".join(lines)
        + f"\n\n💰 مبلغ کل: "
        f"{total:,} تومان\n\n"
        f"🆔 شناسه بله مشتری: {user_id}"
    )

    if ADMIN_CHAT_ID:

        send_message(
            int(ADMIN_CHAT_ID),
            admin_text
        )

    # پاک کردن سبد

    carts.pop(
        user_id,
        None
    )

    user_state.pop(
        user_id,
        None
    )


# =========================================================
# پیام متنی
# =========================================================

def process_message(message):

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get(
        "id"
    )

    user = message.get(
        "from",
        {}
    )

    user_id = user.get(
        "id"
    )

    text = message.get(
        "text",
        ""
    ).strip()

    if text == "/start":

        user_state.pop(
            user_id,
            None
        )

        send_message(
            chat_id,
            "سلام 👋\n\n"
            "به فروشگاه سبزی‌یو خوش آمدید 🌿\n\n"
            "از منوی زیر انتخاب کنید:",
            main_menu()
        )

        return

    if text == "/cancel":

        carts.pop(
            user_id,
            None
        )

        user_state.pop(
            user_id,
            None
        )

        send_message(
            chat_id,
            "❌ سفارش لغو شد.",
            main_menu()
        )

        return

    state = user_state.get(
        user_id,
        {}
    )

    step = state.get(
        "step"
    )

    # نام

    if step == "name":

        state["name"] = text
        state["step"] = "phone"

        send_message(
            chat_id,
            "📱 لطفاً شماره تلفن خود را "
            "وارد کنید:"
        )

        return

    # شماره

    if step == "phone":

        state["phone"] = text
        state["step"] = "delivery"

        send_message(
            chat_id,
            "📍 محل تحویل سفارش را انتخاب کنید:",
            delivery_keyboard()
        )

        return

    send_message(
        chat_id,
        "برای شروع خرید، /start را بزنید.",
        main_menu()
    )


# =========================================================
# دریافت آپدیت‌ها
# =========================================================

def run_bot():

    if not TOKEN:

        raise RuntimeError(
            "BALE_BOT_TOKEN تنظیم نشده است."
        )

    load_customers()

    offset = None

    print(
        "SabziU Bale bot is running..."
    )

    while True:

        try:

            data = {
                "timeout": 30
            }

            if offset is not None:
                data["offset"] = offset

            result = bale_request(
                "getUpdates",
                data
            )

            updates = result.get(
                "result",
                []
            )

            for update in updates:

                offset = (
                    update["update_id"] + 1
                )

                if "callback_query" in update:

                    process_callback(
                        update["callback_query"]
                    )

                elif "message" in update:

                    process_message(
                        update["message"]
                    )

        except Exception as e:

            logging.error(
                f"Bot loop error: {e}"
            )


# =========================================================
# شروع
# =========================================================

if __name__ == "__main__":
    run_bot()
