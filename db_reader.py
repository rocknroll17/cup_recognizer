import sqlite3
conn = sqlite3.connect('qr.db')
cur = conn.cursor()
cur.execute('SELECT * from qr')
result = cur.fetchall()
for i in range(len(result)):
    print(str(result[i][0])+"|",result[i][1])