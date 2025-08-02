import asyncio
import logging
import os
import json
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)
from aiogram.utils.markdown import bold, italic, underline

# Configure logging
logging.basicConfig(level=logging.INFO)

# Bot token to be replaced with your actual token
API_TOKEN = '7418768945:AAEURvaywFpF8M8eMsNdC1NBaCIGl0YICQI'

# Admin IDs
ADMIN_IDS = [804644988,1694080645,6959774479]  # Replace with your actual admin IDs

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
admin_router = Router()
broadcast_router = Router()

# Dictionary to track users who need a reminder
users_to_remind: Dict[int, datetime] = {}

# Links
REVIEWS_LINK = "https://t.me/+o2dYUSbxIhE4MDMy"

# Images (replace with actual URLs)
WELCOME_IMAGE_URL = "https://postimg.cc/Kk2NjS3Y"
PAYMENT_SUCCESS_IMAGE_URL = "https://postimg.cc/GH5xYsTV"

# Flag for broadcast mode
broadcast_mode = False


# Utility functions
def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMIN_IDS


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Handler for the /start command.
    Sends welcome message with image and description.
    """
    # Reset state when starting
    await state.clear()

    # Send first message with image and description
    welcome_text = (
        "На этой улице всё начинается с улыбки)\n\n"
        "И с десерта... 🍰🧁\n\n"
        "Лимонный кекс, ягодный пирог или банановая запеканка — каждая сладость хранила свою тайну\n\n"
        "Как и каждая хозяйка...\n\n"
        f"Добро пожаловать в закрытый клуб {bold('«отЧАЙанные домохозяйки»')}\n\n"
        "Здесь мы не просто печём. Мы создаём повод заглянуть к соседке. Обсудить, почему торт не поднялся, и кто же всё-таки взял последний эклер\n\n"
        "Стоимость подписки на канал:\n\n"
        "490₽ за 1 месяц\n\n"
        f"И после - присоединяйся к каналу по кнопке {bold('ОПЛАТИТЬ ДОСТУП ✅')}"
    )

    await bot.send_photo(
        message.chat.id,
        photo=WELCOME_IMAGE_URL,
        caption=welcome_text,
    )

    # Schedule the second message after 3 seconds
    await asyncio.sleep(3)

    # Send second message with buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Оплатить доступ ✅", callback_data="pay_access")
        ]
    ])

    second_message = await bot.send_message(
        message.chat.id,
        "Выбери интересующий пункт меню:",
        reply_markup=keyboard
    )

    # Save message_id for later deletion if needed
    await state.update_data(menu_message_id=second_message.message_id)

    # Add user to reminder list
    user_id = message.from_user.id
    users_to_remind[user_id] = datetime.now() + timedelta(days=1)


@router.callback_query(F.data == "pay_access")
async def process_payment_button(callback: CallbackQuery, state: FSMContext):
    """
    Handler for the "Оплатить доступ" button.
    Deletes the old message and sends a new one with tariffs.
    """
    # Get the message ID to delete
    data = await state.get_data()
    message_id_to_delete = data.get("menu_message_id")

    if message_id_to_delete:
        await bot.delete_message(callback.message.chat.id, message_id_to_delete)

    # Send new message with tariffs
    tariffs_text = (
        "Стоимость подписки:\n\n"
        "· 1 месяц 490₽\n\n"
        f"{italic('При оплате картой на месяц, оформляется автосписание')}\n\n"        "Получить доступ 👇"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Получить доступ 🔥", url="https://t.me/tribute/app?startapp=ssXR")],
        [InlineKeyboardButton(text="Назад 🔙", callback_data="back_to_menu")]
    ])

    new_message = await bot.send_message(
        callback.message.chat.id,
        tariffs_text,
        reply_markup=keyboard
    )

    # Save new message ID
    await state.update_data(tariffs_message_id=new_message.message_id)

    # Answer callback to remove loading state
    await callback.answer()


@router.callback_query(F.data == "process_payment")
async def process_successful_payment(callback: CallbackQuery, state: FSMContext):
    """
    Handler for successful payment simulation.
    Sends welcome message to the channel.
    """
    # Remove user from reminder list
    user_id = callback.from_user.id
    if user_id in users_to_remind:
        del users_to_remind[user_id]

    # Welcome message after payment
    welcome_text = (
        "Ты теперь одна из нас.\n"
        "Добро пожаловать в наш закрытый клуб\n"
        "«отЧАЙанные домохозяек»🥧\n"
        "Клуб, где знают: за идеальными скатертями и ароматом выпечки скрываются настоящие истории…🤫"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Войти в канал ➡️", callback_data="enter_channel")]
    ])

    await bot.send_photo(
        callback.message.chat.id,
        photo=PAYMENT_SUCCESS_IMAGE_URL,
        caption=welcome_text,
        reply_markup=keyboard
    )

    # Answer callback to remove loading state
    await callback.answer()


@router.callback_query(F.data == "enter_channel")
async def enter_channel(callback: CallbackQuery):
    """
    Handler for "Войти в канал" button.
    Does nothing as specified.
    """
    await callback.answer()


# Удален обработчик для договора оферты, так как эта функция больше не требуется

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """
    Handler for "Назад" button.
    Returns to the main menu.
    """
    # Get the message ID to delete
    data = await state.get_data()
    message_id_to_delete = data.get("tariffs_message_id")

    if message_id_to_delete:
        await bot.delete_message(callback.message.chat.id, message_id_to_delete)

    # Recreate the main menu
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Оплатить доступ ✅", callback_data="pay_access")
        ]
    ])

    new_message = await bot.send_message(
        callback.message.chat.id,
        "Выбери интересующий пункт меню:",
        reply_markup=keyboard
    )

    # Update the stored message ID
    await state.update_data(menu_message_id=new_message.message_id)

    # Answer callback to remove loading state
    await callback.answer()


async def send_reminders():
    """
    Task to send reminders to users who didn't continue interacting with the bot.
    """
    while True:
        current_time = datetime.now()
        users_to_remove = []

        for user_id, reminder_time in users_to_remind.items():
            if current_time >= reminder_time:
                # Send reminder
                reminder_text = (
                    "Иногда домохозяйки совершают странные поступки 🤔\n"
                    "Они нажимают \"Старт\"… и исчезают\n"
                    "Может быть, их отвлёк капризный ребёнок. Или духовка, которая вдруг решила устроить пожар\n"
                    "А может…\n"
                    "они просто не готовы к сладкому, как жизнь, искушению?\n"
                    "В моем закрытом клубе вас ждут десерты, от которых не уйдёшь просто так\n"
                    "Пироги, печенье, кексы — всё то, что делает дом по-настоящему уютным. И опасно вкусным 🔥\n"
                    "Так что, дорогая… если ты всё ещё где-то рядом — просто ответь\n"
                    "Мы уже налили для тебя чашечку горячего шоколада ☕️"
                )

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="Оплатить доступ ✅", url="https://t.me/tribute/app?startapp=ssXR")
                    ]
                ])

                try:
                    await bot.send_message(user_id, reminder_text, reply_markup=keyboard)
                except Exception as e:
                    logging.error(f"Failed to send reminder to user {user_id}: {e}")

                # Mark user for removal from reminder list
                users_to_remove.append(user_id)

        # Remove processed users
        for user_id in users_to_remove:
            users_to_remind.pop(user_id, None)

        # Check every hour
        await asyncio.sleep(3600)

# Admin command handlers
@admin_router.message(Command(commands="admin"))
async def cmd_admin(message: Message):
    """Admin panel command handler."""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде.")
        return

    admin_text = (
        "📊 <b>Админ панель</b>:\n\n"
        "Выберите действие:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Создать рассылку", callback_data="create_broadcast")]
    ])

    await message.answer(
        admin_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@broadcast_router.callback_query(F.data == "create_broadcast")
async def callback_create_broadcast(callback: CallbackQuery):
    """Start broadcast mode."""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа.", show_alert=True)
        return

    global broadcast_mode
    broadcast_mode = True

    await callback.message.answer(
        "Отправьте сообщение, которое нужно разослать всем активным пользователям.\n\n"
        "<b>Поддерживаются:</b> \n"
        "- <b>Текст</b> (без форматирования)\n"
        "- <b>Фото</b> (С описанием, без форматирования)\n"
        "- <b>Видео</b> (С описанием, без форматирования)\n"
        "- <b>Документ</b> (С описанием, без форматирования)\n"
        "- <b>Аудио</b> (С описанием, без форматирования)\n"
        "- <b>Голосовое сообщение</b> (С описанием, без форматирования)\n"
        "- <b>Видеосообщение</b>",
        parse_mode="HTML"
    )

    await callback.answer()


@broadcast_router.message()
async def handle_broadcast(message: Message):
    """Handle broadcast messages."""
    global broadcast_mode

    # Проверяем, является ли пользователь администратором и активен ли режим рассылки
    if not is_admin(message.from_user.id) or not broadcast_mode:
        return

    # Здесь можно добавить сбор ID пользователей из базы активных чатов бота
    # Но так как мы не сохраняем пользователей, нужно специальное решение

    # Только для примера - отправка сообщения обратно администратору
    await message.answer(
        "Функция рассылки доступна, но необходимо реализовать хранение ID пользователей.\n"
        "Сейчас невозможно отправить массовую рассылку, так как пользователи не сохраняются."
    )

    # Деактивируем режим рассылки
    broadcast_mode = False


async def main():
    """Main function to start the bot."""
    dp.include_router(router)
    dp.include_router(admin_router)
    dp.include_router(broadcast_router)

    # Start the reminder task
    asyncio.create_task(send_reminders())

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

