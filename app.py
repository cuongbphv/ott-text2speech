from flask import Flask, request, send_file, jsonify
from gtts import gTTS
from gtts.tokenizer import pre_processors
from pydub import AudioSegment
import os
import uuid
import re

app = Flask(__name__)

AUDIO_DIR = "tmp"
os.makedirs(AUDIO_DIR, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại


def number_to_vietnamese_words(number):
    """Chuyển đổi số thành chữ tiếng Việt"""

    # Xử lý số 0
    if number == 0:
        return "không"

    # Xử lý số âm
    negative = False
    if number < 0:
        negative = True
        number = abs(number)

    # Danh sách các từ đọc số
    don_vi = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

    # Xử lý hàng chục
    def doc_hang_chuc(num):
        chuc = num // 10
        dv = num % 10

        if chuc == 0:
            return don_vi[dv]
        elif chuc == 1:
            if dv == 0:
                return "mười"
            elif dv == 5:
                return "mười lăm"
            else:
                return f"mười {don_vi[dv]}"
        else:
            if dv == 0:
                return f"{don_vi[chuc]} mươi"
            elif dv == 1:
                return f"{don_vi[chuc]} mươi mốt"
            elif dv == 5:
                return f"{don_vi[chuc]} mươi lăm"
            else:
                return f"{don_vi[chuc]} mươi {don_vi[dv]}"

    # Xử lý hàng trăm
    def doc_hang_tram(num):
        tram = num // 100
        du = num % 100

        if du == 0:
            return f"{don_vi[tram]} trăm"
        elif du < 10:
            return f"{don_vi[tram]} trăm lẻ {don_vi[du]}"
        else:
            return f"{don_vi[tram]} trăm {doc_hang_chuc(du)}"

    # Đọc nhóm 3 số
    def doc_nhom(num):
        if num == 0:
            return ""
        elif num < 10:
            return don_vi[num]
        elif num < 100:
            return doc_hang_chuc(num)
        else:
            return doc_hang_tram(num)

    # Cách xử lý theo quy tắc đọc số tiếng Việt
    ty = number // 1000000000
    trieu = (number % 1000000000) // 1000000
    nghin = (number % 1000000) // 1000
    dv = number % 1000

    result = ""

    # Đọc hàng tỷ
    if ty > 0:
        # Nếu có hàng nghìn tỷ
        if ty >= 1000:
            nghin_ty = ty // 1000
            ty_le = ty % 1000

            result += f"{doc_nhom(nghin_ty)} nghìn"

            if ty_le > 0:
                result += f" {doc_nhom(ty_le)}"
        else:
            result += doc_nhom(ty)

        result += " tỷ"

    # Đọc hàng triệu
    if trieu > 0:
        if result:
            result += " "
        result += f"{doc_nhom(trieu)} triệu"

    # Đọc hàng nghìn
    if nghin > 0:
        if result:
            result += " "
        result += f"{doc_nhom(nghin)} nghìn"

    # Đọc hàng đơn vị
    if dv > 0:
        if result:
            result += " "
        result += doc_nhom(dv)

    # Thêm "âm" cho số âm
    if negative:
        result = f"âm {result}"

    return result.strip()


def format_money_vietnamese(amount):
    """Định dạng số tiền tiếng Việt"""

    # Đảm bảo amount là số nguyên
    try:
        amount = int(amount)
    except (ValueError, TypeError):
        raise ValueError("Số tiền không hợp lệ")

    # Chuyển số thành chữ
    words = number_to_vietnamese_words(amount)

    # Thêm đơn vị tiền tệ
    return f"{words} Việt Nam đồng"


def enhance_vietnamese_text(text):
    """Cải thiện văn bản tiếng Việt để đọc tự nhiên hơn"""
    # Thêm dấu phẩy để tạo ngắt nghỉ tự nhiên
    # text = text.replace(" tỷ ", " tỷ, ")
    # text = text.replace(" triệu ", " triệu, ")
    # text = text.replace(" nghìn ", " nghìn, ")

    return text


def enhanced_tts(text, output_file):
    """Tạo giọng đọc cải tiến bằng cách xử lý ngữ điệu"""
    # Tiền xử lý văn bản
    enhanced_text = enhance_vietnamese_text(text)

    # Chia nhỏ văn bản theo dấu phẩy
    segments = enhanced_text.split(',')

    # Khởi tạo đoạn âm thanh trống
    combined = AudioSegment.empty()

    for i, segment in enumerate(segments):
        if not segment.strip():
            continue

        # Tạo file tạm
        temp_file = os.path.join(AUDIO_DIR, f"temp_{uuid.uuid4()}.mp3")

        # Tạo âm thanh bằng Google TTS
        tts = gTTS(segment.strip(), lang='vi')
        tts.save(temp_file)

        # Đọc đoạn âm thanh
        audio_segment = AudioSegment.from_mp3(temp_file)

        # Điều chỉnh âm thanh tùy theo loại segment
        if "đồng" in segment:
            # Kéo dài và giảm nhẹ âm lượng ở từ cuối
            audio_segment = audio_segment - 1  # Giảm 1dB
            if len(audio_segment) > 300:
                audio_segment = audio_segment.fade_out(150)
        elif any(word in segment for word in ["tỷ", "triệu", "nghìn"]):
            # Tăng âm lượng cho các đơn vị quan trọng
            audio_segment = audio_segment + 2  # Tăng 2dB

        # Thêm khoảng dừng nhỏ giữa các đoạn
        if i > 0:
            combined += AudioSegment.silent(duration=150)

        # Kết hợp vào âm thanh chính
        combined += audio_segment

        # Xóa file tạm
        os.remove(temp_file)

    # Lưu file kết quả
    combined.export(output_file, format="mp3")

    return output_file


@app.route('/api/read-money', methods=['GET'])
def read_money():
    try:
        # Lấy số tiền từ tham số
        amount_str = request.args.get('amount', default="0")

        # Lấy tùy chọn cải tiến giọng nói
        enhanced = request.args.get('enhanced', default="true").lower() == "true"

        # Định dạng số tiền thành chữ
        money_text = "Bạn đã nhận số tiền giao dịch " + format_money_vietnamese(amount_str)

        # Tạo đường dẫn file âm thanh
        filename = os.path.join(AUDIO_DIR, f"money_{uuid.uuid4()}.mp3")

        if enhanced and os.path.exists(AUDIO_DIR):
            # Sử dụng giọng đọc cải tiến
            enhanced_tts(money_text, filename)
        else:
            # Sử dụng Google TTS thông thường
            tts = gTTS(money_text, lang='vi')
            tts.save(filename)

        # Gửi file âm thanh
        response = send_file(filename, mimetype='audio/mp3', as_attachment=True,
                             download_name=os.path.basename(filename))

        # Xóa file sau khi gửi
        @response.call_on_close
        def cleanup():
            if os.path.exists(filename):
                os.unlink(filename)

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/text-money', methods=['GET'])
def text_money():
    try:
        # Lấy số tiền từ tham số
        amount_str = request.args.get('amount', default="0")

        # Định dạng số tiền thành chữ
        money_text = format_money_vietnamese(amount_str)

        # Trả về kết quả dạng JSON
        return jsonify({
            "amount": int(amount_str),
            "text": money_text
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tts', methods=['POST'])
def tts():
    data = request.get_json()
    text = data.get('text', '')
    enhanced = data.get('enhanced', True)

    if not text:
        return {'error': 'Missing text'}, 400

    # Tạo đường dẫn file âm thanh
    filename = os.path.join(os.getcwd(), AUDIO_DIR, f"tts_{uuid.uuid4()}.mp3")

    if enhanced and os.path.exists(AUDIO_DIR):
        # Xử lý văn bản để cải thiện ngữ điệu
        processed_text = text
        if "đồng" in text:
            processed_text = enhance_vietnamese_text(text)

        # Sử dụng giọng đọc cải tiến
        enhanced_tts(processed_text, filename)
    else:
        # Sử dụng Google TTS thông thường
        tts = gTTS(text, lang='vi')
        tts.save(filename)

    # Gửi file âm thanh
    response = send_file(filename, mimetype='audio/mp3', as_attachment=True, download_name=os.path.basename(filename))

    # Xóa file sau khi gửi
    @response.call_on_close
    def cleanup():
        if os.path.exists(filename):
            os.unlink(filename)

    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)