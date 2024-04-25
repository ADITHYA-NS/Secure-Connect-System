import sqlite3
conn = sqlite3.connect('vanet.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier TEXT NOT NULL,
        username TEXT UNIQUE,
        private_key TEXT
    )
''')
conn.commit()
conn.close()
