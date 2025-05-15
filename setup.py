import sqlite3

conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create new table with status column
c.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    status TEXT
)
''')

# Create the admin account manually
c.execute("INSERT INTO users (username, password, status) VALUES (?, ?, ?)", 
          ("Ruka Kawai", "Shin Haram", NULL))

conn.commit()
conn.close()

print("Database and admin user created successfully.")
