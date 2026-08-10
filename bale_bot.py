import os
import bale

TOKEN = os.getenv("BALE_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BALE_BOT_TOKEN تنظیم نشده است.")

bot = bale.Bot(token=TOKEN)

@bot.event
async def on_ready():
    print("=== BALE BOT CONNECTED ===")
    print("SabziU Bale bot is ready!")

@bot.event
async def on_message(message):
    if message.content == "/start":
        await message.reply(
            "سلام 👋\n\n"
            "به بازوی سبزی‌یو خوش آمدید 🌿"
        )

bot.run()
