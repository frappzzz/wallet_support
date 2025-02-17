import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import Message
from aiogram.filters import CommandObject
from DB import DB
import config

bot = Bot(token=config.TG_BOT_TOKEN)
dp = Dispatcher()

FLASK_SERVER_URL = "http://127.0.0.1:5005"


@dp.message(Command("start"))
async def start_command(message: Message, command: CommandObject):
    args = command.args
    if not args:
        await message.answer("Используйте ссылку с параметром id_user_web.")
        return

    try:
        id_user_web = int(args)
    except ValueError:
        await message.answer("Некорректный id_user_web. Должно быть число.")
        return

    db = DB()
    db.addUser(message.from_user.id, id_user_web)
    try:
        requests.post(f"{FLASK_SERVER_URL}/new_user", json={
            "id_user_tg": message.from_user.id,
            "id_user_web": id_user_web
        })
    except Exception as e:
        print(f"Ошибка отправки new_user: {e}")
    await message.answer("Привет! Это тех.поддержка HammyPay. Задайте ваш вопрос.")


@dp.message()
async def handle_message(message: Message):
    db = DB()
    id_user_web = db.get_user_web_id(message.from_user.id)

    if not id_user_web:
        await message.answer("Сначала выполните /start с вашим id_user_web.")
        return

    db.addMessage(id_user_web, message.from_user.id, message.text, message.message_id)

    try:
        requests.post(f"{FLASK_SERVER_URL}/new_message", json={
            "id_user_tg": message.from_user.id,
            "message": message.text
        })
    except Exception as e:
        print(f"Ошибка при отправке на Flask: {e}")

    print(f"Сообщение от {message.from_user.id} сохранено")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())