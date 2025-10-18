# 🌊 راهنمای استفاده از Streaming API

این راهنما نحوه استفاده از endpoint streaming برای دریافت نتایج transcription به صورت real-time را توضیح می‌دهد.

---

## 📋 مقدمه

Streaming API به شما این امکان را می‌دهد که نتایج transcription را segment به segment دریافت کنید، به جای اینکه منتظر پردازش کامل فایل صوتی بمانید.

### مزایا:
- ✅ **کاهش latency**: دریافت اولین نتایج سریع‌تر
- ✅ **نمایش real-time**: نمایش تدریجی متن برای کاربر
- ✅ **مناسب برای صوت‌های طولانی**: نیازی به انتظار برای کل فایل نیست
- ✅ **NDJSON format**: هر خط یک JSON object مستقل

### تفاوت با Non-Streaming:

| ویژگی | Streaming (`/transcribe/stream/`) | Non-Streaming (`/transcribe/`) |
|--------|-----------------------------------|-------------------------------|
| فرمت خروجی | NDJSON (خط‌به‌خط) | JSON (یک object) |
| Latency | کم (اولین segment زودتر) | بالاتر (منتظر کل فایل) |
| Use case | UI real-time, live updates | Batch processing, final result |
| Response size | کوچک‌تر (تدریجی) | بزرگ‌تر (یکجا) |

---

## 🚀 استفاده سریع

### Curl (ساده‌ترین)

```bash
curl -X POST "http://localhost:16000/transcribe/stream/" \
  -F "file=@audio.wav" \
  -F "language=fa" \
  -N
```

**خروجی:**
```json
{"start": 0.0, "end": 2.5, "text": "سلام خوش آمدید"}
{"start": 2.5, "end": 5.3, "text": "این یک تست است"}
{"start": 5.3, "end": 7.8, "text": "از سرویس رونویسی خودکار"}
```

### Python (پیشنهادی)

```bash
python test-streaming.py audio.wav -l fa
```

### Bash Script (کامل)

```bash
bash test-streaming.sh audio.wav fa 16000
```

---

## 📡 API Reference

### Endpoint

```
POST /transcribe/stream/
```

### پارامترها

| پارامتر | نوع | پیش‌فرض | توضیحات |
|---------|-----|---------|---------|
| `file` | File | **(required)** | فایل صوتی (wav, mp3, m4a, flac, etc.) |
| `language` | String | `"fa"` | کد زبان (fa, en, ar, ...) |
| `task` | String | `"transcribe"` | نوع تسک: `transcribe` یا `translate` |
| `beam_size` | Integer | `5` | اندازه beam search (1-15) |
| `vad_filter` | Boolean | `true` | فعال‌سازی Voice Activity Detection |

### Response Format

**Content-Type:** `application/x-ndjson`

هر خط یک JSON object با فرمت زیر:

```json
{
  "start": 0.0,      // زمان شروع segment (ثانیه)
  "end": 2.5,        // زمان پایان segment (ثانیه)
  "text": "متن رونویسی شده"
}
```

---

## 💻 مثال‌های کاربردی

### 1. Curl با نمایش زیبا

```bash
curl -X POST "http://localhost:16000/transcribe/stream/" \
  -F "file=@audio.wav" \
  -F "language=fa" \
  -F "beam_size=10" \
  -N | while read line; do
    echo "$line" | jq -r '"[\(.start)s - \(.end)s] \(.text)"'
  done
```

**خروجی:**
```
[0.0s - 2.5s] سلام خوش آمدید
[2.5s - 5.3s] این یک تست است
[5.3s - 7.8s] از سرویس رونویسی خودکار
```

### 2. Python با Real-time Display

```python
import requests
import json

def stream_transcribe(audio_file, language="fa"):
    url = "http://localhost:16000/transcribe/stream/"

    with open(audio_file, 'rb') as f:
        files = {'file': f}
        data = {'language': language}

        # Stream response
        with requests.post(url, files=files, data=data, stream=True) as response:
            for line in response.iter_lines():
                if line:
                    segment = json.loads(line)
                    print(f"[{segment['start']:.1f}s - {segment['end']:.1f}s]")
                    print(f"  {segment['text']}")
                    print()

# استفاده
stream_transcribe("audio.wav", language="fa")
```

### 3. JavaScript/Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const fetch = require('node-fetch');

async function streamTranscribe(audioFile, language = 'fa') {
  const form = new FormData();
  form.append('file', fs.createReadStream(audioFile));
  form.append('language', language);

  const response = await fetch('http://localhost:16000/transcribe/stream/', {
    method: 'POST',
    body: form
  });

  // Read stream line by line
  const reader = response.body;
  let buffer = '';

  for await (const chunk of reader) {
    buffer += chunk.toString();
    const lines = buffer.split('\n');
    buffer = lines.pop(); // Keep incomplete line

    for (const line of lines) {
      if (line.trim()) {
        const segment = JSON.parse(line);
        console.log(`[${segment.start}s - ${segment.end}s] ${segment.text}`);
      }
    }
  }
}

// Usage
streamTranscribe('audio.wav', 'fa');
```

### 4. Python با Progress Bar

```python
import requests
import json
from tqdm import tqdm

def stream_with_progress(audio_file, language="fa"):
    url = "http://localhost:16000/transcribe/stream/"

    segments = []

    with open(audio_file, 'rb') as f:
        files = {'file': f}
        data = {'language': language, 'beam_size': 10}

        with requests.post(url, files=files, data=data, stream=True) as response:
            # Create progress bar
            with tqdm(desc="Transcribing", unit="segment") as pbar:
                for line in response.iter_lines():
                    if line:
                        segment = json.loads(line)
                        segments.append(segment)

                        # Update progress
                        pbar.update(1)
                        pbar.set_postfix({
                            'time': f"{segment['end']:.1f}s",
                            'chars': len(segment['text'])
                        })

    # Combine all segments
    full_text = ' '.join(s['text'] for s in segments)

    return full_text, segments

# Usage
text, segments = stream_with_progress("audio.wav", "fa")
print(f"\nFull transcription:\n{text}")
```

### 5. ذخیره در فایل (NDJSON)

```bash
curl -X POST "http://localhost:16000/transcribe/stream/" \
  -F "file=@audio.wav" \
  -F "language=fa" \
  -N -o output.ndjson

# تبدیل به JSON معمولی
jq -s '.' output.ndjson > output.json
```

### 6. Real-time UI Update (FastAPI + WebSocket)

```python
from fastapi import FastAPI, WebSocket
import requests
import json
import asyncio

app = FastAPI()

@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    await websocket.accept()

    # دریافت فایل از client
    audio_data = await websocket.receive_bytes()

    # ذخیره موقت
    with open("temp.wav", "wb") as f:
        f.write(audio_data)

    # Stream به client
    url = "http://localhost:16000/transcribe/stream/"
    with open("temp.wav", "rb") as f:
        files = {'file': f}
        data = {'language': 'fa'}

        with requests.post(url, files=files, data=data, stream=True) as response:
            for line in response.iter_lines():
                if line:
                    segment = json.loads(line)
                    # ارسال به client
                    await websocket.send_json(segment)

    await websocket.close()
```

---

## 🎯 Use Cases

### 1. Live Transcription Dashboard

برای نمایش real-time در UI:

```javascript
// React component
function LiveTranscription({ audioFile }) {
  const [segments, setSegments] = useState([]);

  useEffect(() => {
    const formData = new FormData();
    formData.append('file', audioFile);
    formData.append('language', 'fa');

    fetch('http://localhost:16000/transcribe/stream/', {
      method: 'POST',
      body: formData
    }).then(response => {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      function readStream() {
        reader.read().then(({ done, value }) => {
          if (done) return;

          const lines = decoder.decode(value).split('\n');
          lines.forEach(line => {
            if (line.trim()) {
              const segment = JSON.parse(line);
              setSegments(prev => [...prev, segment]);
            }
          });

          readStream();
        });
      }

      readStream();
    });
  }, [audioFile]);

  return (
    <div>
      {segments.map((seg, i) => (
        <div key={i}>
          <span>[{seg.start.toFixed(1)}s - {seg.end.toFixed(1)}s]</span>
          <p>{seg.text}</p>
        </div>
      ))}
    </div>
  );
}
```

### 2. Subtitle Generator

تبدیل segments به SRT format:

```python
def segments_to_srt(segments):
    """تبدیل segments به فرمت SRT"""
    srt_lines = []

    for i, seg in enumerate(segments, 1):
        start = format_srt_time(seg['start'])
        end = format_srt_time(seg['end'])
        text = seg['text']

        srt_lines.append(f"{i}")
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(text)
        srt_lines.append("")  # Empty line

    return '\n'.join(srt_lines)

def format_srt_time(seconds):
    """تبدیل ثانیه به فرمت SRT (00:00:00,000)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

# Usage
url = "http://localhost:16000/transcribe/stream/"
segments = []

with open("audio.wav", "rb") as f:
    response = requests.post(url, files={'file': f}, data={'language': 'fa'}, stream=True)
    for line in response.iter_lines():
        if line:
            segments.append(json.loads(line))

# Generate SRT
srt_content = segments_to_srt(segments)
with open("subtitles.srt", "w", encoding="utf-8") as f:
    f.write(srt_content)
```

### 3. Batch Processing با Progress

```python
import glob
from pathlib import Path

def batch_stream_transcribe(audio_dir, output_dir, language="fa"):
    """پردازش دسته‌ای فایل‌های صوتی"""
    audio_files = glob.glob(f"{audio_dir}/*.wav")

    for audio_file in tqdm(audio_files, desc="Files"):
        filename = Path(audio_file).stem
        output_file = f"{output_dir}/{filename}.json"

        segments = []

        url = "http://localhost:16000/transcribe/stream/"
        with open(audio_file, 'rb') as f:
            response = requests.post(
                url,
                files={'file': f},
                data={'language': language, 'beam_size': 10},
                stream=True
            )

            for line in response.iter_lines():
                if line:
                    segments.append(json.loads(line))

        # ذخیره
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'file': filename,
                'segments': segments,
                'full_text': ' '.join(s['text'] for s in segments)
            }, f, ensure_ascii=False, indent=2)

# Usage
batch_stream_transcribe('./audio_files', './transcriptions', language='fa')
```

---

## 🔧 تنظیمات پیشرفته

### بهینه‌سازی برای Latency کم

```bash
# کمترین latency (ممکن است دقت کمتری داشته باشد)
curl -X POST "http://localhost:16000/transcribe/stream/" \
  -F "file=@audio.wav" \
  -F "language=fa" \
  -F "beam_size=1" \
  -F "vad_filter=false" \
  -N
```

### بهینه‌سازی برای دقت بالا

```bash
# بالاترین دقت (latency بیشتر)
curl -X POST "http://localhost:16000/transcribe/stream/" \
  -F "file=@audio.wav" \
  -F "language=fa" \
  -F "beam_size=10" \
  -F "vad_filter=true" \
  -N
```

### Timeout Configuration

```python
# برای فایل‌های خیلی طولانی
response = requests.post(
    url,
    files=files,
    data=data,
    stream=True,
    timeout=(30, 600)  # (connect timeout, read timeout)
)
```

---

## 📊 مقایسه عملکرد

| Scenario | Stream API | Regular API | مزیت |
|----------|------------|-------------|------|
| فایل 30 ثانیه | TTFS: ~0.5s | Response: ~2s | ⚡ Stream سریعتر |
| فایل 5 دقیقه | TTFS: ~0.5s | Response: ~15s | ⚡⚡ Stream خیلی سریعتر |
| Batch 100 فایل | مشابه | مشابه | 🔄 یکسان |
| UI Real-time | ✅ عالی | ❌ نامناسب | ✅ Stream |

**TTFS**: Time To First Segment

---

## ⚠️ نکات مهم

### 1. Memory Management

```python
# ✅ GOOD: استفاده از streaming
with requests.post(url, files=files, stream=True) as response:
    for line in response.iter_lines():
        process(line)

# ❌ BAD: بارگذاری کل response در حافظه
response = requests.post(url, files=files)
content = response.content  # Loads everything!
```

### 2. Error Handling

```python
try:
    with requests.post(url, files=files, stream=True, timeout=300) as response:
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    segment = json.loads(line)
                    yield segment
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {line}")

except requests.exceptions.Timeout:
    logger.error("Request timed out")
except requests.exceptions.RequestException as e:
    logger.error(f"Request failed: {e}")
```

### 3. Connection Pooling

```python
# برای requests متعدد
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=10,
    max_retries=3
)
session.mount('http://', adapter)

# استفاده
response = session.post(url, files=files, stream=True)
```

---

## 🐛 عیب‌یابی

### مشکل: "Connection reset"

**علت:** Timeout یا مشکل network

**راه‌حل:**
```python
response = requests.post(url, files=files, stream=True, timeout=(30, 600))
```

### مشکل: "Empty responses"

**علت:** فایل صوتی خراب یا فرمت نامعتبر

**راه‌حل:**
```bash
# بررسی فایل
ffprobe audio.wav

# تبدیل به فرمت استاندارد
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

### مشکل: "Slow streaming"

**علت:** CPU/GPU زیاد مشغول است

**راه‌حل:**
- کاهش `beam_size`
- افزایش منابع سرور
- استفاده از compute_type سبک‌تر (int8)

---

## 📚 منابع بیشتر

- [FastAPI Streaming Responses](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [NDJSON Format](http://ndjson.org/)
- [Requests Streaming](https://requests.readthedocs.io/en/latest/user/advanced/#streaming-requests)

---

**آخرین آپدیت:** 2025-10-18
**نسخه:** 1.0
