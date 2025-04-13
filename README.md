# Enhanced Vietnamese Money gTTS API

## Tổng quan

API Đọc Số Tiền Tiếng Việt là một dịch vụ REST cung cấp khả năng chuyển đổi số tiền thành văn bản và âm thanh tiếng Việt với ngữ điệu tự nhiên.
API này được tối ưu hóa cho việc đọc số tiền trong các ứng dụng ngân hàng, tài chính và thương mại điện tử.

## Tính năng

- Chuyển đổi số tiền thành chữ tiếng Việt
- Đọc số tiền bằng giọng Google TTS với ngữ điệu tự nhiên
- Tạo các thông báo giao dịch tài chính tự động
- Hỗ trợ số tiền lớn (hàng nghìn tỷ đồng)
- Xử lý ngữ điệu và ngắt nghỉ tự nhiên khi đọc số tiền

## Cài đặt

### Yêu cầu

- Python 3.6+
- Flask
- gTTS (Google Text-to-Speech)
- pydub
- ffmpeg

### Các bước cài đặt

1. Tạo và kích hoạt môi trường ảo:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Cài đặt các gói phụ thuộc:
   ```bash
   pip install flask gtts pydub
   ```

3. Cài đặt ffmpeg (bắt buộc cho pydub):
   - **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Windows**:
     1. Tải ffmpeg từ https://github.com/BtbN/FFmpeg-Builds/releases (chọn file ffmpeg-master-latest-win64-gpl.zip cho Windows 64-bit)
     2. Giải nén và đặt vào thư mục `C:\ffmpeg`
     3. Thêm `C:\ffmpeg\bin` vào biến môi trường PATH:
        - Mở Start menu, tìm "Edit environment variables"
        - Chọn "Environment Variables"
        - Trong phần "System variables", tìm và chọn biến "Path", nhấn "Edit"
        - Nhấn "New" và thêm đường dẫn `C:\ffmpeg\bin`
        - Nhấn "OK" để lưu thay đổi
     4. Khởi động lại Command Prompt hoặc PowerShell
     5. Kiểm tra cài đặt bằng cách gõ lệnh: `ffmpeg -version`

4. Khởi động server:
   ```bash
   python app.py
   ```

## API Endpoints

### 1. Chuyển số tiền thành chữ

**Endpoint:** `GET /api/text-money`

**Parameters:**
- `amount`: Số tiền cần chuyển đổi (bắt buộc)

**Response:**
```json
{
  "amount": 1500000,
  "text": "một triệu năm trăm nghìn đồng"
}
```

**Example:**
```
GET /api/text-money?amount=1500000
```

### 2. Đọc số tiền

**Endpoint:** `GET /api/read-money`

**Parameters:**
- `amount`: Số tiền cần đọc (bắt buộc)
- `enhanced`: Sử dụng ngữ điệu cải tiến (mặc định: true)
- `type`: Loại thông báo (nhận: "receive", chuyển: "send", số dư: "balance", mặc định: chỉ đọc số tiền)

**Response:**
- File MP3 chứa giọng đọc số tiền

**Examples:**
```
GET /api/read-money?amount=1500000
GET /api/read-money?amount=1500000&enhanced=false
GET /api/read-money?amount=1500000&type=receive
```

### 3. Đọc văn bản tùy chỉnh

**Endpoint:** `POST /api/tts`

**Request Body:**
```json
{
  "text": "Văn bản cần đọc",
  "enhanced": true
}
```

**Response:**
- File MP3 chứa giọng đọc văn bản

## Khắc phục lỗi ffmpeg trên Windows

Nếu bạn gặp lỗi sau khi cài đặt:
```
RuntimeWarning: Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work
```

Hãy thực hiện các bước sau:

1. Kiểm tra lại việc cài đặt ffmpeg và đảm bảo đường dẫn `C:\ffmpeg\bin` đã được thêm đúng vào PATH
2. Nếu vẫn gặp lỗi, bạn có thể chỉ định đường dẫn ffmpeg trực tiếp trong code:
   ```python
   from pydub import AudioSegment
   
   # Chỉ định đường dẫn đến ffmpeg
   AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
   AudioSegment.ffmpeg = r"C:\ffmpeg\bin\ffmpeg.exe"
   AudioSegment.ffprobe = r"C:\ffmpeg\bin\ffprobe.exe"
   ```

## Ví dụ sử dụng

### Tích hợp vào ứng dụng web

```javascript
// Đọc thông báo nhận tiền
function playMoneyNotification(amount) {
  const audio = new Audio(`/api/read-money?amount=${amount}&type=receive`);
  audio.play();
}

// Sử dụng API text
async function getMoneyText(amount) {
  const response = await fetch(`/api/text-money?amount=${amount}`);
  const data = await response.json();
  return data.text;
}
```

### Tích hợp vào ứng dụng mobile

Gọi API để tạo thông báo âm thanh cho biến động số dư:
```
GET /api/read-money?amount=1500000&type=balance
```

## Xử lý số tiền lớn

API có khả năng đọc chính xác số tiền lớn. Ví dụ:
- `1589039021120` sẽ được đọc là "một nghìn năm trăm tám mươi chín tỷ ba mươi chín triệu hai mươi mốt nghìn một trăm hai mươi đồng"

## Cải tiến ngữ điệu

API sử dụng các kỹ thuật xử lý âm thanh để cải thiện ngữ điệu khi đọc số tiền:
1. Thêm ngắt nghỉ tự nhiên sau các đơn vị (tỷ, triệu, nghìn)
2. Điều chỉnh âm lượng để nhấn mạnh các phần quan trọng
3. Thêm hiệu ứng fade-out cho phần cuối câu

## Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng tạo issue hoặc pull request để cải thiện dự án.

## Giấy phép

[MIT License](LICENSE)
