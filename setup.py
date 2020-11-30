import os
import generate_db

try:
    os.mkdir("bills")
except OSError:
    print('bills folder already exists')

try:
    os.mkdir("users")
except OSError:
    print('users folder already exists')

try:
    os.mkdir("goods")
except OSError:
    print('goods folder already exists')

try:
    generate_db.create_tasks_table()
except Exception as e:
    print(e)

try:
    generate_db.create_users_table()
except Exception as e:
    print(e)

try:
    generate_db.create_used_promo()
except Exception as e:
    print(e)