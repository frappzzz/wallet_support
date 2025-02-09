import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import Message
from DB import DB

bot = Bot(token="8041525340:AAGiUjdpl7ZmDc5IO5YvATfXgBRXI_DRCz8")
dp = Dispatcher()

FLASK_SERVER_URL = "http://127.0.0.1:5005"  # Укажи адрес сервера Flask

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Привет! Это тех.поддержка HammyPay. Здесь Вы можете оставить свой вопрос и Вам ответят в ближайшее время.")


@dp.message()
async def handle_message(message: Message):
    db = DB()
    db.addMessage(1, message.from_user.id, message.text, message.message_id)

    # Отправляем сообщение на сервер Flask, чтобы обновить чат
    try:
        requests.post(f"{FLASK_SERVER_URL}/new_message", json={
            "id_user_tg": message.from_user.id,
            "message": message.text
        })
    except Exception as e:
        print(f"Ошибка при отправке данных на сервер Flask: {e}")

    print(f"Сообщение от {message.from_user.id} сохранено")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
