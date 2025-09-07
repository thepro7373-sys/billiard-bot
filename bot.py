import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = list(map(int, os.getenv("ADMINS").split(",")))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Kabinalar va zallar narxlari
PRICES = {
    "Kabina 1": 50000,
    "Kabina 2": 50000,
    "Kabina 3": 50000,
    "Zal 1": 30000,
    "Zal 2": 30000,
}

# Holatlarni saqlash
sessions = {}
daily_income = 0
last_reset = None


def reset_daily_income():
    global daily_income, last_reset
    daily_income = 0
    last_reset = datetime.now().date()


async def auto_reset():
    while True:
        now = datetime.now()
        if now.hour == 9 and (last_reset is None or last_reset != now.date()):
            reset_daily_income()
            logging.info("Kunlik daromad reset qilindi")
        await asyncio.sleep(60)


@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("⛔ Sizda bu botdan foydalanish huquqi yo‘q.")

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for name in PRICES.keys():
        keyboard.add(name)
    await message.answer("✅ Xona tanlang:", reply_markup=keyboard)


@dp.message_handler(lambda msg: msg.text in PRICES.keys())
async def handle_room(message: types.Message):
    room = message.text
    if room not in sessions:
        sessions[room] = {"start": None, "end": None, "total": 0}

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("▶️ Start", "⏹ Stop", "📊 Hisobot")
    await message.answer(f"✅ {room} tanlandi. Buyruqni tanlang:", reply_markup=keyboard)


@dp.message_handler(lambda msg: msg.text in ["▶️ Start", "⏹ Stop", "📊 Hisobot"])
async def handle_action(message: types.Message):
    global daily_income
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return await message.answer("⛔ Sizda huquq yo‘q.")

    # Default xona (agar tanlanmagan bo‘lsa)
    room = "Kabina 1"

    if message.text == "▶️ Start":
        sessions[room]["start"] = datetime.now()
        await message.answer(f"▶️ {room} boshlandi {sessions[room]['start'].strftime('%H:%M')} da")

    elif message.text == "⏹ Stop":
        if not sessions[room]["start"]:
            return await message.answer("❌ Avval start bosing.")

        sessions[room]["end"] = datetime.now()
        duration = (sessions[room]["end"] - sessions[room]["start"]).seconds // 60
        price_per_hour = PRICES[room]
        cost = (duration / 60) * price_per_hour
        sessions[room]["total"] += cost
        daily_income += cost

        await message.answer(
            f"⏹ {room} yakunlandi.\n"
            f"⏱ Vaqt: {duration} daqiqa\n"
            f"💰 Summa: {int(cost):,} so‘m\n"
            f"📊 Jami: {int(sessions[room]['total']):,} so‘m"
        )

    elif message.text == "📊 Hisobot":
        await message.answer(
            f"📊 Kunlik tushum: {int(daily_income):,} so‘m",
            reply_markup=types.ReplyKeyboardRemove()
        )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(auto_reset())
    executor.start_polling(dp, skip_updates=True)
