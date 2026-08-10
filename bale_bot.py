import os

from bale import Bot, Message
from bale.handlers import CommandHandler

TOKEN = os.getenv("BALE_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BALE_BOT_TOKEN تنظیم نشده است.")

client = Bot(token=TOKEN)


@client.listen("on_ready")
async def on_ready():
    print("=== BALE BOT CONNECTED ===")
    print("SabziU Bale bot is ready!")


@client.handle(CommandHandler("start"))
async def start_command(message: Message):
    await message.reply(
        "سلام 👋\n\n"
        "به بازوی سبزی‌یو خوش آمدید 🌿\n\n"
        "ربات با موفقیت به بله متصل شده است."
    )


@client.handle(CommandHandler("help"))
async def help_command(message: Message):
    await message.reply(
        "🌿 سبزی‌یو\n\n"
        "فروشگاه به‌زودی فعال می‌شود."
    )


client.run()
