import sys
import cv2
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QGridLayout, QFrame
from PyQt5.QtCore import pyqtSlot, Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QFontDatabase, QFont
from pyzbar import pyzbar
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn
import time
import os

# FastAPI 앱 생성
api_app = FastAPI()

class Order:
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
        orders.append(Order(id, name, original_price, price))
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
class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.start_server()

    def initUI(self):
        self.main_layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.left_layout.setAlignment(Qt.AlignTop)
        self.right_layout = QVBoxLayout()
        self.right_layout.setAlignment(Qt.AlignCenter)


        # 주문 내역 제목 추가
        self.title_label = QLabel('주문 내역', self)
        self.title_label.setAlignment(Qt.AlignTop)
        self.title_label.setStyleSheet("font-size: 30px;")
        self.left_layout.addWidget(self.title_label)

        # self.qr_label = QLabel('QR코드를 인식하세요', self)
        # self.qr_label.setAlignment(Qt.AlignCenter)
        # self.qr_label.hide()
        # self.left_layout.addWidget(self.qr_label)

        self.result_label = QLabel('', self)
        self.result_label.setAlignment(Qt.AlignLeft)
        self.result_label.hide()
        self.left_layout.addWidget(self.result_label)

        self.camera_label = QLabel(self)
        self.right_layout.addWidget(QLabel("                                                            "))
        self.right_layout.addWidget(self.camera_label)


        # 중앙의 검은색 줄 추가
        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.VLine)
        self.divider.setFrameShadow(QFrame.Sunken)
        self.divider.setLineWidth(2)
        self.divider.setFixedWidth(2)

        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addWidget(self.divider)
        self.main_layout.addLayout(self.right_layout)
        self.setLayout(self.main_layout)
        self.setWindowTitle('')
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #EAE0CC")
        self.showMaximized()

        # 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_buttons)
        self.timer.start(1000)

        self.scanner_thread = None

    def start_qr_scanner(self, id):
        self.current_id = id
        # self.qr_label.show()
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
        # self.result_label.setText(f"스캔된 QR 데이터: {qr_data}")
        # self.result_label.show()
       # self.qr_label.hide()
        # QR 코드 인식이 성공적으로 되면 서버에 정보를 보내서 deploy
        id = self.current_id
        response = requests.post("http://10.210.56.158:5000/api/qr/req", json={"id": id, "cup_id": qr_data})
        if response.status_code == 200:
            orders = [order for order in orders if order.id != id]
            self.remove_order_widget(id)
        else:
            print("이미 대여된 컵입니다.")
        self.camera_label.hide()
        self.stop_qr_scanner()

    def update_buttons(self):
        global orders
        current_orders = [gb.property("order_info").id for gb in self.findChildren(QGroupBox)]

        # Remove orders that are not in the updated orders list
        for order_id in current_orders:
            if order_id not in [order.id for order in orders]:
                self.remove_order_widget(order_id)

        # Add orders that are in the updated orders list but not currently displayed
        for order in orders:
            if order.id not in current_orders:
                self.add_order_widget(order)

    def add_order_widget(self, order):
        group_box = QGroupBox(self)
        group_box.setProperty("order_info", order)
        group_box.setStyleSheet("background-color : khaki")
        group_box.setFixedSize(1000, 200)

        layout = QGridLayout()

        # 이미지 경로 설정
        image_path = os.path.join('img', f"americano.jpg") 
        #   image_path = os.path.join('img', f"{order.name}.jpg") 로 추후에 변경할 것.
        if os.path.exists(image_path): 
            image_label = QLabel(self)
            pixmap = QPixmap(image_path)
            image_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
            layout.addWidget(image_label, 0, 0)
        else:
            print(f"Image not found: {image_path}")

        layout.addWidget(QLabel("ID:"), 0, 1)
        layout.addWidget(QLabel(str(order.id)), 0, 2)  # Convert int to str
        layout.addWidget(QLabel("Name:"), 0, 3)
        layout.addWidget(QLabel(order.name), 0, 4)
        layout.addWidget(QLabel("Original Price:"), 0, 5)
        layout.addWidget(QLabel(str(order.original_price)), 0, 6)  # Convert int to str
        layout.addWidget(QLabel("Price:"), 0, 7)
        layout.addWidget(QLabel(str(order.price)), 0, 8)  # Convert int to str

        self.setStyleSheet("font-size: 20px;")

        qr_button = QPushButton("QR 배정", self)
        qr_button.setFixedSize(120, 120)
        qr_button.clicked.connect(lambda _, o=order: self.start_qr_scanner(o.id))
        layout.addWidget(qr_button, 0, 9)
        qr_button.setStyleSheet("background-color: #C9ADA1;")


        group_box.setLayout(layout)
        self.left_layout.addWidget(group_box)  # Add widget at index 1

    def remove_order_widget(self, order_id):
        for group_box in self.findChildren(QGroupBox):
            if group_box.property("order_info").id == order_id:
                self.left_layout.removeWidget(group_box)
                group_box.deleteLater()
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
    fontDb=QFontDatabase()
    fontDb.addApplicationFont(os.path.join("./font/gamtan_regular.ttf"))
    app.setFont(QFont('gamtan_regular.ttf'))
    ex = MyApp()
    sys.exit(app.exec_())
