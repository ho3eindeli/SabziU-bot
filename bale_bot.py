@bot.event
async def on_callback(callback: CallbackQuery):

    user_id = str(callback.from_user.user_id)
    data = callback.data

    # =====================================================
    # مشتری ذخیره‌شده
    # =====================================================

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
            "اطلاعات شما آماده است.\n"
            "حالا محصول موردنظر را انتخاب کنید:",
            components=categories_keyboard(),
        )
        return

    # =====================================================
    # ثبت مشخصات جدید
    # =====================================================

    if data == "new_customer":

        user_states[user_id] = "name"

        await callback.message.reply(
            "👤 لطفاً نام و نام خانوادگی خود را وارد کنید:"
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

        category = data.replace("category_", "", 1)

        names = {
            "fried": "🌿 سبزی‌های سرخ‌شده",
            "raw": "🥬 سبزی‌های خام",
            "pickles": "🥒 ترشیجات",
            "syrup": "🥭 شربت‌ها و مربا",
        }

        if category not in names:

            await callback.message.reply(
                "❌ دسته‌بندی پیدا نشد.",
                components=categories_keyboard(),
            )
            return

        await callback.message.reply(
            f"{names[category]}\n\n"
            "محصول موردنظر را انتخاب کنید:",
            components=category_keyboard(category),
        )
        return

    # =====================================================
    # انتخاب محصول
    # =====================================================

    if data.startswith("product_"):

        product_id = data.replace("product_", "", 1)

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

    # =====================================================
    # افزودن محصول به سبد
    # =====================================================

    if data.startswith("add_"):

        product_id = data.replace("add_", "", 1)

        if product_id not in PRODUCTS:

            await callback.message.reply(
                "❌ محصول پیدا نشد.",
                components=categories_keyboard(),
            )
            return

        # ساخت سبد برای مشتری
        if user_id not in carts:
            carts[user_id] = {}

        # افزایش تعداد
        old_quantity = carts[user_id].get(product_id, 0)

        carts[user_id][product_id] = old_quantity + 1

        product = PRODUCTS[product_id]

        quantity = carts[user_id][product_id]

        await callback.message.reply(
            "✅ محصول به سبد خرید اضافه شد!\n\n"
            f"🌿 {product['name']}\n"
            f"📦 {product['size']}\n"
            f"🔢 تعداد: {quantity}\n"
            f"💰 قیمت واحد: {product['price']:,} تومان\n\n"
            "از منوی زیر می‌توانید تعداد را تغییر دهید:",
            components=cart_keyboard(user_id),
        )
        return

    # =====================================================
    # افزایش تعداد
    # =====================================================

    if data.startswith("plus_"):

        product_id = data.replace("plus_", "", 1)

        if product_id not in PRODUCTS:
            return

        if user_id not in carts:
            carts[user_id] = {}

        current_quantity = carts[user_id].get(product_id, 0)

        carts[user_id][product_id] = current_quantity + 1

        await show_cart(
            callback.message,
            user_id,
        )
        return

    # =====================================================
    # کاهش تعداد
    # =====================================================

    if data.startswith("minus_"):

        product_id = data.replace("minus_", "", 1)

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

        # اگر مشتری قبلاً مشخصات دارد
        if (
            user_id in customers
            and customers[user_id].get("name")
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

    # =====================================================
    # تحویل — هیأت امنا
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

    # =====================================================
    # تحویل — مسجد مولای متقیان
    # =====================================================

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

    # =====================================================
    # Callback ناشناخته
    # =====================================================

    logging.warning(
        f"Unknown callback received: {data}"
    )
