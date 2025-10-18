# 🔧 راهنمای رفع خطای CORS

راه‌حل کامل برای خطای CORS در Whisper Service

---

## ❌ خطای CORS چیست؟

```
Access to fetch at 'http://services.aiopt.io:16000/' from origin 'http://localhost:8080'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on
the requested resource.
```

این خطا زمانی رخ می‌دهد که:
- **Frontend** (HTML) روی یک domain است (مثلاً `localhost:8080`)
- **Backend** (API) روی domain دیگری است (مثلاً `services.aiopt.io:16000`)
- Backend اجازه دسترسی cross-origin نمی‌دهد

---

## ✅ راه‌حل: اضافه کردن CORS Middleware

### مرحله 1: آپدیت کد FastAPI

فایل `faster-whisper-service.py` را ویرایش کنید:

#### 1. Import کردن CORS:

```python
from fastapi.middleware.cors import CORSMiddleware
```

#### 2. اضافه کردن Middleware (بعد از `app = FastAPI(...)`):

```python
app = FastAPI(
    title="⚡ High-Throughput Whisper Service (Faster Whisper)",
    description="Fast, batched speech-to-text service using Faster Whisper with advanced chunking",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### مرحله 2: Rebuild و Restart سرویس

#### اگر از Docker استفاده می‌کنید:

```bash
# توقف کانتینر
docker-compose down whisper-gpu

# Rebuild image
docker-compose build --no-cache whisper-gpu

# اجرای مجدد
docker-compose up -d whisper-gpu

# بررسی لاگ
docker logs -f whisper-service-gpu
```

#### اگر مستقیم اجرا می‌کنید:

```bash
# توقف سرویس (Ctrl+C)

# اجرای مجدد
python faster-whisper-service.py
```

---

### مرحله 3: تست CORS

#### با Browser Console:

```javascript
fetch('http://services.aiopt.io:16000/')
  .then(r => r.json())
  .then(d => console.log('✅ CORS works!', d))
  .catch(e => console.error('❌ CORS error:', e));
```

#### با curl:

```bash
curl -H "Origin: http://localhost:8080" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://services.aiopt.io:16000/transcribe/ \
     -v
```

**انتظار:** باید header `Access-Control-Allow-Origin: *` را ببینید

---

## 🔒 نسخه امن برای Production

برای محیط تولید، از `allow_origins=["*"]` استفاده نکنید!

### روش 1: Origins مشخص

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://services.aiopt.io",
        "https://yourapp.com"
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)
```

### روش 2: Dynamic Origins (بر اساس Environment)

```python
import os

# در config.py
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:8080").split(",")

# در faster-whisper-service.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

سپس در `docker-compose.yml`:

```yaml
environment:
  - CORS_ORIGINS=http://localhost:8080,http://services.aiopt.io,https://yourapp.com
```

---

## 🎯 تنظیمات پیشنهادی

### Development:

```python
allow_origins=["*"]  # همه origins
allow_methods=["*"]  # همه methods
allow_headers=["*"]  # همه headers
```

### Production:

```python
allow_origins=[
    "https://yourapp.com",
    "https://www.yourapp.com"
]
allow_credentials=True
allow_methods=["GET", "POST", "OPTIONS"]
allow_headers=["Content-Type", "Authorization"]
```

---

## 🐛 عیب‌یابی

### مشکل 1: هنوز خطا می‌گیرم

**چک‌لیست:**
- [ ] سرویس را restart کردید؟
- [ ] Cache مرورگر را پاک کردید؟ (Ctrl+Shift+R)
- [ ] در DevTools → Network → بررسی کنید header `Access-Control-Allow-Origin` وجود دارد؟

```bash
# بررسی headers
curl -I http://services.aiopt.io:16000/
```

### مشکل 2: Preflight request failed

**علت:** مرورگر یک OPTIONS request ارسال می‌کند قبل از POST

**راه‌حل:** CORS middleware خودکار این را handle می‌کند، ولی اگر مشکل دارید:

```python
@app.options("/transcribe/")
async def transcribe_options():
    return {"message": "OK"}
```

### مشکل 3: با curl کار می‌کند اما با browser نه

**علت:** curl CORS را check نمی‌کند، browser می‌کند

**راه‌حل:** از browser console استفاده کنید:

```javascript
fetch('http://services.aiopt.io:16000/', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json'
  }
})
.then(r => r.json())
.then(d => console.log('Success:', d))
.catch(e => console.error('Error:', e));
```

---

## 📊 بررسی CORS Headers

### Headers که باید ببینید:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
Access-Control-Allow-Headers: *
Access-Control-Allow-Credentials: true
```

### چک کردن با DevTools:

1. باز کردن DevTools (F12)
2. رفتن به tab "Network"
3. کلیک روی request
4. مشاهده "Response Headers"

---

## 🌐 CORS با Reverse Proxy (Nginx)

اگر از Nginx استفاده می‌کنید:

```nginx
server {
    listen 80;
    server_name services.aiopt.io;

    location / {
        proxy_pass http://localhost:16000;

        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'Content-Type';

        # Preflight
        if ($request_method = 'OPTIONS') {
            return 204;
        }

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## ✅ تست نهایی

بعد از اعمال تغییرات:

### 1. Health Check:

```bash
curl http://services.aiopt.io:16000/
```

**خروجی موردانتظار:**
```json
{
  "status": "ok",
  "service": "faster-whisper",
  "model": "203-final-ct2",
  "device": "cuda"
}
```

### 2. CORS Test:

باز کردن HTML interface و مشاهده console:

```
✅ API is available
Model: 203-final-ct2
Device: cuda
```

### 3. Full Test:

کلیک روی "شروع ضبط" و صحبت کردن. اگر متن ظاهر شد = موفق! 🎉

---

## 📝 Checklist کامل

- [ ] `from fastapi.middleware.cors import CORSMiddleware` اضافه شد
- [ ] `app.add_middleware(CORSMiddleware, ...)` اضافه شد
- [ ] سرویس restart شد
- [ ] با curl تست شد
- [ ] با browser console تست شد
- [ ] HTML interface کار می‌کند
- [ ] برای production، origins محدود شدند

---

## 🔗 منابع

- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [MDN CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [CORS Explained](https://web.dev/cross-origin-resource-sharing/)

---

**آخرین آپدیت:** 2025-10-18

موفق باشید! 🚀
