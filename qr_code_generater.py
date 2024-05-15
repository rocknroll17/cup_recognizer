import qrcode
import os

def generate_qr_code(cur, conn, qr_text):
    file_name = qr_text+".png"
    # QR 코드 생성
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)

    # QR 코드 이미지 생성
    img = qr.make_image(fill_color="black", back_color="white")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    directory_path = os.path.join(current_dir, "qr_code")
    file_path = os.path.join(directory_path, file_name)
    # 이미지 파일로 저장
    img.save(file_path)

    print(f"QR code 이미지가 {file_path} 파일로 생성되었습니다.")