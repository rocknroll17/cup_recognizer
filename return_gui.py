import sys
import cv2
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import pyqtSlot, Qt, QMetaObject, Q_ARG, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap
from pyzbar import pyzbar
import requests

class QRScannerThread(QThread):
    qr_data_found = pyqtSignal(str)
    frame_ready = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        self.scanning = False

    def run(self):
        cap = cv2.VideoCapture(0)
        while self.scanning:
            ret, frame = cap.read()
            if ret:
                decoded_objects = pyzbar.decode(frame)
                for obj in decoded_objects:
                    qr_data = obj.data.decode("utf-8")
                    self.qr_data_found.emit(qr_data)
                    self.scanning = False
                    break

                # Convert the frame to QImage for displaying in QLabel
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.frame_ready.emit(qt_image)

        cap.release()

    def start_scanning(self):
        self.scanning = True
        self.start()

    def stop_scanning(self):
        self.scanning = False
        self.wait()

class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.qr_scanner_thread = QRScannerThread()
        self.qr_scanner_thread.qr_data_found.connect(self.update_result_label)
        self.qr_scanner_thread.frame_ready.connect(self.update_video_frame)

    def initUI(self):
        # 전체 레이아웃 설정
        self.main_layout = QVBoxLayout()

        # 중앙 정렬을 위한 레이아웃
        self.central_layout = QVBoxLayout()
        self.central_layout.setAlignment(Qt.AlignCenter)

        # '배정' 버튼 생성 및 추가
        self.assign_button = QPushButton('반납하기', self)
        self.assign_button.setFixedSize(300, 100)
        self.assign_button.clicked.connect(self.show_qr_message)
        self.central_layout.addWidget(self.assign_button)

        # QR 코드 안내 문구와 '다음' 버튼 생성 (초기에는 숨김)
        self.qr_label = QLabel('QR코드를 인식하세요', self)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.hide()
        self.central_layout.addWidget(self.qr_label)

        # QR 코드 인식 결과 라벨
        self.result_label = QLabel('', self)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.hide()
        self.central_layout.addWidget(self.result_label)

        self.next_button = QPushButton('처음으로', self)
        self.next_button.setFixedSize(150, 50)
        self.next_button.clicked.connect(self.show_assign_button)
        self.next_button.hide()
        self.central_layout.addWidget(self.next_button)

        # 비디오 프레임을 표시할 라벨
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.hide()
        self.central_layout.addWidget(self.video_label)

        # 중앙 레이아웃을 메인 레이아웃에 추가
        self.main_layout.addLayout(self.central_layout)
        self.main_layout.setAlignment(Qt.AlignCenter)

        # 레이아웃을 윈도우에 설정
        self.setLayout(self.main_layout)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)  # 타이머가 한 번만 작동하도록 설정
        self.timer.timeout.connect(self.show_assign_button)  # 타이머가 만료되면 show_assign_button 메서드 호출

        # 윈도우 속성 설정
        self.setWindowTitle('반납기')
        self.setGeometry(300, 300, 300, 400)
        self.showMaximized()

    @pyqtSlot()
    def show_qr_message(self):
        # '배정' 버튼을 숨기고, QR 코드 안내 문구와 '다음' 버튼을 보이게 함
        self.assign_button.hide()
        self.qr_label.show()
        self.next_button.show()
        self.result_label.hide()
        self.video_label.show()
        self.start_qr_scanner()

    @pyqtSlot()
    def show_assign_button(self):
        # QR 코드 안내 문구와 '다음' 버튼을 숨기고, '배정' 버튼을 보이게 함
        self.timer.stop()
        self.qr_label.hide()
        self.next_button.hide()
        self.result_label.hide()
        self.video_label.hide()
        self.assign_button.show()
        self.stop_qr_scanner()
        #cv2.destroyAllWindows()

    def start_qr_scanner(self):
        self.qr_scanner_thread.start_scanning()

    def stop_qr_scanner(self):
        self.qr_scanner_thread.stop_scanning()

    @pyqtSlot(QImage)
    def update_video_frame(self, qt_image):
        # 비디오 프레임을 QLabel에 표시합니다.
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

        # 비디오 프레임에 맞게 QLabel의 크기를 조정합니다.
        self.video_label.setFixedSize(qt_image.width(), qt_image.height())

    @pyqtSlot(str)
    def update_result_label(self, qr_data):
        response = requests.post("http://10.210.56.158:5000/api/qr/"+qr_data)
        self.qr_label.hide()
        if response.status_code == 200:
            self.result_label.setText(f"컵이 반납되었습니다: {qr_data}")
        else:
            self.result_label.setText("대여되지 않은 컵입니다.")
        self.result_label.show()
        self.video_label.hide()
        self.timer.start(6000)

    def closeEvent(self, event):
        sys.exit()
        """self.timer.stop()
        self.stop_qr_scanner()
        self.qr_scanner_thread.quit()  # 스레드 종료 요청
        self.qr_scanner_thread.wait()  # 스레드가 종료될 때까지 대기
        event.accept()
        cv2.destroyAllWindows()  # OpenCV 윈도우 닫기"""




if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())