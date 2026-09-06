"""
bot.py — точка входа. Запускает Telegram-бота учёта личных финансов.

Как пользоваться (когда бот запущен):
    "кофе 250"        -> запишет трату 250 руб. в категорию "Еда"
    "500 такси"       -> цифра и слово можно писать в любом порядке
    /report           -> график трат за последние 30 дней
    /report 7         -> график трат за последние 7 дней
    /undo             -> удалить последнюю добавленную запись
    /help             -> подсказка по командам
"""

import asyncio
import logging
import os
import re

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, FSInputFile
from dotenv import load_dotenv

import db
from categorizer import detect_category
from charts import build_report_chart

load_dotenv()  # подтягивает переменные из .env файла

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регулярка, чтобы найти число (сумму) в сообщении пользователя.
# Ловит "250", "250.5", "250,5"
AMOUNT_PATTERN = re.compile(r"(\d+[.,]?\d*)")


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот учёта личных финансов.\n\n"
        "Просто напиши мне трату в свободной форме, например:\n"
        "  <code>кофе 250</code>\n"
        "  <code>500 такси</code>\n\n"
        "Команды:\n"
        "/report [дни] — график трат (по умолчанию за 30 дней)\n"
        "/undo — удалить последнюю запись\n"
        "/help — эта подсказка",
        parse_mode="HTML",
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await cmd_start(message)


@dp.message(Command("report"))
async def cmd_report(message: Message, command: CommandObject):
    # Если после /report указано число дней — используем его, иначе 30
    days = 30
    if command.args:
        try:
            days = int(command.args.strip())
        except ValueError:
            pass

    expenses = db.get_expenses(message.from_user.id, days=days)
    chart_path = build_report_chart(expenses, days)

    if chart_path is None:
        await message.answer(f"За последние {days} дней трат не найдено.")
        return

    await message.answer_photo(FSInputFile(chart_path))


@dp.message(Command("undo"))
async def cmd_undo(message: Message):
    deleted = db.delete_last_expense(message.from_user.id)
    if deleted is None:
        await message.answer("Нечего удалять — записей ещё нет.")
    else:
        await message.answer(
            f"Удалил последнюю запись: {deleted['amount']:.0f} руб. ({deleted['category']})"
        )


@dp.message(F.text)
async def handle_expense(message: Message):
    """
    Обрабатывает обычное текстовое сообщение как запись о трате.
    Ищет в тексте число (сумму), остальной текст использует для определения категории.
    """
    text = message.text.strip()
    match = AMOUNT_PATTERN.search(text)

    if not match:
        await message.answer(
            "Не нашёл сумму в сообщении. Напиши, например: \"кофе 250\""
        )
        return

    amount_str = match.group(1).replace(",", ".")
    amount = float(amount_str)

    category = detect_category(text)
    db.add_expense(message.from_user.id, amount, category, text)

    await message.answer(f"Записал: {amount:.0f} руб. -> {category}")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "Не найден BOT_TOKEN. Создай файл .env и добавь туда BOT_TOKEN=твой_токен"
        )
    db.init_db()
    logger.info("Бот запущен, жду сообщений...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
