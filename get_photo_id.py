import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)


logging.basicConfig(
    level=logging.INFO
)


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def get_photo_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.message.photo:

        photo = update.message.photo[-1]

        await update.message.reply_text(
            f"Photo file_id:\n\n{photo.file_id}"
        )

        print(
            "PHOTO FILE ID:",
            photo.file_id
        )

    else:

        await update.message.reply_text(
            "لطفاً یک عکس ارسال کنید."
        )


def main():

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            get_photo_id
        )
    )

    print(
        "Photo ID bot is running..."
    )

    app.run_polling()


if __name__ == "__main__":
    main()
