import sqlite3
import random

conn = sqlite3.connect("users.db")
cursor = conn.cursor()
len_username = random.randint(1,9)
username = ""
for _ in range(len_username):
    username  += chr(random.randint(65,90))
password = ""
for _ in range(len_username):
    password  += chr(random.randint(65,90))
cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
conn.commit()
conn.close()