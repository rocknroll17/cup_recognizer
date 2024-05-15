import cv2
import pyzbar.pyzbar as pyzbar
import sqlite3
import random
import time
import qr_code_generater

conn = sqlite3.connect('qr.db')
cur = conn.cursor()

def new_cup(cur, conn, qr_code):
    qr_code_generater.generate_qr_code(qr_code)
    cur.execute('INSERT INTO qr (qr_code, name) VALUES (?, ?)', (qr_code, None))
    conn.commit()

def delete_cup():
    pass

def deploy_cup(cur, conn, cup, name):
    cur.execute('UPDATE qr SET name = '+name+' WHERE qr_code = '+cup)
    conn.commit()

def return_cup(cur, conn, cup):
    cur.execute('SELECT name FROM qr WHERE qr_code = '+cup)
    result = cur.fetchone()[0]
    cur.execute('UPDATE qr SET name = NULL WHERE qr_code = '+cup)
    conn.commit()
    return result
#해당 코드는 아직 해당 qr code가 존재하는 코드인지 인식하지 못함.
#없으면 null이라 그럼
def query_cup(cur, conn, cup):
    cur.execute('SELECT name FROM qr WHERE qr_code = ?', (cup))
    result = cur.fetchone()[0]
    return result[0] if result else None

def instance():
    conn = sqlite3.connect('qr.db')
    cur = conn.cursor()
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    recog = False
    while 1:
        success, frame = cap.read()
        if not success:
            break

        for code in pyzbar.decode(frame):
            my_code = code.data.decode('utf-8')
            print("인식 성공 : ", my_code)
            if query_cup(cur, conn, my_code):
                print("컵이 반납되었습니다.")
                cap.release()
                cv2.destroyAllWindows()
                result = True
                recog = True
                break
            else:
                cap.release()
                cv2.destroyAllWindows()
                recog = True
        if recog:
            break