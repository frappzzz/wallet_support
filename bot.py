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
        await message.answer("Используйте ссылку с параметром токена.")
        return

    token = args
    db = DB()

    # Проверяем, существует ли токен в базе данных
    db.cur.execute("SELECT id_user_web, id_user_tg FROM Users WHERE token = ?", (token,))
    user = db.cur.fetchone()

    if not user:
        await message.answer("Некорректный токен.")
        return

    id_user_web = user[0]
    id_user_tg = message.from_user.id

    # Если пользователь уже авторизован, обновляем его токен
    if user[1]:  # Если id_user_tg уже есть
        db.cur.execute("""
            UPDATE Users
            SET token = ?
            WHERE id_user_web = ?
        """, (token, id_user_web))
    else:
        # Если пользователь не авторизован, добавляем id_user_tg
        db.cur.execute("""
            UPDATE Users
            SET id_user_tg = ?, token = ?
            WHERE id_user_web = ?
        """, (id_user_tg, token, id_user_web))
    db.con.commit()

    await message.answer("Вы успешно авторизованы! Теперь вы можете общаться с поддержкой.")

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