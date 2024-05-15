import sqlite3
conn = sqlite3.connect('qr.db')
cur = conn.cursor()
cur.execute('SELECT * from qr')
result = cur.fetchall()
print(result)
for i in range(len(result)):
    cur.execute('UPDATE qr SET name = NULL WHERE qr_code = ?', (result[i][0],))
conn.commit()