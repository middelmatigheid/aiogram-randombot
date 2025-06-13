import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Connecting to database
HOST = os.getenv('HOST')
DBNAME = os.getenv('DBNAME')
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
PORT = os.getenv('PORT')
connection = psycopg2.connect(host=HOST, dbname=DBNAME, user=USER, password=PASSWORD, port=PORT)


# Deleting all tables from database
async def delete_tables():
    with connection.cursor() as cursor:
        cursor.execute("""DROP TABLE IF EXISTS users, images, texts;""")
        connection.commit()


# Creating tables if they don't exist
async def create_tables():
    with connection.cursor() as cursor:
        # Table users stores all key info about users
        # user_id stores user's telegram id
        # nickname stores user's nickname, which is used when generating images and texts to identify the author
        # step stores user's current step
        # page stores current number of viewing page
        # last_page stores last seen page
        # last_nickname stores last used nickname to view generated works by nickname
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users(
                user_id int PRIMARY KEY,
                nickname varchar(50) NOT NULL,
                step varchar(50),
                page int,
                last_page int,
                last_nickname varchar(50));"""
        )
        # Table images stores generated images
        # image_id stores serial number of image, which is also image's saved name in catalog
        # user_id stores image author's telegram id
        # user_image_id stores serial number of user's image
        # nickname stores author's nickname, under which image was generated to identify author
        # nickname_image_id stores serial number of nickname's image
        # date stores date when image was generated in format DD-MM-YYYY
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS images(
                image_id serial PRIMARY KEY,
                user_id int NOT NULL,
                user_image_id int NOT NULL,
                nickname varchar(50) NOT NULL,
                nickname_image_id int NOT NULL,
                date varchar(10) NOT NULL);"""
        )
        # Table texts stores generated texts
        # text_id stores serial number of text
        # user_id stores image author's telegram id
        # user_text_id stores serial number of user's text
        # nickname stores author's nickname, under which text was generated to identify author
        # nickname_text_id stores serial number of nickname's text
        # date stores date when text was generated in format DD-MM-YYYY
        # text stores generated text
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS texts(
                text_id serial PRIMARY KEY,
                user_id int NOT NULL,
                user_text_id int NOT NULL,
                nickname varchar(50) NOT NULL,
                nickname_text_id int NOT NULL,
                date varchar(10) NOT NULL,
                text varchar(250) NOT NULL);"""
        )
        connection.commit()


# Adding new user to the database
async def add_new_user(user_id):
    with connection.cursor() as cursor:
        cursor.execute(f"INSERT INTO users (user_id, nickname, step, page, last_page, last_nickname) VALUES ({user_id}, 'None', 'None', 1, 1, 'None');")
        connection.commit()


# Adding new text to the database
async def add_new_text(user_id, user_text_id, nickname, nickname_text_id, date, text):
    with connection.cursor() as cursor:
        cursor.execute(f"INSERT INTO texts (user_id, user_text_id, nickname, nickname_text_id, date, text) VALUES ({user_id}, {user_text_id}, '{nickname}', {nickname_text_id}, '{date}', '{text}');")
        connection.commit()


# Adding new image to the database
async def add_new_image(user_id, user_image_id, nickname, nickname_image_id, date):
    with connection.cursor() as cursor:
        cursor.execute(f"INSERT INTO images (user_id, user_image_id, nickname, nickname_image_id, date) VALUES ({user_id}, {user_image_id}, '{nickname}', {nickname_image_id}, '{date}');")
        connection.commit()


# Updating user's step
async def update_user_step(user_id, step):
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE users SET step = '{step}' WHERE user_id = {user_id};")
        connection.commit()


# Updating user's page
async def update_user_page(user_id, page):
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE users SET page = {page} WHERE user_id = {user_id};")
        connection.commit()


# Updating user's nickname
async def update_user_nickname(user_id, nickname):
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE users SET nickname = '{nickname}' WHERE user_id = {user_id};")
        connection.commit()


# Updating user's last page
async def update_user_last_page(user_id, last_page):
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE users SET last_page = {last_page} WHERE user_id = {user_id};")
        connection.commit()


# Updating user's last nickname
async def update_user_last_nickname(user_id, last_nickname):
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE users SET last_nickname = '{last_nickname}' WHERE user_id = {user_id};")
        connection.commit()


# Getting all user's info by his telegram id
async def get_user_by_id(user_id):
    with (connection.cursor() as cursor):
        cursor.execute(f"SELECT * FROM users WHERE user_id = {user_id};")
        user = cursor.fetchone()
        if user is None:
            return None
        keys = ['user_id', 'nickname', 'step', 'page', 'last_page', 'last_nickname']
        res = {}
        for i in range(len(keys)):
            res[keys[i]] = user[i]
        return res


# Getting max text id from texts
async def get_max_text_id():
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT MAX(text_id) FROM texts;")
        text_id = cursor.fetchone()[0]
        return text_id


# Getting max text id, which user generated
async def get_max_text_id_by_user(user_id):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT MAX(text_id) FROM texts WHERE user_id = {user_id};")
        text_id = cursor.fetchone()[0]
        return text_id


# Getting max user text id
async def get_max_user_text_id(user_id):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT MAX(user_text_id) FROM texts WHERE user_id = {user_id};")
        text_id = cursor.fetchone()[0]
        return text_id


# Getting max nickname text id
async def get_max_nickname_text_id(nickname):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT MAX(nickname_text_id) FROM texts WHERE nickname = '{nickname}';")
        text_id = cursor.fetchone()[0]
        return text_id


# Getting texts according to the page
async def get_texts(page):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT text_id, nickname, date, text FROM texts WHERE ({(page - 1) * 5} < text_id AND text_id < {page * 5 + 1});")
        texts = cursor.fetchall()
        return texts


# Getting user's texts according to the page
async def get_texts_by_user_id(user_id, page):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT text_id, nickname, date, text FROM texts WHERE (user_id = {user_id} AND {(page - 1) * 5} < user_text_id AND user_text_id < {page * 5 + 1});")
        texts = cursor.fetchall()
        return texts


# Getting nickname's texts according to the page
async def get_texts_by_nickname(nickname, page):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT text_id, nickname, date, text FROM texts WHERE (nickname = '{nickname}' AND {(page - 1) * 5} < nickname_text_id AND nickname_text_id < {page * 5 + 1});")
        texts = cursor.fetchall()
        return texts


# Getting max image id
async def get_max_image_id():
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT MAX(image_id) FROM images;")
        image_id = cursor.fetchone()[0]
        return image_id


# Getting max image id, which user generated
async def get_max_image_id_by_user_id(user_id):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT MAX(image_id) FROM images WHERE user_id = {user_id};")
        image_id = cursor.fetchone()[0]
        return image_id


# Getting max user image id
async def get_max_user_image_id(user_id):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT MAX(user_image_id) FROM images WHERE user_id = {user_id};")
        image_id = cursor.fetchone()[0]
        return image_id


# Getting max nickname image id
async def get_max_nickname_image_id(nickname):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT MAX(nickname_image_id) FROM images WHERE nickname = '{nickname}';")
        image_id = cursor.fetchone()[0]
        return image_id


# Getting images according to the page
async def get_images(page):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT image_id, nickname, date FROM images WHERE ({(page - 1) * 5} < image_id AND image_id < {page * 5 + 1});")
        images = cursor.fetchall()
        return images


# Getting user's images according to the page
async def get_images_by_user_id(user_id, page):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT image_id, nickname, date FROM images WHERE (user_id = {user_id} AND {(page - 1) * 5} < user_image_id AND user_image_id < {page * 5 + 1});")
        images = cursor.fetchall()
        return images


# Getting nickname's images according to the page
async def get_images_by_nickname(nickname, page):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT image_id, nickname, date FROM images WHERE (nickname = '{nickname}' AND {(page - 1) * 5} < nickname_image_id AND nickname_image_id < {page * 5 + 1});")
        images = cursor.fetchall()
        return images

