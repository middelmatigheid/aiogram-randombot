import os
from dotenv import load_dotenv
import random
import datetime
from math import ceil
from PIL import Image, ImageDraw
from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, KeyboardButton, FSInputFile
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
import app.database as db

load_dotenv()

# Connecting to telegram bot
TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
router = Router()


# Building keyboard markup
async def add_markup(*buttons):
    keyboard = ReplyKeyboardBuilder()
    for button in buttons:
        keyboard.row(KeyboardButton(text=button))
    return keyboard.as_markup(resize_keyboard=True)


# Generating date in format DD-MM-YYYY (Moscow timezone)
async def add_date():
    date = str(datetime.datetime.utcnow() + datetime.timedelta(hours=3))[:10]
    date = date[8:] + date[4:8] + date[:4]
    return date


# Function checks if the number of page is correct, returns True if so
# Returns False, sending message to the user that the number of page is incorrect
async def check_page(message, num):
    user = await db.get_user_by_id(message.chat.id)
    if num < 6 and user['page'] != 1:
        await message.answer('Некорректный номер страницы, попробуй снова', reply_markup=await add_markup('Посмотреть мои работы', 'Поиск по автору', 'Главное меню'))
        return False
    elif user['page'] > ceil(num / 5):
        await db.update_user_page(message.chat.id, user['page'] - 1)
        await message.answer('Некорректный номер страницы, попробуй снова', reply_markup=await add_markup('Предыдущая страница', 'Ввести номер страницы', 'Посмотреть мои работы', 'Поиск по автору', 'Главное меню'))
        return False
    elif user['page'] == 0:
        await db.update_user_page(message.chat.id, 1)
        await message.answer('Некорректный номер страницы, попробуй снова', reply_markup=await add_markup('Следующая страница',  'Ввести номер страницы', 'Посмотреть мои работы', 'Поиск по автору', 'Главное меню'))
        return False
    else:
        return True


# Function creates and returns correct ReplyKeyboardMarkup according to the number of page
async def add_page_markup(page, num):
    if page < ceil(num / 5) and page != 1:
        markup = await add_markup('Следующая страница', 'Предыдущая страница', 'Ввести номер страницы', 'Посмотреть мои работы', 'Поиск по автору', 'Главное меню')
    elif page != 1:
        markup = await add_markup('Предыдущая страница', 'Ввести номер страницы', 'Посмотреть мои работы', 'Поиск по автору', 'Главное меню')
    elif page < ceil(num / 5):
        markup = await add_markup('Следующая страница', 'Ввести номер страницы', 'Посмотреть мои работы', 'Поиск по автору', 'Главное меню')
    else:
        markup = await add_markup('Посмотреть мои работы', 'Поиск по автору', 'Главное меню')
    return markup


# Function creates and sends message of previously generated texts, returns True if everything is fine, returns False otherwise
async def text_page(message, nickname=None):
    user = await db.get_user_by_id(message.chat.id)
    message_text = ''

    if user['step'] == 'viewing own generated texts':
        texts = await db.get_texts_by_user_id(message.chat.id, user['page'])
        texts_amount = await db.get_max_user_text_id(message.chat.id)
        if not texts:
            await message.answer('У тебя еще нет сгенерированных работ, попробуй позже')
            return False
        if not await check_page(message, texts_amount):
            return False
        for elem in texts:
            if elem[0] != 1:
                message_text += '\n'
            message_text += f'\n\n{elem[3]}\n\nТекст <i><b>№{elem[0]}</b></i> сгенерирован <i><b>{elem[2]}</b></i> пользователем <i><b>{elem[1]}</b></i>'
        message_text += f'\n\n\nСтраница <i><b>{user["page"]}</b></i> из <i><b>{ceil(texts_amount / 5)}</b></i>'

    elif user['step'] == 'viewing nickname generated texts':
        texts = await db.get_texts_by_nickname(nickname, user['page'])
        texts_amount = await db.get_max_nickname_text_id(nickname)
        if not texts:
            await message.answer('У данного автора еще нет работ, попробуй другого')
            return False
        if not await check_page(message, texts_amount):
            return False
        for elem in texts:
            if elem[0] != 1:
                message_text += '\n'
            message_text += f'\n\n{elem[3]}\n\nТекст <i><b>№{elem[0]}</b></i> сгенерирован <i><b>{elem[2]}</b></i> пользователем <i><b>{elem[1]}</b></i>'
        message_text += f'\n\n\nСтраница <i><b>{user["page"]}</b></i> из <i><b>{ceil(texts_amount / 5)}</b></i>'

    else:
        texts = await db.get_texts(user['page'])
        texts_amount = await db.get_max_text_id()
        if not await check_page(message, texts_amount):
            return False
        for elem in texts:
            if elem[0] != 1:
                message_text += '\n'
            message_text += f'\n\n{elem[3]}\n\nТекст <i><b>№{elem[0]}</b></i> сгенерирован <i><b>{elem[2]}</b></i> пользователем <i><b>{elem[1]}</b></i>'
        message_text += f'\n\n\nСтраница <i><b>{user["page"]}</b></i> из <i><b>{ceil(texts_amount / 5)}</b></i>'
    await message.answer(message_text, reply_markup=await add_page_markup(user['page'], texts_amount))
    return True


# Function creates and sends message of previously generated images, returns True if everything is fine, returns False otherwise
async def image_page(message, nickname=None):
    user = await db.get_user_by_id(message.chat.id)

    if user['step'] == 'viewing own generated images':
        images = await db.get_images_by_user_id(message.chat.id, user['page'])
        images_amount = await db.get_max_user_image_id(message.chat.id)
        if not images:
            await message.answer('У тебя еще нет сгенерированных работ, попробуй позже')
            return False
        if not await check_page(message, images_amount):
            return False
        for elem in images[:- 1]:
            await bot.send_photo(message.chat.id, photo=FSInputFile(f'images/{elem[0]}.png'), caption=f'Картинка <i><b>№{elem[0]}</b></i> сгенерирована <i><b>{elem[2]}</b></i> под именем <i><b>{elem[1]}</b></i>')
        await bot.send_photo(message.chat.id, photo=FSInputFile(f'images/{images[-1][0]}.png'), caption=f'Картинка <i><b>№{images[-1][0]}</b></i> сгенерирована <i><b>{images[-1][2]}</b></i> под именем <i><b>{images[-1][1]}</b></i>\n\nСтраница <i><b>{user["page"]}</b></i> из <i><b>{ceil(images_amount / 5)}</b></i>', reply_markup=await add_page_markup(user['page'], images_amount))

    elif user['step'] == 'viewing nickname generated images':
        images = await db.get_images_by_nickname(nickname, user['page'])
        images_amount = await db.get_max_nickname_image_id(nickname)
        if not images:
            await message.answer('У данного автора еще нет работ, попробуй другого')
            return False
        if not await check_page(message, images_amount):
            return False
        for elem in images[:- 1]:
            await bot.send_photo(message.chat.id, photo=FSInputFile(f'images/{elem[0]}.png'), caption=f'Картинка <i><b>№{elem[0]}</b></i> сгенерирована <i><b>{elem[2]}</b></i> пользователем <i><b>{elem[1]}</b></i>')
        await bot.send_photo(message.chat.id, photo=FSInputFile(f'images/{images[-1][0]}.png'), caption=f'Картинка <i><b>№{images[-1][0]}</b></i> сгенерирована <i><b>{images[-1][2]}</b></i> пользователем <i><b>{images[-1][1]}</b></i>\n\nСтраница <i><b>{user["page"]}</b></i> из <i><b>{ceil(images_amount / 5)}</b></i>', reply_markup=await add_page_markup(user['page'], images_amount))

    else:
        images = await db.get_images(user['page'])
        images_amount = await db.get_max_image_id()
        if not await check_page(message, images_amount):
            return False
        for elem in images[:- 1]:
            await bot.send_photo(message.chat.id, photo=FSInputFile(f'images/{elem[0]}.png'), caption=f'Картинка <i><b>№{elem[0]}</b></i> сгенерирована <i><b>{elem[2]}</b></i> пользователем <i><b>{elem[1]}</b></i>')
        await bot.send_photo(message.chat.id, photo=FSInputFile(f'images/{images[-1][0]}.png'), caption=f'Картинка <i><b>№{images[-1][0]}</b></i> сгенерирована <i><b>{images[-1][2]}</b></i> пользователем <i><b>{images[-1][1]}</b></i>\n\nСтраница <i><b>{user["page"]}</b></i> из <i><b>{ceil(images_amount / 5)}</b></i>', reply_markup=await add_page_markup(user['page'], images_amount))
    return True


# Processing start command
@router.message(Command('start'))
async def command_start(message: Message):
    user = await db.get_user_by_id(message.chat.id)
    if user is None:
        await db.add_new_user(message.chat.id)
    await message.answer('Выбери одно из действий, чтобы начать', reply_markup=await add_markup('Сгенерировать новое', 'Посмотреть существующее'))


# Processing text message
@router.message(F.text)
async def main_menu(message: Message):
    user = await db.get_user_by_id(message.chat.id)
    if user is None:
        await db.add_new_user(message.chat.id)
        user = await db.get_user_by_id(message.chat.id)

    # 'Main menu' button
    # Choosing action
    if message.text == 'Главное меню':
        await db.update_user_step(message.chat.id, 'None')
        await db.update_user_page(message.chat.id, 1)
        await db.update_user_last_page(message.chat.id, 1)
        await db.update_user_last_nickname(message.chat.id, 'None')
        await message.answer('Выбери одно из действий', reply_markup=await add_markup('Сгенерировать новое', 'Посмотреть существующее'))

    # 'Generate new' button
    # Choosing what to generate
    elif message.text == 'Сгенерировать новое':
        if user['nickname'] == 'None':
            await db.update_user_step(message.chat.id, 'adding nickname')
            await message.answer('Введи имя, которое будет видно другим пользователям', reply_markup=await add_markup('Сгенерировать новое', 'Посмотреть существующее'))
        else:
            await db.update_user_step(message.chat.id, 'generating new')
            await db.update_user_page(message.chat.id, 1)
            await db.update_user_last_page(message.chat.id, 1)
            await db.update_user_last_nickname(message.chat.id, 'None')
            await message.answer('Выбери, что сгенерировать', reply_markup=await add_markup('Текст', 'Картинку', 'Изменить имя', 'Главное меню'))

    # Generate new 'text' button
    # Generating and sending new text
    elif (user is not None and user['step'] == 'generating new' and message.text == 'Текст') or (user is not None and user['step'] == 'generating new text' and message.text == 'Сгенерировать еще'):
        generated_text = ''.join(random.choices('ЙФЯЦЫЧУВСКАМЕПИНРТГОЬШЛБЩДЮЗЖХЭЪйфяцычувскамепинртгоьшлбщдюзжхэъ 0123456789,.!?', k=random.randint(1, 250)))
        user_text_id = await db.get_max_user_text_id(message.chat.id)
        if user_text_id is None:
            user_text_id = 0
        nickname_text_id = await db.get_max_nickname_text_id(user['nickname'])
        if nickname_text_id is None:
            nickname_text_id = 0
        date = await add_date()
        await db.add_new_text(message.chat.id, user_text_id + 1, user['nickname'], nickname_text_id + 1, date, generated_text)
        text_id = await db.get_max_text_id_by_user(message.chat.id)
        await db.update_user_step(message.chat.id, 'generating new text')
        await message.answer(f'{generated_text}\n\nТвой текст <i><b>№{text_id}</b></i> сгенерирован <i><b>{date}</b></i> под именем <i><b>{user["nickname"]}</b></i>', reply_markup=await add_markup('Сгенерировать еще', 'Главное меню'))

    # Generate new 'image' button
    # Generating and sending new image
    elif (user is not None and user['step'] == 'generating new' and message.text == 'Картинку') or (user is not None and user['step'] == 'generating new image' and message.text == 'Сгенерировать еще'):
        image = Image.new(mode='RGB', size=(random.randint(0, 250), (random.randint(0, 250))))
        draw = ImageDraw.Draw(image)
        width = image.size[0]
        height = image.size[1]
        for i in range(width):
            for j in range(height):
                r, g, b = [random.randint(0, 255) for i in range(3)]
                draw.point((i, j), (r, g, b))
        user_image_id = await db.get_max_user_image_id(message.chat.id)
        if user_image_id is None:
            user_image_id = 0
        nickname_image_id = await db.get_max_nickname_image_id(user['nickname'])
        if nickname_image_id is None:
            nickname_image_id = 0
        date = await add_date()
        await db.add_new_image(message.from_user.id, user_image_id + 1, user['nickname'], nickname_image_id + 1, date)
        image_id = await db.get_max_image_id_by_user_id(message.chat.id)
        image.save(f'images/{image_id}.png')
        await db.update_user_step(message.chat.id, 'generating new image')
        await bot.send_photo(message.chat.id, photo=FSInputFile(f'images/{image_id}.png'), caption=f'Твоя картинка <i><b>№{image_id}</b></i> сгенерирована <i><b>{date}</b></i> под именем <i><b>{user["nickname"]}</b></i>', reply_markup=await add_markup('Сгенерировать еще', 'Главное меню'))
        del draw

    # 'View existing' button
    # Choosing what to view
    elif message.text == 'Посмотреть существующее':
        await db.update_user_step(message.chat.id, 'None')
        await message.answer('Выбери, что посмотреть', reply_markup=await add_markup('Тексты', 'Картинки', 'Главное меню'))

    # View existing 'texts' button
    # Viewing previously generated texts
    elif message.text == 'Тексты':
        await db.update_user_step(message.chat.id, 'viewing generated texts')
        await db.update_user_page(message.chat.id, 1)
        await text_page(message)

    # 'Next text page' button
    # Next page of previously generated texts
    elif user is not None and user['step'].split()[-1] == 'texts' and message.text == 'Следующая страница':
        await db.update_user_page(message.chat.id, user['page'] + 1)
        if user['step'] == 'viewing nickname generated texts':
            await text_page(message, user['last_nickname'])
        else:
            await text_page(message)

    # 'Previous text page' button
    # Previous page of previously generated texts
    elif user is not None and user['step'].split()[-1] == 'texts' and message.text == 'Предыдущая страница':
        await db.update_user_page(message.chat.id, user['page'] - 1)
        if user['step'] == 'viewing nickname generated texts':
            await text_page(message, user['last_nickname'])
        else:
            await text_page(message)

    # 'View my texts' button
    # Viewing user's generated texts
    elif user is not None and user['step'].split()[-1] == 'texts' and message.text == 'Посмотреть мои работы':
        await db.update_user_step(message.chat.id, 'viewing own generated texts')
        await db.update_user_page(message.chat.id, 1)
        await text_page(message)

    # 'View texts by author' button
    # Viewing generated texts by author's nickname
    elif user is not None and user['step'].split()[-1] == 'texts' and message.text == 'Поиск по автору':
        await db.update_user_step(message.chat.id, 'viewing nickname generated texts')
        await db.update_user_page(message.chat.id, 1)
        await message.answer('Напиши имя автора, чьи работы ты хочешь найти')

    # 'Enter the number of text page' button
    # Viewing page according to the num of page
    elif user is not None and user['step'].split()[-1] == 'texts' and message.text == 'Ввести номер страницы':
        if user['step'] == 'viewing own generated texts':
            await db.update_user_step(message.chat.id, 'viewing page own generated texts')
        elif user['step'] == 'viewing nickname generated texts':
            await db.update_user_step(message.chat.id, 'viewing page nickname generated texts')
        else:
            await db.update_user_step(message.chat.id, 'viewing page generated texts')
        await message.answer('Введи номер страницы')

    elif user is not None and user['step'].split()[-1] == 'texts' and user['step'].split()[1] == 'page':
        if not message.text.isdigit():
            await message.answer('Некорректный номер страницы')
        else:
            await db.update_user_last_page(message.chat.id, user['page'])
            await db.update_user_page(message.chat.id, int(message.text))
            if user['step'] == 'viewing page own generated texts':
                await db.update_user_step(message.chat.id, 'viewing own generated texts')
                if not await text_page(message):
                    await db.update_user_page(message.chat.id, user['last_page'])
                await db.update_user_step(message.chat.id, 'viewing page own generated texts')
            elif user['step'] == 'viewing page nickname generated texts':
                await db.update_user_step(message.chat.id, 'viewing nickname generated texts')
                if not await text_page(message, user['last_nickname']):
                    await db.update_user_page(message.chat.id, user['last_page'])
                await db.update_user_step(message.chat.id, 'viewing page nickname generated texts')
            else:
                await db.update_user_step(message.chat.id, 'viewing generated texts')
                if not await text_page(message):
                    await db.update_user_page(message.chat.id, user['last_page'])
                await db.update_user_step(message.chat.id, 'viewing page generated texts')

    elif user is not None and user['step'] == 'viewing nickname generated texts':
        if await text_page(message, message.text):
            await db.update_user_last_nickname(message.chat.id, message.text)

    # View existing 'images' button
    # Viewing previously generated images
    elif message.text == 'Картинки':
        await db.update_user_step(message.chat.id, 'viewing generated images')
        await db.update_user_page(message.chat.id, 1)
        await image_page(message)

    # 'Next image page' button
    # Next page of previously generated images
    elif user is not None and user['step'].split()[-1] == 'images' and message.text == 'Следующая страница':
        await db.update_user_page(message.chat.id, user['page'] + 1)
        if user['step'] == 'viewing nickname generated images':
            await image_page(message, user['last_nickname'])
        else:
            await image_page(message)

    # 'Previous image page' button
    # Previous page of previously generated images
    elif user is not None and user['step'].split()[-1] == 'images' and message.text == 'Предыдущая страница':
        await db.update_user_page(message.chat.id, user['page'] - 1)
        if user['step'] == 'viewing nickname generated images':
            await image_page(message, user['last_nickname'])
        else:
            await image_page(message)

    # 'View my images' button
    # Viewing user's generated images
    elif user is not None and user['step'].split()[-1] == 'images' and message.text == 'Посмотреть мои работы':
        await db.update_user_step(message.chat.id, 'viewing own generated images')
        await db.update_user_page(message.chat.id, 1)
        await image_page(message)

    # 'View images by author' button
    # Viewing generated texts by author's nickname
    elif user is not None and user['step'].split()[-1] == 'images' and message.text == 'Поиск по автору':
        await db.update_user_step(message.chat.id, 'viewing nickname generated images')
        await db.update_user_page(message.chat.id, 1)
        await message.answer('Напиши имя автора, чьи работы ты хочешь найти')

    # 'Enter the number of image page' button
    # Viewing page according to the num of page
    elif user is not None and user['step'].split()[-1] == 'images' and message.text == 'Ввести номер страницы':
        if user['step'] == 'viewing own generated images':
            await db.update_user_step(message.chat.id, 'viewing page own generated images')
        elif user['step'] == 'viewing nickname generated images':
            await db.update_user_step(message.chat.id, 'viewing page nickname generated images')
        else:
            await db.update_user_step(message.chat.id, 'viewing page generated images')
        await message.answer('Введи номер страницы')

    elif user is not None and user['step'].split()[-1] == 'images' and user['step'].split()[1] == 'page':
        if not message.text.isdigit():
            await message.answer('Некорректный номер страницы')
        else:
            await db.update_user_last_page(message.chat.id, user['page'])
            await db.update_user_page(message.chat.id, int(message.text))
            if user['step'] == 'viewing page own generated images':
                await db.update_user_step(message.chat.id, 'viewing own generated images')
                if not await image_page(message):
                    await db.update_user_page(message.chat.id, user['last_page'])
                await db.update_user_step(message.chat.id, 'viewing page own generated images')
            elif user['step'] == 'viewing page nickname generated images':
                await db.update_user_step(message.chat.id, 'viewing nickname generated images')
                if not await image_page(message, ['last_nickname']):
                    await db.update_user_page(message.chat.id, user['last_page'])
                await db.update_user_step(message.chat.id, 'viewing page nickname generated images')
            else:
                await db.update_user_step(message.chat.id, 'viewing generated images')
                if not await image_page(message):
                    await db.update_user_page(message.chat.id, user['last_page'])
                await db.update_user_step(message.chat.id, 'viewing page generated images')

    elif user is not None and user['step'] == 'viewing nickname generated images':
        if await image_page(message, message.text):
            await db.update_user_last_nickname(message.chat.id, message.text)

    # Adding user's nickname to the database
    elif user is not None and user['step'] == 'adding nickname':
        if len(message.text) > 50 and not message.text.isalnum():
            await message.answer('Длина имени не должна превышать 50 символов, в имени присутствуют некорректные символы, попробуй снова', eply_markup=await add_markup('Сгенерировать новое', 'Посмотреть существующее'))
        elif len(message.text) > 50:
            await message.answer('Длина имени не должна превышать 50 символов, попробуй снова', reply_markup=await add_markup('Сгенерировать новое', 'Посмотреть существующее'))
        elif not message.text.isalnum():
            await message.answer('В имени присутствуют некорректные символы, попробуй снова', reply_markup=await add_markup('Сгенерировать новое', 'Посмотреть существующее'))
        else:
            await db.update_user_nickname(message.chat.id, message.text)
            await db.update_user_step(message.chat.id, 'generating new')
            await message.answer('Выбери, что сгенерировать', reply_markup=await add_markup('Текст', 'Картинку', 'Изменить имя', 'Главное меню'))

    # 'Edit name' button
    # Updating nickname in database
    elif message.text == 'Изменить имя':
        await db.update_user_step(message.chat.id, 'editing nickname')
        await message.answer('Введи новое имя, которое будет видно другим пользователям')

    elif user is not None and user['step'] == 'editing nickname':
        if len(message.text) > 50 and not message.text.isalnum():
            await message.answer('Длина имени не должна превышать 50 символов, в имени присутствуют некорректные символы, попробуй снова')
        elif len(message.text) > 50:
            await message.answer('Длина имени не должна превышать 50 символов, попробуй снова')
        elif not message.text.isalnum():
            await message.answer('В имени присутствуют некорректные символы, попробуй снова')
        else:
            await db.update_user_nickname(message.chat.id, message.text)
            await db.update_user_step(message.chat.id, 'generating new')
            await message.answer('Имя успешно изменено, выбери, что сгенерировать', reply_markup=await add_markup('Текст', 'Картинку', 'Изменить имя', 'Главное меню'))

    else:
        await db.update_user_step(message.chat.id, 'None')
        await db.update_user_page(message.chat.id, 1)
        await db.update_user_last_page(message.chat.id, 1)
        await db.update_user_last_nickname(message.chat.id, 'None')
        await message.answer('Неизвестная команда, попробуй снова', reply_markup=await add_markup('Сгенерировать новое', 'Посмотреть существующее'))