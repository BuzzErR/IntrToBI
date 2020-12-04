import sqlite3


def create_users_table():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE USERS 
                (
                [Telegram_id] INTEGER PRIMARY KEY,
                [Name] TEXT,
                [Surname] TEXT, 
                [Age] INTEGER,
                [Phone] INTEGER,
                [Home_lat] REAL, 
                [Home_long] REAL,
                [Radius_of_tasks] REAL,
                [Pass_file] TEXT,
                [Approved] BOOLEAN,
                [Status] TEXT,
                [Courier] BOOLEAN DEFAULT FALSE,
                [Chat_id] INTEGER,        
                [Balance] REAL
                )
                ''')
    conn.commit()
    conn.close()


def create_used_promo():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE USED_PROMO
                    (
                    [id] INTEGER PRIMARY KEY AUTOINCREMENT, 
                    [User_telegram_id] INTEGER, 
                    [Code] TEXT
                    )
                    ''')
    conn.commit()
    conn.close()


def create_tasks_table():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE TASKS 
                (
                [id] INTEGER PRIMARY KEY AUTOINCREMENT ,
                [Owner_telegram_id] INTEGER,
                [Description] TEXT,
                [Price_for_delivery] REAL,
                [Price_for_goods] REAL,   
                [Age_limit] BOOLEAN,
                [Courier] INTEGER, 
                [Home_lat] REAL,
                [Home_long] REAL,
                [Is_completed] BOOLEAN DEFAULT FALSE,
                [Datetime] TEXT,
                [Photo_of_bill] TEXT, 
                [Photo_of_products] TEXT,
                [Total_real_price] REAL
                )
                ''')
    conn.commit()
    conn.close()
