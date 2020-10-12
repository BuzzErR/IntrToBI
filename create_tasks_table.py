import sqlite3

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
