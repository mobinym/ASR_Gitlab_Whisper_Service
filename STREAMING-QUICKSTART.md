# 🚀 Streaming API - Quick Start

راهنمای سریع برای شروع کار با Streaming Transcription

---

## ⚡ سریع‌ترین راه (30 ثانیه)

### 1️⃣ با Curl

```bash
curl -X POST "http://localhost:16000/transcribe/stream/" \
  -F "file=@your_audio.wav" \
  -F "language=fa" \
  -N
```

### 2️⃣ با Python Script (پیشنهادی)

```bash
# اجرای تست کامل
python test-streaming.py your_audio.wav -l fa

# فقط تست پایه
python test-streaming.py your_audio.wav -l fa --test basic

# ذخیره خروجی
python test-streaming.py your_audio.wav -l fa -o output.ndjson
```

### 3️⃣ با Bash Script

```bash
# تست ساده
bash test-streaming.sh your_audio.wav fa 16000

# یا اگر از Docker استفاده می‌کنید
bash test-streaming.sh your_audio.wav fa 16000
```

---

## 📋 دستورات پرکاربرد

### نمایش زیبا با jq

```bash
curl -X POST "http://localhost:16000/transcribe/stream/" \
  -F "file=@audio.wav" \
  -F "language=fa" \
  -N | jq -r '"[\(.start)s-\(.end)s] \(.text)"'
```

### ذخیره در فایل

```bash
# NDJSON format
curl -X POST "http://localhost:16000/transcribe/stream/" \
  -F "file=@audio.wav" \
  -F "language=fa" \
  -N -o output.ndjson

# تبدیل به JSON
jq -s '.' output.ndjson > output.json
```

### با تنظیمات پیشرفته

```bash
curl -X POST "http://localhost:16000/transcribe/stream/" \
  -F "file=@audio.wav" \
  -F "language=fa" \
  -F "beam_size=10" \
  -F "vad_filter=true" \
  -N
```

---

## 🐍 Python Quick Examples

### مثال 1: ساده‌ترین

```python
import requests
import json

url = "http://localhost:16000/transcribe/stream/"

with open("audio.wav", "rb") as f:
    response = requests.post(
        url,
        files={'file': f},
        data={'language': 'fa'},
        stream=True
    )

    for line in response.iter_lines():
        if line:
            segment = json.loads(line)
            print(f"[{segment['start']:.1f}s] {segment['text']}")
```

### مثال 2: با ذخیره نتایج

```python
import requests
import json

segments = []

with open("audio.wav", "rb") as f:
    response = requests.post(
        "http://localhost:16000/transcribe/stream/",
        files={'file': f},
        data={'language': 'fa', 'beam_size': 10},
        stream=True
    )

    for line in response.iter_lines():
        if line:
            segment = json.loads(line)
            segments.append(segment)
            print(f"Segment {len(segments)}: {segment['text']}")

# کل متن
full_text = ' '.join(s['text'] for s in segments)
print(f"\nFull: {full_text}")
```

---

## 🎯 پارامترها

| پارامتر | مقدار پیش‌فرض | توضیح |
|---------|---------------|--------|
| `file` | **(required)** | فایل صوتی |
| `language` | `"fa"` | کد زبان: `fa`, `en`, `ar` |
| `beam_size` | `5` | دقت (1-15، بالاتر = دقیق‌تر) |
| `vad_filter` | `true` | فیلتر سکوت |

---

## 💡 Use Cases

### Use Case 1: Real-time UI

برای نمایش تدریجی در رابط کاربری

```bash
# ارسال و نمایش segment به segment
curl -X POST "http://localhost:16000/transcribe/stream/" \
  -F "file=@audio.wav" \
  -F "language=fa" \
  -N | while read line; do
    echo "$line" | jq -r '.text'
  done
```

### Use Case 2: Subtitle Generator

```python
def to_srt(segments):
    for i, seg in enumerate(segments, 1):
        start = f"{int(seg['start']//60):02}:{seg['start']%60:06.3f}".replace('.', ',')
        end = f"{int(seg['end']//60):02}:{seg['end']%60:06.3f}".replace('.', ',')
        print(f"{i}\n00:{start} --> 00:{end}\n{seg['text']}\n")

# Usage
segments = []
with open("audio.wav", "rb") as f:
    response = requests.post(url, files={'file': f}, data={'language': 'fa'}, stream=True)
    for line in response.iter_lines():
        if line:
            segments.append(json.loads(line))

to_srt(segments)
```

### Use Case 3: Batch Processing

```bash
# پردازش همه فایل‌های wav در یک دایرکتوری
for file in *.wav; do
    echo "Processing: $file"
    curl -X POST "http://localhost:16000/transcribe/stream/" \
      -F "file=@$file" \
      -F "language=fa" \
      -N -o "${file%.wav}.ndjson"
done
```

---

## 🔍 مقایسه: Stream vs Non-Stream

| ویژگی | Stream | Non-Stream |
|-------|--------|-----------|
| **Endpoint** | `/transcribe/stream/` | `/transcribe/` |
| **Format** | NDJSON (line by line) | JSON (single object) |
| **Latency** | ⚡ کم (segments به محض آماده) | ⏱️ بالاتر (منتظر کل فایل) |
| **Use case** | Real-time UI, live updates | Final result, batch jobs |

### تست مقایسه:

```bash
# Stream
time curl -X POST "http://localhost:16000/transcribe/stream/" \
  -F "file=@audio.wav" -F "language=fa" -N > stream.txt

# Non-Stream
time curl -X POST "http://localhost:16000/transcribe/" \
  -F "file=@audio.wav" -F "language=fa" > regular.json
```

---

## ⚠️ نکات مهم

### ✅ DO:
- از `-N` در curl استفاده کنید (غیرفعال کردن buffering)
- از `stream=True` در Python requests استفاده کنید
- برای فایل‌های طولانی timeout مناسب تنظیم کنید

### ❌ DON'T:
- کل response را در حافظه نگه ندارید
- بدون error handling استفاده نکنید
- برای batch processing ساده از streaming استفاده نکنید

---

## 🐛 عیب‌یابی سریع

### خطا: "Connection timeout"

```bash
# افزایش timeout
curl --max-time 600 -X POST "http://localhost:16000/transcribe/stream/" \
  -F "file=@audio.wav" -F "language=fa" -N
```

### خطا: "Invalid JSON"

```bash
# بررسی خروجی خام
curl -X POST "http://localhost:16000/transcribe/stream/" \
  -F "file=@audio.wav" -F "language=fa" -N | cat -A
```

### خطا: "Empty response"

```bash
# بررسی فایل صوتی
ffprobe audio.wav

# تبدیل به فرمت استاندارد
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

---

## 📚 مطالعه بیشتر

- [راهنمای کامل Streaming API](STREAMING-API-GUIDE.md)
- [مستندات اصلی سرویس](README-FASTER-WHISPER.md)
- [راهنمای بهبود دقت](ACCURACY-GUIDE.md)

---

**نکته:** برای جزئیات بیشتر و examples پیشرفته‌تر، به [STREAMING-API-GUIDE.md](STREAMING-API-GUIDE.md) مراجعه کنید.
