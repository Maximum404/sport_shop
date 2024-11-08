
import logging
from aiogram import Bot, types
from aiogram.types import InputMediaPhoto, BufferedInputFile
import asyncio
from io import BytesIO
from aiogram.enums import ParseMode

TELEGRAM_BOT_TOKEN = '7113385961:AAGu-5n5gG0iWBZAjpL9WmLr0C5zLNocgXY'
TELEGRAM_CHAT_ID = '-1002262117702'
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_telegram_message(message, photos):
    media_group = []

    for i, photo in enumerate(photos):
        temp_file = BytesIO(photo)
        temp_file.name = f"temp_photo_{i}.jpg"
        media = InputMediaPhoto(media=BufferedInputFile(temp_file.getvalue(), filename=temp_file.name))

        # Добавляем подпись к первой фотографии
        if i == 0:
            truncated_message = truncate_message(message)
            media.caption = truncated_message
            media.parse_mode = ParseMode.MARKDOWN

        media_group.append(media)

    # Отправка медиагруппы
    await bot.send_media_group(chat_id=TELEGRAM_CHAT_ID, media=media_group)

def truncate_message(message, max_length=1024):
    if len(message) <= max_length:
        return message
    return message[:max_length] + '...'
