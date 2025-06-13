import os
from dotenv import load_dotenv
import random
from PIL import Image, ImageDraw
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from app.handlers import router
import app.database as db

load_dotenv()

# Connecting to telegram bot
TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()


# Adding 1 text and 1 image to the database from developer to prevent empty database
async def from_developer():
    image = Image.new(mode='RGB', size=(random.randint(0, 250), (random.randint(0, 250))))
    draw = ImageDraw.Draw(image)
    width = image.size[0]
    height = image.size[1]
    for i in range(width):
        for j in range(height):
            r, g, b = [random.randint(0, 255) for i in range(3)]
            draw.point((i, j), (r, g, b))
    image.save('images/1.png')
    del draw
    await db.add_new_text(1, 1, 'разработчик', 1, '10-05-2003', 'привет')
    await db.add_new_image(1, 1, 'разработчик', 1, '20-05-2003')


# Main function to start the bot
async def main():
    await db.delete_tables()
    await db.create_tables()
    await from_developer()
    dp.include_router(router)
    await dp.start_polling(bot)


# Starting the bot
if __name__ == '__main__':
    asyncio.run(main())

    
