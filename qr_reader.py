import cv2
import pyzbar.pyzbar as pyzbar
import sqlite3
import random
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
    cur.execute('UPDATE qr SET name = ? WHERE qr_code = ?', (name, cup))
    conn.commit()

def return_cup(cur, conn, cup):
    cur.execute('SELECT name FROM qr WHERE qr_code = ?', (cup,))
    result = cur.fetchone()[0]
    cur.execute('UPDATE qr SET name = NULL WHERE qr_code = ?', (cup,))
    conn.commit()
    return result
#해당 코드는 아직 해당 qr code가 존재하는 코드인지 인식하지 못함.
#없으면 null이라 그럼
def query_cup(cur, conn, cup):
    cur.execute('SELECT name FROM qr WHERE qr_code = ?', (cup,))
    result = cur.fetchone()[0]
    return result[0] if result else None
def qr_deploy(name):
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    recog = False
    cv2.namedWindow('cup qr code recognizer', cv2.WINDOW_NORMAL)
    while 1:
        success, frame = cap.read()
        if not success:
            break

        for code in pyzbar.decode(frame):
            my_code = code.data.decode('utf-8')
            print("인식 성공 : ", my_code)
            if not query_cup(cur, conn, my_code):
                deploy_cup(cur,conn, my_code, name)
                print(name+"의 컵이 대여되었습니다.")
                cap.release()
                cv2.destroyAllWindows()
                result = True
                recog = True
                break
            else:
                print("Error: 반납 처리 되지 않은 컵입니다.")
                cap.release()
                cv2.destroyAllWindows()
                result = False
                recog = True
        if recog:
            break

        cv2.setWindowProperty('cup qr code recognizer', cv2.WND_PROP_TOPMOST, 1)
        cv2.imshow('cup qr code recognizer', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    return result

def qr_return():
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
                name = return_cup(cur, conn, my_code)
                print(name+"의 컵이 반납되었습니다.")
                cap.release()
                cv2.destroyAllWindows()
                result = True
                recog = True
                break
            else:
                print("Error: 대여 처리 되지 않은 컵입니다.")
                cap.release()
                cv2.destroyAllWindows()
                result = False
                recog = True
        if recog:
            break
        cv2.imshow('cup qr code recognizer', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    return result

if __name__ == "__main__":
    qr_deploy("user"+str(random.randint(1,10)))