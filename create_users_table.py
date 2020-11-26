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
