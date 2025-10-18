# 🎙️ راهنمای رونویسی Real-time

راهنمای کامل برای استفاده از رونویسی زنده و real-time

---

## 📁 فایل‌های موجود

### 1️⃣ [gradio-realtime.py](gradio-realtime.py) - Progressive Streaming

**نحوه کار:**
- صدا را دریافت می‌کند
- به chunks کوچک (2-5 ثانیه) تقسیم می‌کند
- هر chunk را جداگانه transcribe می‌کند
- نتایج را به صورت تدریجی نمایش می‌دهد

**استفاده:**
```bash
pip install gradio requests soundfile numpy
python gradio-realtime.py
```

**مناسب برای:**
- تست progressive transcription
- یادگیری روش chunking
- استفاده بدون نیاز به WebSocket

---

### 2️⃣ [gradio-true-realtime.html](gradio-true-realtime.html) - Live Streaming ⭐

**نحوه کار:**
- از Web Audio API استفاده می‌کند
- صدا را به صورت زنده ضبط می‌کند
- هر N ثانیه یک chunk می‌فرستد
- متن را real-time به‌روزرسانی می‌کند
- شامل visualizer صدا

**استفاده:**
```bash
# فقط کافیست فایل HTML را در مرورگر باز کنید
# یا با یک web server ساده:
python -m http.server 8080
# سپس: http://localhost:8080/gradio-true-realtime.html
```

**مناسب برای:**
- استفاده واقعی real-time
- دمو برای مشتریان
- تجربه کاربری عالی

---

### 3️⃣ [websocket-endpoint.py](websocket-endpoint.py) - Backend WebSocket

کد WebSocket endpoint برای افزودن به `faster-whisper-service.py`

**نیاز به اضافه شدن به سرویس اصلی**

---

## 🚀 راه‌اندازی سریع

### روش 1: HTML Interface (ساده‌ترین) ⭐

```bash
# 1. فقط کافیست سرویس Whisper را run کنید
docker-compose up -d whisper-gpu

# 2. فایل HTML را باز کنید
# با double-click روی gradio-true-realtime.html
# یا:
python -m http.server 8080
# باز کردن: http://localhost:8080/gradio-true-realtime.html

# 3. شروع صحبت!
```

### روش 2: Gradio Progressive

```bash
# 1. نصب dependencies
pip install gradio requests soundfile numpy

# 2. اجرا
python gradio-realtime.py

# 3. باز کردن مرورگر
# http://localhost:7860
```

---

## 💻 استفاده

### HTML Interface (gradio-true-realtime.html)

#### گام 1: تنظیمات

- **زبان**: فارسی، انگلیسی، عربی، ترکی
- **Beam Size**: 1-10 (پیش‌فرض: 5)
  - کمتر = سریع‌تر
  - بیشتر = دقیق‌تر
- **Chunk Duration**: 1-5 ثانیه (پیش‌فرض: 3)
  - کمتر = به‌روزرسانی سریعتر
  - بیشتر = دقت بهتر

#### گام 2: شروع ضبط

1. کلیک روی "▶️ شروع ضبط"
2. اجازه دسترسی به میکروفن
3. شروع به صحبت کنید

#### گام 3: مشاهده نتایج

- متن به صورت خودکار هر N ثانیه اضافه می‌شود
- Visualizer صدا را real-time نشان می‌دهد
- می‌توانید همچنان ادامه دهید

#### گام 4: توقف

کلیک روی "⏹️ توقف ضبط"

---

### Gradio Progressive Interface

#### چگونه کار می‌کند:

```
1. ضبط صدا (کل صدا)
   ↓
2. تقسیم به chunks
   ↓
3. برای هر chunk:
   - Transcribe
   - اضافه به متن کامل
   - نمایش در UI
   ↓
4. نمایش نهایی
```

#### مثال:

```python
# صدای 10 ثانیه‌ای
# Chunk duration = 2s

Chunk 1 (0-2s)   → "سلام"
Chunk 2 (1.5-3.5s) → "خوش آمدید"  # 50% overlap
Chunk 3 (3-5s)   → "به سرویس"
Chunk 4 (4.5-6.5s) → "رونویسی"
Chunk 5 (6-8s)   → "خودکار"
Chunk 6 (7.5-9.5s) → "ویسپر"

نتیجه نهایی: "سلام خوش آمدید به سرویس رونویسی خودکار ویسپر"
```

---

## 🎨 اسکرین‌شات (متنی)

### HTML Interface:

```
╔══════════════════════════════════════════════════╗
║     🎙️ رونویسی زنده واقعی                      ║
║  صحبت کنید و متن را به صورت real-time مشاهده  ║
║                     کنید                         ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  🌐 زبان: [فارسی ▼]                            ║
║  🎯 Beam: [━━━●━━━━━━] 5                        ║
║  ⏱️ Chunk: [━━━━●━━━━] 3s                       ║
║                                                  ║
║     ●  [وضعیت ضبط نشانگر]                      ║
║                                                  ║
║  [▂▃▅▇▆▄▂▃▅▇]  Audio Visualizer                 ║
║                                                  ║
║  [▶️ شروع]  [⏹️ توقف]  [🗑️ پاک کردن]         ║
║                                                  ║
║  🔴 در حال ضبط...                               ║
║                                                  ║
║  ┌────────────────────────────────────────────┐ ║
║  │ سلام خوش آمدید به سرویس رونویسی خودکار  │ ║
║  │ ویسپر. این یک نمونه متن است که...        │ ║
║  │                                            │ ║
║  └────────────────────────────────────────────┘ ║
║                                                  ║
║  💡 نکات استفاده:                               ║
║  • Chunk Duration کوچکتر = سریعتر              ║
║  • Beam Size بالاتر = دقیق‌تر                   ║
╚══════════════════════════════════════════════════╝
```

---

## ⚙️ تنظیمات بهینه

### برای سرعت بالا:

```
Beam Size: 3
Chunk Duration: 2s
VAD Filter: true
```

**نتیجه:** به‌روزرسانی هر 2 ثانیه، latency کم

### برای دقت بالا:

```
Beam Size: 10
Chunk Duration: 4s
VAD Filter: true
```

**نتیجه:** دقت بالاتر، به‌روزرسانی هر 4 ثانیه

### برای تعادل:

```
Beam Size: 5
Chunk Duration: 3s
VAD Filter: true
```

**نتیجه:** متعادل بین سرعت و دقت ✅

---

## 📊 مقایسه روش‌ها

| ویژگی | gradio-simple.py | gradio-realtime.py | HTML Real-time |
|-------|------------------|--------------------|--------------------|
| **Latency** | بالا (کل فایل) | متوسط (chunks) | کم (live) ✅ |
| **User Experience** | ساده | خوب | عالی ✅ |
| **Visualizer** | ❌ | ❌ | ✅ |
| **Progressive Update** | ❌ | ✅ | ✅ |
| **Setup** | آسان | آسان | خیلی آسان ✅ |
| **Dependencies** | Gradio + requests | Gradio + numpy | فقط مرورگر ✅ |

---

## 🐛 عیب‌یابی

### مشکل 1: "میکروفن کار نمی‌کند"

**علت:** مرورگر اجازه دسترسی ندارد

**راه‌حل:**
1. در Chrome: `chrome://settings/content/microphone`
2. اجازه دسترسی به `localhost` بدهید
3. یا از HTTPS استفاده کنید

### مشکل 2: "متن duplicate می‌شود"

**علت:** Overlap بین chunks

**راه‌حل:**
- در `gradio-realtime.py`: کاهش `OVERLAP` به 0.2
- یا افزایش `CHUNK_DURATION`

### مشکل 3: "به‌روزرسانی خیلی کند است"

**راه‌حل:**
- کاهش `Chunk Duration` به 1-2 ثانیه
- کاهش `Beam Size` به 3
- استفاده از HTML interface

### مشکل 4: "CORS Error"

**علت:** API و HTML در domainهای مختلف

**راه‌حل:**

در `faster-whisper-service.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🔧 سفارشی‌سازی

### تغییر Chunk Duration پیش‌فرض

**HTML:**
```html
<input type="range" id="chunkDuration" min="1" max="5" value="3" step="0.5">
```
تغییر `value="3"` به مقدار دلخواه

**Python:**
```python
CHUNK_DURATION = 2  # ثانیه
```

### تغییر Overlap

**Python:**
```python
OVERLAP = 0.5  # 50% overlap
```

کاهش به 0.2 برای overlap کمتر

### اضافه کردن زبان جدید

**HTML:**
```html
<select id="language">
    <option value="fa">فارسی</option>
    <option value="en">English</option>
    <option value="ar">العربية</option>
    <option value="ur">اردو</option>  <!-- جدید -->
</select>
```

---

## 🌐 استفاده در شبکه

### دسترسی از موبایل به PC:

1. **روی PC:**
```bash
python -m http.server 8080
```

2. **IP سیستم را پیدا کنید:**
```bash
ipconfig  # Windows
ifconfig  # Linux/Mac
```

3. **از موبایل:**
```
http://192.168.1.100:8080/gradio-true-realtime.html
```

**نکته:** مطمئن شوید firewall اجازه دسترسی می‌دهد.

---

## 🎯 Use Cases

### Use Case 1: جلسات آنلاین

- زبان: فارسی
- Beam: 5-7
- Chunk: 3-4s
- **هدف:** دقت بالا برای جلسات مهم

### Use Case 2: یادداشت‌برداری سریع

- زبان: فارسی
- Beam: 3
- Chunk: 2s
- **هدف:** سرعت بالا برای یادداشت‌های شخصی

### Use Case 3: پادکست/مصاحبه

- زبان: بسته به محتوا
- Beam: 10
- Chunk: 5s
- **هدف:** بالاترین دقت

---

## 📈 بهینه‌سازی عملکرد

### Client-side:

```javascript
// کاهش تعداد requests
const CHUNK_DURATION = 4; // به جای 2

// استفاده از queue
let transcriptionQueue = [];
```

### Server-side:

```yaml
# docker-compose.yml
environment:
  - BATCH_SIZE=4  # کاهش برای latency کمتر
  - COMPUTE_TYPE=int8_float16  # سریعتر
```

---

## 🔮 آینده

### ویژگی‌های در راه:

1. **WebSocket واقعی**
   - Streaming دوطرفه
   - Latency زیر 1 ثانیه

2. **Speaker Diarization**
   - تشخیص چند speaker
   - جداسازی متن‌ها

3. **Punctuation Restoration**
   - اضافه کردن خودکار نقطه‌گذاری
   - بهبود خوانایی

4. **Multi-language Detection**
   - تشخیص خودکار زبان
   - Switch بین زبان‌ها

---

## 📚 منابع بیشتر

- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [MediaRecorder API](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
- [Gradio Streaming](https://gradio.app/guides/streaming-outputs/)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)

---

**آخرین آپدیت:** 2025-10-18
**نسخه:** 1.0

موفق باشید! 🚀
