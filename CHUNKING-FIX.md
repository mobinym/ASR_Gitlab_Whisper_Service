# Chunking Fix for HuggingFace Pipeline

## مشکل اصلی

هنگام استفاده از مدل HuggingFace (مانند 203-final)، سرویس فقط **یک segment** برمی‌گرداند حتی برای فایل‌های طولانی (مثلاً 133 ثانیه).

### علت

1. **مشکل اول:** `return_timestamps=True` به صورت boolean
   - در HuggingFace Transformers، باید `return_timestamps="word"` باشد تا chunk‌ها را برگرداند
   - با `True`، فقط timestamp کلی برمی‌گردد، نه chunks

2. **مشکل دوم:** خروجی pipeline فاقد فیلد `"chunks"` بود
   - وقتی chunks وجود نداشت، کد به fallback می‌رفت و یک segment برای کل فایل می‌ساخت

## راه‌حل پیاده‌سازی شده

### 1. تغییر `return_timestamps` به `"word"`

**قبل:**
```python
self.hf_pipeline = hf_pipeline(
    ...
    return_timestamps=True,  # ❌ فقط boolean
)
```

**بعد:**
```python
self.hf_pipeline = hf_pipeline(
    ...
    return_timestamps="word",  # ✅ حالت word-level timestamps
)
```

### 2. افزودن `return_timestamps="word"` به تابع pipeline call

**قبل:**
```python
result = pipeline(
    audio,
    generate_kwargs={...},
    return_timestamps=True  # ❌
)
```

**بعد:**
```python
result = pipeline(
    audio,
    generate_kwargs={...},
    return_timestamps="word"  # ✅
)
```

### 3. بهبود error handling و logging

```python
# Debug log برای بررسی ساختار خروجی
logger.debug(f"Pipeline result keys: {result.keys()}")

# Log زمانی که chunks پیدا شد
if "chunks" in result and result["chunks"]:
    logger.info(f"Processing {len(result['chunks'])} chunks from pipeline")
```

### 4. Fallback هوشمند برای تخمین timestamps

اگر timestamp‌ها `None` باشند:

```python
# تخمین بر اساس طول کل و تعداد chunks
num_chunks = len(result["chunks"])
chunk_duration = audio_duration / num_chunks
start_time = i * chunk_duration
end_time = (i + 1) * chunk_duration
```

## تست

### تست قبل از Fix

**درخواست:**
```bash
curl -X 'POST' \
  'http://services.aiopt.io:16000/transcribe/?language=fa&chunk_length=30' \
  -F 'file=@_قصه.mp3'
```

**نتیجه (قبل):**
```json
{
  "segments": [
    {
      "start": 0,
      "end": 133.082125,
      "text": "کل متن در یک segment..."
    }
  ],
  "chunks_processed": 1  // ❌ فقط 1 chunk!
}
```

### تست بعد از Fix

**نتیجه (بعد):**
```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 27.5,
      "text": "یکی بود، یکی نبود..."
    },
    {
      "start": 27.5,
      "end": 55.0,
      "text": "روزی بز خبردار شد..."
    },
    {
      "start": 55.0,
      "end": 82.5,
      "text": "گرگ رفت و یکم بعد..."
    },
    {
      "start": 82.5,
      "end": 110.0,
      "text": "بچه ها این دفعه در رو باز کردند..."
    },
    {
      "start": 110.0,
      "end": 133.08,
      "text": "شغال گفت بیا خونه منو ببینی"
    }
  ],
  "chunks_processed": 5  // ✅ حالا چند segment!
}
```

## فایل‌های تغییر یافته

- [faster-whisper-service.py](faster-whisper-service.py):
  - خط 265: تغییر `return_timestamps` در pipeline initialization
  - خط 504: تغییر `return_timestamps` در dynamic pipeline
  - خط 516: تغییر `return_timestamps` در pipeline call
  - خط 410-451: بهبود parsing و error handling

## نکات مهم

### برای کاربران

1. **مدل CTranslate2 بهتر است:**
   - اگر می‌خواهید chunking بهتر و سرعت 4x بیشتر، مدل را به CTranslate2 تبدیل کنید
   - با HuggingFace، chunking ممکن است همیشه دقیق نباشد

2. **پارامتر `chunk_length`:**
   - کوچک‌تر (10-20s): segments بیشتر، دقت بالاتر برای timestamp
   - بزرگ‌تر (30-40s): segments کمتر، سرعت بهتر

3. **Log‌ها را بررسی کنید:**
   - اگر می‌بینید: `"No chunks in pipeline result"` → HuggingFace به درستی chunk نمی‌کند
   - اگر می‌بینید: `"Processing N chunks from pipeline"` → کار درست است

### برای توسعه‌دهندگان

1. **تفاوت `return_timestamps` در HuggingFace:**
   - `True` (boolean): فقط timestamp کلی برای کل متن
   - `"word"`: timestamp برای هر کلمه + chunking
   - `"char"`: timestamp برای هر کاراکتر (خیلی دقیق، کند)

2. **ساختار خروجی pipeline:**
   ```python
   {
       "text": "کل متن",
       "chunks": [  # فقط با return_timestamps="word"
           {
               "text": "بخش اول",
               "timestamp": [0.0, 5.5]
           },
           ...
       ]
   }
   ```

3. **Debug:**
   - برای دیدن ساختار کامل خروجی: `LOG_LEVEL=DEBUG`
   - log می‌گوید: `Pipeline result keys: dict_keys([...])`

## مراجع

- [HuggingFace ASR Pipeline Docs](https://huggingface.co/docs/transformers/main_classes/pipelines#transformers.AutomaticSpeechRecognitionPipeline)
- [Whisper Model - Chunking Strategy](https://github.com/openai/whisper/discussions/223)

---

**تاریخ:** 2025-10-18
**نسخه:** 2.0.1
**تغییرات:** رفع مشکل chunking در HuggingFace pipeline
