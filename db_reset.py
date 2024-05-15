import sqlite3
conn = sqlite3.connect('qr.db')
cur = conn.cursor()
for i in range(1,4):
    cur.execute('INSERT INTO qr (qr_code, name) VALUES (?, ?)', (str(i), str(0)))
conn.commit()