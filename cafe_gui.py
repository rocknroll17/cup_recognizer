import sys
import cv2
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import pyqtSlot, Qt, QMetaObject, Q_ARG, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from pyzbar import pyzbar
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn
import qr_reader
import time

# FastAPI 앱 생성
api_app = FastAPI()

class order:
    def __init__(self, id, name, original_price, price):
        self.id = id
        self.name = name
        self.original_price = original_price
        self.price = price

    def __repr__(self):
        return str(self.id)
    
    def __str__(self):
        return str(self.id)


# 현재 버튼 목록
orders = []
templates = Jinja2Templates(directory="templates")

# CORS 설정
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api_app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@api_app.post("/order_request")
async def create_button(request: Request):
    global orders
    datareq = await request.json()
    datareq = datareq.get("orderItems")
    print(datareq)
    for i in datareq:
        id = i.get("id")
        name = i.get("name")
        original_price = i.get("original_price")
        price = i.get("price")
        orders.append(order(id, name, original_price, price))
        print(orders)
    return JSONResponse(content={"message": "Button created successfully"})

# OpenCV QR 코드 스캐너 스레드
class QRScannerThread(QThread):
    qr_data_signal = pyqtSignal(str)
    frame_signal = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanning = True

    def run(self):
        cap = cv2.VideoCapture(0)
        while self.scanning:
            ret, frame = cap.read()
            if ret:
                decoded_objects = pyzbar.decode(frame)
                for obj in decoded_objects:
                    qr_data = obj.data.decode("utf-8")
                    self.qr_data_signal.emit(qr_data)
                    self.scanning = False  # QR 코드가 인식되면 스캐너 스레드 종료
                    break
                self.frame_signal.emit(frame)
            else:
                break
        cap.release()

    def stop(self):
        self.scanning = False
        self.wait()

# PyQt5 앱 생성
# PyQt5 앱 생성
class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.start_server()

    def initUI(self):
        self.main_layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.left_layout.setAlignment(Qt.AlignCenter)
        self.right_layout = QVBoxLayout()
        self.right_layout.setAlignment(Qt.AlignCenter)

        self.qr_label = QLabel('QR코드를 인식하세요', self)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.hide()
        self.left_layout.addWidget(self.qr_label)

        self.result_label = QLabel('', self)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.hide()
        self.left_layout.addWidget(self.result_label)

        self.camera_label = QLabel(self)
        self.right_layout.addWidget(self.camera_label)

        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addLayout(self.right_layout)
        self.setLayout(self.main_layout)
        self.setWindowTitle('QR 코드 인식기')
        self.setGeometry(100, 100, 800, 600)
        self.show()

        # 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_buttons)
        self.timer.start(1000)

        self.scanner_thread = None

    def start_qr_scanner(self, id):
        self.current_id = id
        self.qr_label.show()
        self.result_label.hide()
        self.scanner_thread = QRScannerThread()
        self.scanner_thread.qr_data_signal.connect(self.handle_qr_result)
        self.scanner_thread.frame_signal.connect(self.update_camera_frame)
        self.scanner_thread.start()
        time.sleep(0.8)
        self.camera_label.show()

    def stop_qr_scanner(self):
        if self.scanner_thread is not None:
            self.scanner_thread.stop()

    @pyqtSlot(object)
    def update_camera_frame(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        self.camera_label.setPixmap(QPixmap.fromImage(q_img))
        
    @pyqtSlot(str)
    def handle_qr_result(self, qr_data):
        global orders
        self.result_label.setText(f"스캔된 QR 데이터: {qr_data}")
        self.result_label.show()
        self.qr_label.hide()
        # QR 코드 인식이 성공적으로 되면 서버에 정보를 보내서 deploy
        id = self.current_id
        response = requests.post("http://10.210.56.158:5000/api/qr/req", json={"id":id, "cup_id": qr_data})
        if response.status_code == 200:
            orders = [order for order in orders if order.id != id]
            self.remove_button(id)
        else:
            print("이미 대여된 컵입니다.")
        self.camera_label.hide()
        self.stop_qr_scanner()

    def update_buttons(self):
        global orders
        current_buttons = [btn.text() for btn in self.findChildren(QPushButton)]

        # Remove buttons that are not in the updated orders list
        for btn in current_buttons:
            if btn not in [order.id for order in orders]:
                self.remove_button(btn)

        # Add buttons that are in the updated orders list but not currently displayed
        for order in orders:
            if order.id not in current_buttons:
                self.add_button(order)


    def add_button(self, order):
        button = QPushButton(str(order.id), self)
        button.setFixedSize(150, 50)
        button.clicked.connect(lambda _, u=order.id: self.start_qr_scanner(u))
        self.left_layout.addWidget(button)

    def remove_button(self, username):
        for btn in self.findChildren(QPushButton):
            if btn.text() == username:
                self.left_layout.removeWidget(btn)
                btn.deleteLater()
                break

    def start_server(self):
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def run_server(self):
        uvicorn.run(api_app, host="0.0.0.0", port=4440)

    def closeEvent(self, event):
        if self.scanner_thread is not None:
            self.stop_qr_scanner()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())