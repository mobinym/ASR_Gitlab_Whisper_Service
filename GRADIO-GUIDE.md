# 🎙️ راهنمای استفاده از Gradio Interface

رابط کاربری وب برای رونویسی صوت با میکروفن

---

## 🚀 راه‌اندازی سریع (30 ثانیه)

### نسخه ساده

```bash
# 1. نصب dependencies
pip install gradio requests soundfile

# 2. اجرا
python gradio-simple.py

# 3. باز کردن در مرورگر
# http://localhost:7860
```

### نسخه کامل (با تنظیمات پیشرفته)

```bash
# 1. نصب dependencies
pip install -r requirements-gradio.txt

# 2. اجرا
python gradio-live-transcription.py

# 3. باز کردن در مرورگر
# http://localhost:7860
```

---

## 📁 فایل‌های موجود

### 1️⃣ `gradio-simple.py` (ساده)

**ویژگی‌ها:**
- ✅ رابط minimal و ساده
- ✅ فقط ضبط از میکروفن و رونویسی
- ✅ انتخاب زبان
- ✅ کمتر از 60 خط کد

**مناسب برای:**
- تست سریع
- یادگیری
- استفاده شخصی

**اسکرین‌شات متنی:**
```
┌─────────────────────────────────────┐
│ 🎙️ رونویسی صوت با Whisper         │
├─────────────────────────────────────┤
│ 🎤 میکروفن                         │
│  [Start Recording] [Stop]           │
│                                     │
│ زبان: [فارسی ▼]                    │
│                                     │
│ [Submit]                            │
│                                     │
│ 📄 متن رونویسی شده:                │
│ ┌─────────────────────────────┐    │
│ │ متن شما اینجا نمایش داده   │    │
│ │ می‌شود...                   │    │
│ └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### 2️⃣ `gradio-live-transcription.py` (پیشرفته)

**ویژگی‌ها:**
- ✅ رابط کامل با تنظیمات پیشرفته
- ✅ بررسی وضعیت API
- ✅ انتخاب بین Streaming/Regular API
- ✅ تنظیم Beam Size و VAD Filter
- ✅ نمایش metrics عملکرد
- ✅ ذخیره متن در فایل
- ✅ راهنما و توضیحات داخل رابط

**مناسب برای:**
- استفاده حرفه‌ای
- دمو برای مشتریان
- محیط تولید

---

## 💻 استفاده

### روش 1: اجرا روی ماشین محلی

اگر سرویس Whisper روی همین سیستم است:

```bash
# API URL پیش‌فرض
# http://localhost:16000

python gradio-simple.py
```

### روش 2: اتصال به سرور remote

اگر سرویس Whisper روی سرور دیگری است:

```python
# ویرایش فایل gradio-simple.py
API_URL = "http://YOUR_SERVER_IP:16000/transcribe/"

# یا gradio-live-transcription.py
API_BASE_URL = "http://YOUR_SERVER_IP:16000"
```

سپس:
```bash
python gradio-simple.py
```

### روش 3: اجرا روی سرور (دسترسی از راه دور)

```bash
# اجرا روی سرور
python gradio-live-transcription.py

# دسترسی از مرورگر
# http://SERVER_IP:7860
```

**نکته امنیتی:** برای محیط تولید، از reverse proxy (nginx) یا authentication استفاده کنید.

---

## 🎯 نحوه استفاده

### مرحله 1: شروع ضبط

1. روی دکمه میکروفن کلیک کنید
2. اجازه دسترسی به میکروفن را بدهید
3. شروع به صحبت کنید

### مرحله 2: توقف ضبط

1. دوباره روی دکمه میکروفن کلیک کنید
2. صبر کنید تا فایل صوتی آماده شود

### مرحله 3: رونویسی

1. روی دکمه "Submit" یا "🚀 رونویسی" کلیک کنید
2. منتظر بمانید (معمولاً 1-3 ثانیه)
3. متن در textarea نمایش داده می‌شود

### مرحله 4: کپی/ذخیره

- **کپی:** روی دکمه Copy کلیک کنید
- **ذخیره:** (نسخه کامل) روی "💾 ذخیره متن" کلیک کنید

---

## ⚙️ تنظیمات (نسخه کامل)

### زبان

انتخاب زبان صوتی:
- فارسی (`fa`)
- English (`en`)
- العربية (`ar`)
- Türkçe (`tr`)
- Auto Detect (شناسایی خودکار)

### Streaming API

- ✅ **فعال:** استفاده از endpoint streaming (سریعتر)
- ❌ **غیرفعال:** استفاده از endpoint معمولی (اطلاعات بیشتر)

### Beam Size

- **1-5:** سریع اما دقت کمتر
- **5:** متعادل (پیش‌فرض) ✅
- **10-15:** دقت بالا اما کندتر

### VAD Filter

- ✅ **فعال:** حذف خودکار سکوت‌ها (توصیه می‌شود)
- ❌ **غیرفعال:** پردازش کل صدا

---

## 🎨 سفارشی‌سازی

### تغییر Theme

```python
# در gradio-simple.py یا gradio-live-transcription.py
demo = gr.Interface(
    ...,
    theme=gr.themes.Soft()  # یا Glass, Monochrome, Base
)
```

### تغییر پورت

```python
demo.launch(
    server_port=8080  # به جای 7860
)
```

### فعال کردن Share Link (دسترسی عمومی موقت)

```python
demo.launch(
    share=True  # ایجاد لینک عمومی gradio.live
)
```

**خروجی:**
```
Running on public URL: https://abc123.gradio.live
```

⚠️ **هشدار:** این لینک عمومی است و همه می‌توانند به آن دسترسی داشته باشند!

---

## 🔧 عیب‌یابی

### مشکل 1: "Cannot connect to API"

**علت:** سرویس Whisper در دسترس نیست

**راه‌حل:**
```bash
# بررسی سرویس
curl http://localhost:16000/

# اگر در docker
docker ps | grep whisper

# راه‌اندازی مجدد
docker-compose up -d whisper-gpu
```

### مشکل 2: میکروفن کار نمی‌کند

**علت:** مرورگر اجازه دسترسی ندارد

**راه‌حل:**
- در Chrome/Firefox: Settings → Privacy → Microphone
- اجازه دسترسی به `localhost:7860` بدهید
- یا از HTTPS استفاده کنید

### مشکل 3: خطای "Module not found"

**راه‌حل:**
```bash
pip install -r requirements-gradio.txt
```

### مشکل 4: کیفیت صدای ضبط شده پایین است

**راه‌حل:**
- از میکروفن با کیفیت بهتر استفاده کنید
- فاصله کمتر از میکروفن صحبت کنید
- محیط کم‌نویز انتخاب کنید

---

## 🌐 استفاده در شبکه محلی

### سناریو: دسترسی از موبایل به اپلیکیشن روی PC

1. **روی PC اجرا کنید:**

```bash
python gradio-live-transcription.py
```

2. **IP سیستم را پیدا کنید:**

```bash
# Windows
ipconfig

# Linux/Mac
ifconfig
# یا
ip addr show
```

3. **از موبایل وارد شوید:**

```
http://192.168.1.100:7860
```

(جایگزین IP واقعی کنید)

---

## 🐳 اجرا با Docker

اگر می‌خواهید Gradio را هم در Docker اجرا کنید:

### Dockerfile برای Gradio

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-gradio.txt .
RUN pip install --no-cache-dir -r requirements-gradio.txt

COPY gradio-live-transcription.py .

EXPOSE 7860

CMD ["python", "gradio-live-transcription.py"]
```

### ساخت و اجرا

```bash
# Build
docker build -t whisper-gradio -f Dockerfile.gradio .

# Run
docker run -d \
  -p 7860:7860 \
  --name whisper-gradio \
  whisper-gradio

# دسترسی
# http://localhost:7860
```

### اضافه کردن به docker-compose.yml

```yaml
services:
  whisper-gradio:
    build:
      context: .
      dockerfile: Dockerfile.gradio
    image: whisper-gradio:latest
    container_name: whisper-gradio
    restart: unless-stopped
    ports:
      - "7860:7860"
    networks:
      - whisper-net
    environment:
      - API_BASE_URL=http://whisper-gpu:8000
```

---

## 📊 مقایسه نسخه‌ها

| ویژگی | gradio-simple.py | gradio-live-transcription.py |
|-------|------------------|------------------------------|
| **خطوط کد** | ~60 | ~350 |
| **API Health Check** | ❌ | ✅ |
| **Streaming Support** | ❌ | ✅ |
| **Beam Size Control** | ❌ | ✅ |
| **VAD Filter Control** | ❌ | ✅ |
| **Performance Metrics** | ❌ | ✅ |
| **Export to File** | ❌ | ✅ |
| **راهنما داخلی** | ❌ | ✅ |
| **مناسب برای** | تست سریع | استفاده حرفه‌ای |

---

## 🎓 مثال‌های پیشرفته

### مثال 1: اضافه کردن History

```python
import gradio as gr

def transcribe_with_history(audio, language, history):
    # Transcribe
    text = transcribe(audio, language)

    # Add to history
    history.append(f"[{language}] {text}")

    return text, "\n\n".join(history)

demo = gr.Interface(
    fn=transcribe_with_history,
    inputs=[
        gr.Audio(sources=["microphone"], type="numpy"),
        gr.Dropdown(choices=[("فارسی", "fa"), ("English", "en")], value="fa"),
        gr.State([])  # History state
    ],
    outputs=[
        gr.Textbox(label="نتیجه فعلی"),
        gr.Textbox(label="تاریخچه", lines=10)
    ]
)
```

### مثال 2: Real-time Streaming (واقعی)

برای streaming واقعی از WebSocket استفاده کنید:

```python
# نیاز به websocket-client
import websockets
import asyncio

async def stream_audio(audio_stream):
    async with websockets.connect('ws://localhost:8000/ws/stream') as ws:
        for chunk in audio_stream:
            await ws.send(chunk)
            result = await ws.recv()
            yield result
```

---

## 📚 منابع

- [Gradio Documentation](https://gradio.app/docs/)
- [Gradio Audio Component](https://gradio.app/docs/#audio)
- [Whisper Streaming API Guide](STREAMING-API-GUIDE.md)

---

## 💡 نکات بهینه‌سازی

### برای کاهش Latency

1. **استفاده از Streaming API** (نسخه کامل)
2. **کاهش Beam Size** به 3 یا 5
3. **اجرا روی همان سرور** که Whisper service است

### برای بهبود دقت

1. **افزایش Beam Size** به 10 یا 15
2. **فعال کردن VAD Filter**
3. **استفاده از میکروفن با کیفیت**
4. **محیط بدون نویز**

### برای استفاده همزمان

Gradio به صورت پیش‌فرض از concurrent requests پشتیبانی می‌کند:

```python
demo.launch(
    max_threads=10  # تعداد همزمانی
)
```

---

## 🔐 امنیت

برای استفاده در production:

### 1. اضافه کردن Authentication

```python
demo.launch(
    auth=("username", "password")
)
```

### 2. استفاده از HTTPS

```bash
# با nginx reverse proxy
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3. محدود کردن دسترسی

```python
demo.launch(
    server_name="127.0.0.1",  # فقط localhost
    allowed_paths=["/app/uploads"]  # محدودیت فایل
)
```

---

**آخرین آپدیت:** 2025-10-18
**نسخه:** 1.0

موفق باشید! 🚀
