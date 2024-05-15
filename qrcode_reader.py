import cv2
import pyzbar.pyzbar as pyzbar
import sqlite3
import random
import time
import qr_code_generater

conn = sqlite3.connect('qr.db')
cur = conn.cursor()

def new_cup(cur, conn, qr_code):
    qr_text = input("생성할 컵의 qr_text를 입력하세요: ")
    qr_code_generater.generate_qr_code(qr_text)
    cur.execute('INSERT INTO qr (qr_code, name) VALUES (?, ?)', (qr_code, name))
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
    cur.execute('SELECT name FROM qr WHERE qr_code = ?', (cup,))
    result = cur.fetchone()[0]
    return result[0] if result else None

while True:
    recog = False
    #option = input("옵션을 선택하세요 (1: QR 코드 인식 시작, 기타: 종료): ")
    if 1:#option == "1"
        time.sleep(2)
        cap = cv2.VideoCapture(0)
        cap.set(3, 640)
        cap.set(4, 480)

        while not recog:
            success, frame = cap.read()
            if not success:
                print("인식이 잘못 되었습니다.")
                break

            for code in pyzbar.decode(frame):
                my_code = code.data.decode('utf-8')
                print("인식 성공 : ", my_code)
                if query_cup(cur, conn, my_code):
                    name = return_cup(cur,conn, my_code)
                    print(name+"의 컵이 반납되었습니다.")
                else:
                    name = str(random.randint(1,10))
                    deploy_cup(cur,conn, my_code, name)
                    print(name+"의 컵이 대여되었습니다.")
                recog = True
                
                # QR 코드 인식 후 OpenCV 창을 닫음
                cap.release()
                cv2.destroyAllWindows()
                break

            cv2.imshow('cup qr code recognizer', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                recog = True  # 'q' 키를 누르면 루프를 종료

        # 내부 while 루프 종료 시 OpenCV 창 닫기
        cap.release()
        cv2.destroyAllWindows()
    else:
        break

# 외부 while 루프 종료 시 모든 자원 해제
cv2.destroyAllWindows()
