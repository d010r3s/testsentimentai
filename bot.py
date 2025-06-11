import asyncio, os, requests
from aiogram import Bot, Dispatcher, types

BOT = Bot(os.getenv("TG_TOKEN"))
dp  = Dispatcher()

@dp.message(commands=["status"])
async def status(msg: types.Message):
    r = requests.post("http://localhost:8000/classify",
                      json={"text": msg.text.replace('/status','')}).json()
    await msg.answer(f"Тональность: {r['sentiment']}")

async def main():
    await dp.start_polling(BOT)
if __name__ == "__main__":
    asyncio.run(main())
