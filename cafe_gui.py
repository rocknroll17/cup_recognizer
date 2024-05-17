import sys
import cv2
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import pyqtSlot, Qt, QMetaObject, Q_ARG
from pyzbar import pyzbar

class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # 전체 레이아웃 설정
        self.main_layout = QVBoxLayout()

        # 중앙 정렬을 위한 레이아웃
        self.central_layout = QVBoxLayout()
        self.central_layout.setAlignment(Qt.AlignCenter)

        # '배정' 버튼 생성 및 추가
        self.assign_button = QPushButton('컵 배정하기', self)
        self.assign_button.setFixedSize(150, 50)
        self.assign_button.clicked.connect(self.show_qr_message)
        self.central_layout.addWidget(self.assign_button)

        # QR 코드 안내 문구와 '다음' 버튼 생성 (초기에는 숨김)
        self.qr_label = QLabel('QR코드를 인식하세요', self)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.hide()
        self.central_layout.addWidget(self.qr_label)

        self.next_button = QPushButton('다음', self)
        self.next_button.setFixedSize(150, 50)
        self.next_button.clicked.connect(self.show_assign_button)
        self.next_button.hide()
        self.central_layout.addWidget(self.next_button)

        # QR 코드 인식 결과 라벨
        self.result_label = QLabel('', self)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.hide()
        self.central_layout.addWidget(self.result_label)

        # 중앙 레이아웃을 메인 레이아웃에 추가
        self.main_layout.addLayout(self.central_layout)
        self.main_layout.setAlignment(Qt.AlignCenter)

        # 레이아웃을 윈도우에 설정
        self.setLayout(self.main_layout)

        # 윈도우 속성 설정
        self.setWindowTitle('배정 버튼 클릭')
        self.setGeometry(300, 300, 300, 200)
        self.show()

    @pyqtSlot()
    def show_qr_message(self):
        # '배정' 버튼을 숨기고, QR 코드 안내 문구와 '다음' 버튼을 보이게 함
        self.assign_button.hide()
        self.qr_label.show()
        self.next_button.show()
        self.result_label.hide()
        self.start_qr_scanner()

    @pyqtSlot()
    def show_assign_button(self):
        # QR 코드 안내 문구와 '다음' 버튼을 숨기고, '배정' 버튼을 보이게 함
        self.qr_label.hide()
        self.next_button.hide()
        self.result_label.hide()
        self.assign_button.show()
        self.stop_qr_scanner()

    def start_qr_scanner(self):
        self.scanning = True
        self.thread = threading.Thread(target=self.qr_scanner)
        self.thread.start()

    def stop_qr_scanner(self):
        self.scanning = False

    def qr_scanner(self):
        cap = cv2.VideoCapture(0)
        while self.scanning:
            ret, frame = cap.read()
            if ret:
                decoded_objects = pyzbar.decode(frame)
                for obj in decoded_objects:
                    qr_data = obj.data.decode("utf-8")
                    QMetaObject.invokeMethod(self, "update_result_label", Qt.QueuedConnection, Q_ARG(str, qr_data))
                    self.stop_qr_scanner()
                    break

                # Display the frame (for debugging purposes)
                cv2.imshow("QR Code Scanner", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        cap.release()
        cv2.destroyAllWindows()

    @pyqtSlot(str)
    def update_result_label(self, qr_data):
        self.result_label.setText(f"QR 코드 인식: {qr_data}")
        self.result_label.show()

    def closeEvent(self, event):
        if hasattr(self, 'scanning') and self.scanning:
            self.stop_qr_scanner()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
