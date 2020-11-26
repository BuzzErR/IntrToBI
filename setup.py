import os
import create_tasks_table
import create_users_table

try:
    os.mkdir("/bills")
except OSError:
    print('bills folder already exists')

try:
    os.mkdir("/goods")
except OSError:
    print('goods folder already exists')

try:
    os.mkdir("/goods")
except OSError:
    print('goods folder already exists')

try:
    create_tasks_table.create_tasks_table()
except Exception as e:
    print(e)

try:
    create_users_table.create_users_table()
except Exception as e:
    print(e)
