# 🎯 راهنمای بهبود دقت مدل Whisper

این راهنما روش‌های مختلف برای بهبود دقت transcription را توضیح می‌دهد.

---

## 📊 مقایسه Compute Types

| Compute Type | دقت (WER) | سرعت نسبی | مصرف VRAM | پشتیبانی GPU |
|--------------|-----------|-----------|-----------|--------------|
| **float32** | ⭐⭐⭐⭐⭐ (بهترین) | 1x (پایه) | زیاد | همه |
| **bfloat16** | ⭐⭐⭐⭐⭐ (تقریباً مثل float32) | 2x سریعتر | متوسط | Ampere+ (RTX 30xx, A100) |
| **float16** | ⭐⭐⭐⭐ (خوب) | 2x سریعتر | متوسط | همه (Volta+) |
| **int8_float16** | ⭐⭐⭐ (متوسط) | 3x سریعتر | کم | همه |
| **int8** | ⭐⭐ (قابل قبول) | 4x سریعتر | خیلی کم | همه |

---

## 🚀 راه‌های بهبود دقت

### 1️⃣ تغییر Compute Type (تأثیر: ⭐⭐⭐⭐⭐)

#### گزینه A: استفاده از bfloat16 (توصیه شده برای GPU های جدید)

```yaml
# docker-compose.yml
- COMPUTE_TYPE=bfloat16
```

**مزایا:**
- ✅ دقت تقریباً مثل float32
- ✅ سرعت 2x بیشتر از float32
- ✅ مصرف VRAM معقول

**نیازمندی:**
- GPU Ampere یا جدیدتر (RTX 30xx, RTX 40xx, A100, H100)

**چگونه بررسی کنیم؟**
```bash
docker exec whisper-service-gpu nvidia-smi --query-gpu=name --format=csv,noheader
```

#### گزینه B: استفاده از float32 (بالاترین دقت)

```yaml
# docker-compose.yml
- COMPUTE_TYPE=float32
```

**مزایا:**
- ✅ بالاترین دقت ممکن
- ✅ کار می‌کند روی همه GPU ها

**معایب:**
- ⚠️ 2x کندتر از float16/bfloat16
- ⚠️ مصرف VRAM بیشتر (~2x)

---

### 2️⃣ افزایش Beam Size (تأثیر: ⭐⭐⭐⭐)

```yaml
# docker-compose.yml
- BEAM_SIZE=10  # پیش‌فرض: 5
```

**توضیح:**
- Beam search با اندازه بزرگتر مسیرهای بیشتری را بررسی می‌کند
- دقت بالاتر، اما سرعت کمتر

**مقایسه:**

| Beam Size | دقت | سرعت | توصیه |
|-----------|-----|------|-------|
| 1 | ⭐⭐ | سریعترین | فقط برای draft |
| 5 | ⭐⭐⭐⭐ | سریع | **پیش‌فرض متعادل** ⚡ |
| 10 | ⭐⭐⭐⭐⭐ | متوسط | **توصیه برای دقت بالا** ✅ |
| 15 | ⭐⭐⭐⭐⭐ | کند | فقط در صورت نیاز شدید |

---

### 3️⃣ استفاده از مدل بزرگ‌تر (تأثیر: ⭐⭐⭐⭐⭐)

مدل فعلی شما: `203-final-ct2`

اگر این مدل بر اساس Whisper `base` یا `small` است، ارتقا به مدل بزرگتر **بیشترین تأثیر** را دارد:

| مدل | Parameters | WER (فارسی) | VRAM | سرعت |
|-----|-----------|-------------|------|------|
| base | 74M | ~15% | 1 GB | سریع |
| small | 244M | ~10% | 2 GB | متوسط |
| medium | 769M | ~6% | 5 GB | کندتر |
| large-v2 | 1.55B | ~4% | 10 GB | کند |
| large-v3 | 1.55B | **~3.5%** ✅ | 10 GB | کند |

**چگونه بررسی کنیم مدل ما چه سایزی است؟**
```bash
docker exec whisper-service-gpu python -c "
from faster_whisper import WhisperModel
model = WhisperModel('/data/models/203-final-ct2')
print(f'Model info: {model}')
"
```

---

### 4️⃣ تنظیمات پیشرفته (تأثیر: ⭐⭐⭐)

این تنظیمات در کد [faster-whisper-service.py:508-521] هستند:

```python
# فعلی (متعادل):
temperature=0.0,
compression_ratio_threshold=2.4,
log_prob_threshold=-1.0,
no_speech_threshold=0.6,
```

**برای دقت بهتر:**
```python
temperature=0.0,  # بدون randomness
compression_ratio_threshold=2.0,  # سخت‌گیرانه‌تر برای متن تکراری
log_prob_threshold=-0.8,  # فقط نتایج با احتمال بالا
no_speech_threshold=0.7,  # حساس‌تر به سکوت
```

---

### 5️⃣ بهبود کیفیت صدای ورودی (تأثیر: ⭐⭐⭐⭐)

#### تنظیمات پیش‌پردازش:

```yaml
# docker-compose.yml
environment:
  - TRIM_TOP_DB=30  # حذف سکوت بهتر (پیش‌فرض: 25)
  - NORMALIZATION_TARGET_DB=-20.0  # نرمال‌سازی قوی‌تر (پیش‌فرض: -23)
```

#### آماده‌سازی صدا قبل از transcription:

1. **حذف نویز:** از Audacity یا ffmpeg استفاده کنید
2. **فرمت مناسب:** WAV 16kHz mono بهترین نتیجه را می‌دهد
3. **قطع سکوت:** سکوت‌های طولانی را حذف کنید

```bash
# مثال با ffmpeg:
ffmpeg -i input.mp3 \
  -ar 16000 \
  -ac 1 \
  -af "highpass=f=200, lowpass=f=3000, afftdn" \
  output.wav
```

---

## 🎛️ پروفایل‌های آماده

### پروفایل 1: سرعت بالا (فعلی)

```bash
docker-compose up -d whisper-gpu
```

```yaml
- COMPUTE_TYPE=float16
- BEAM_SIZE=5
- BATCH_SIZE=16
```

**استفاده:** transcription سریع، دقت خوب

---

### پروفایل 2: دقت بالا (جدید) ✅

```bash
docker-compose --profile accuracy up -d
```

```yaml
- COMPUTE_TYPE=bfloat16  # یا float32
- BEAM_SIZE=10
- BATCH_SIZE=8
```

**استفاده:** وقتی دقت بالا اولویت است
**پورت:** 16001

---

### پروفایل 3: دقت حداکثر (دستی)

در `docker-compose.yml` تغییر دهید:

```yaml
environment:
  - COMPUTE_TYPE=float32
  - BEAM_SIZE=15
  - BATCH_SIZE=4
  - VAD_FILTER=true
```

**استفاده:** برای صداهای چالش‌برانگیز
**هشدار:** 3-4x کندتر!

---

## 📈 نحوه تست و مقایسه

### 1. آماده‌سازی:

```bash
# فایل تست آماده کنید
cp your_test_audio.wav test.wav
```

### 2. تست با تنظیمات مختلف:

```bash
# تست 1: float16 + beam=5
curl -X POST http://localhost:16000/transcribe/ \
  -F "file=@test.wav" \
  -F "language=fa" \
  -F "beam_size=5" \
  | jq '.transcription' > result_float16_beam5.txt

# تست 2: bfloat16 + beam=10
curl -X POST http://localhost:16001/transcribe/ \
  -F "file=@test.wav" \
  -F "language=fa" \
  -F "beam_size=10" \
  | jq '.transcription' > result_bfloat16_beam10.txt

# تست 3: float32 + beam=10
# (ابتدا COMPUTE_TYPE=float32 تنظیم کنید)
curl -X POST http://localhost:16000/transcribe/ \
  -F "file=@test.wav" \
  -F "language=fa" \
  -F "beam_size=10" \
  | jq '.transcription' > result_float32_beam10.txt
```

### 3. مقایسه نتایج:

```bash
# مقایسه دستی
diff result_float16_beam5.txt result_bfloat16_beam10.txt
diff result_float16_beam5.txt result_float32_beam10.txt
```

---

## 🎯 توصیه نهایی

### سناریو 1: GPU جدید دارید (RTX 30xx+)
```yaml
COMPUTE_TYPE=bfloat16
BEAM_SIZE=10
```
**نتیجه:** بهترین تعادل بین دقت و سرعت ✅

### سناریو 2: GPU قدیمی‌تر (RTX 20xx, V100)
```yaml
COMPUTE_TYPE=float16
BEAM_SIZE=10
```
**نتیجه:** دقت خوب با سرعت قابل قبول

### سناریو 3: نیاز به بالاترین دقت
```yaml
COMPUTE_TYPE=float32
BEAM_SIZE=15
BATCH_SIZE=4
```
**نتیجه:** بالاترین دقت، اما کندتر

### سناریو 4: صداهای پرنویز
```yaml
COMPUTE_TYPE=bfloat16
BEAM_SIZE=10
TRIM_TOP_DB=30
# + پیش‌پردازش صدا با ffmpeg
```

---

## ❓ سوالات متداول

### Q: آیا bfloat16 واقعاً دقت را حفظ می‌کند؟

**A:** بله! bfloat16 رنج dynamic مثل float32 دارد (اما precision کمتر). برای Whisper، تفاوت WER معمولاً < 0.5% است.

### Q: چرا float32 کندتر است؟

**A:** عملیات ریاضی روی 32-bit طولانی‌تر است و Tensor Cores GPU نمی‌توانند استفاده شوند.

### Q: آیا می‌توانم همزمان هر دو پروفایل را اجرا کنم؟

**A:** بله! پورت‌های مختلف دارند:
- پروفایل سرعت: `localhost:16000`
- پروفایل دقت: `localhost:16001`

```bash
docker-compose up -d whisper-gpu
docker-compose --profile accuracy up -d
```

---

## 🔗 منابع بیشتر

- [CTranslate2 Quantization Guide](https://opennmt.net/CTranslate2/quantization.html)
- [Faster Whisper Performance Tips](https://github.com/SYSTRAN/faster-whisper#performance)
- [OpenAI Whisper Paper](https://arxiv.org/abs/2212.04356)

---

**آخرین آپدیت:** 2025-10-18
**نسخه:** 1.0
