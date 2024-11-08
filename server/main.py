import sqlite3
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import base64
from contextlib import asynccontextmanager
from telegram_bot import send_telegram_message  # Импортируйте функцию для отправки сообщения

logging.basicConfig(level=logging.INFO)

app = FastAPI()
origins = [
    "https://gymnasticstuff.uk",
    "https://www.gymnasticstuff.uk",
    "https://gymnasticstuff.uk/api/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Функция для преобразования base64 строк в бинарные данные
def base64_to_binary(base64_str):
    return base64.b64decode(base64_str)

# Модель данных для товара
class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float  # Исправлено на float
    send_to_channel: bool
    category: str
    telegram_id: str  # Новое поле для Telegram ID продавца
    photos: list[str]  # Список фотографий в виде base64 строк

def create_connection():
    conn = sqlite3.connect('shop.db', check_same_thread=False)
    return conn

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()

    # Создание таблицы products с новым столбцом telegram_id
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        send_to_channel INTEGER NOT NULL,  -- Поле для отправки поста в канал
        category TEXT NOT NULL,  -- Поле для категории
        telegram_id TEXT  -- Новое поле для Telegram ID продавца
    )
    ''')

    # Создание таблицы photos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        photo BLOB,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')

    conn.commit()
    conn.close()

# Вызов функции create_tables после её определения
create_tables()

@app.get("/api/products", response_model=list[Product])
def get_products():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    products_list = []
    for product in products:
        product_id = product[0]
        cursor.execute("SELECT photo FROM photos WHERE product_id = ?", (product_id,))
        photos = cursor.fetchall()
        photos_base64 = [base64.b64encode(photo[0]).decode('utf-8') for photo in photos]

        product_dict = {
            "id": product_id,
            "name": product[1],
            "description": product[2],
            "price": float(product[3]),  # Исправлено на float
            "send_to_channel": bool(product[4]),
            "category": str(product[5]),  # Преобразуем category в строку
            "telegram_id": str(product[6]),  # Новое поле для Telegram ID продавца
            "photos": photos_base64
        }
        products_list.append(product_dict)

        # Логирование значения category
        logging.info(f"Product category: {product[5]}")

    conn.close()
    logging.info(f"Products list: {[{'id': p['id'], 'name': p['name'], 'description': p['description'], 'price': p['price'], 'send_to_channel': p['send_to_channel'], 'category': p['category'], 'telegram_id': p['telegram_id']} for p in products_list]}")  # Логирование без фотографий
    return products_list

@app.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    cursor.execute("SELECT photo FROM photos WHERE product_id = ?", (product_id,))
    photos = cursor.fetchall()
    photos_base64 = [base64.b64encode(photo[0]).decode('utf-8') for photo in photos]

    product_dict = {
        "id": product[0],
        "name": product[1],
        "description": product[2],
        "price": float(product[3]),  # Исправлено на float
        "send_to_channel": bool(product[4]),
        "category": str(product[5]),  # Преобразуем category в строку
        "telegram_id": str(product[6]),  # Новое поле для Telegram ID продавца
        "photos": photos_base64
    }

    conn.close()
    logging.info(f"Product: {{'id': product_dict['id'], 'name': product_dict['name'], 'description': product_dict['description'], 'price': product_dict['price'], 'send_to_channel': product_dict['send_to_channel'], 'category': product_dict['category'], 'telegram_id': product_dict['telegram_id']}}")  # Логирование без фотографий
    return product_dict

@app.post("/api/products")
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),  # Исправлено на float
    send_to_channel: bool = Form(...),
    category: str = Form(...),
    telegram_id: str = Form(...),  # Новое поле для Telegram ID продавца
    photos: list[UploadFile] = File(...),
):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO products (name, description, price, send_to_channel, category, telegram_id) VALUES (?, ?, ?, ?, ?, ?)",
                       (name, description, price, send_to_channel, str(category), telegram_id))  # Добавление telegram_id
        product_id = cursor.lastrowid

        photo_bytes_list = []
        for photo in photos:
            photo_blob = await photo.read()
            cursor.execute("INSERT INTO photos (product_id, photo) VALUES (?, ?)", (product_id, photo_blob))
            photo_bytes_list.append(photo_blob)

        conn.commit()
        logging.info("Data inserted successfully")

        if send_to_channel:
            def escape_markdown(text):
                special_chars = r'_*[]()~>#+-=|{}!'
                return ''.join(f'\\{char}' if char in special_chars else char for char in text)

            name_escaped = escape_markdown(name)
            price_escaped = escape_markdown(str(price))
            description_escaped = escape_markdown(description)
            category_escaped = escape_markdown(category)

            message = f"*{name_escaped}*\n\n*Цена:* {price_escaped}\n\n*Категория:* {category_escaped}\n\n*Описание:* {description_escaped}"
            logging.info(f"Sending message to Telegram: {message}")
            print(photo_bytes_list)
            print(message)

            await send_telegram_message(message, photo_bytes_list)  # Отправляем все фотографии

    except sqlite3.Error as e:
        logging.error(f"Error inserting data: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        conn.close()

    return {"message": "Product created successfully"}

@app.put("/api/products/{product_id}")
async def update_product(
    product_id: int,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),  # Исправлено на float
    send_to_channel: bool = Form(...),
    category: str = Form(...),
    telegram_id: str = Form(...),  # Новое поле для Telegram ID продавца
    photos: list[UploadFile] = File(...),
):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE products SET name = ?, description = ?, price = ?, send_to_channel = ?, category = ?, telegram_id = ? WHERE id = ?",
                       (name, description, price, send_to_channel, str(category), telegram_id, product_id))  # Добавление telegram_id

        cursor.execute("DELETE FROM photos WHERE product_id = ?", (product_id,))
        for photo in photos:
            photo_blob = await photo.read()
            cursor.execute("INSERT INTO photos (product_id, photo) VALUES (?, ?)", (product_id, photo_blob))

        conn.commit()
        logging.info("Data updated successfully")
    except sqlite3.Error as e:
        logging.error(f"Error updating data: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        conn.close()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product updated successfully"}

@app.delete("/api/products/{product_id}")
def delete_product(product_id: int):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        cursor.execute("DELETE FROM photos WHERE product_id = ?", (product_id,))
        conn.commit()
        logging.info("Data deleted successfully")
    except sqlite3.Error as e:
        logging.error(f"Error deleting data: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        conn.close()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

# Обработчик событий жизненного цикла
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация при старте
    yield
    # Закрытие соединения с базой данных при завершении работы приложения
    conn = create_connection()
    conn.close()

app.router.lifespan_context = lifespan
