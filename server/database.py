import sqlite3

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
