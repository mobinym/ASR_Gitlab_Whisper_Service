Got it ✅  
Since you want the README file to be in **English** and strong enough for GitHub, I’ll write a **clear, professional, and well-structured README** in Markdown format that explains the code, usage, features, and setup instructions.

Here’s your README:  




# 🎙️ Farsi Speech-to-Text API (Whisper Auto-Chunking)

A **FastAPI-based** service for converting **Persian (Farsi) speech to text** using [OpenAI Whisper](https://huggingface.co/openai/whisper) with **automatic chunking** and **custom audio preprocessing** for better results.  

This service comes with:
- 🚀 **High-quality speech transcription** optimized for Persian language.
- 🎯 **Automatic chunking** for processing long audio files.
- 🎛 **Advanced audio preprocessing** (silence trimming, noise reduction, compression, normalization).
- ⚡ GPU acceleration when available.
- 📦 Easy Docker deployment.

---

## ✨ Features
- **Persian (Farsi)** speech-to-text transcription.
- **Supports multiple Whisper models** stored in `/data/models`.
- **Automatic model loading** from `.env` file.
- **Custom audio preprocessing pipeline**:
  - Silence trimming
  - Noise reduction (spectral subtraction)
  - Dynamic range compression
  - Loudness normalization
- **REST API endpoints**:
  - `/transcribe/` → Upload and transcribe audio
  - `/models/` → List available models
  - `/` → API health check

---

## 📂 Project Structure
├── service.py               # Main FastAPI application
├── requirements.txt         # Python dependencies
├── .env                      # Environment variables
└── /data/models/             # Directory containing Whisper models




## ⚙️ Requirements

### Python Dependencies
Listed in `requirements.txt`:
```
fastapi
uvicorn
librosa
numpy
soundfile
transformers
python-dotenv
torch>=2.2.0
python-multipart
resampy
```

---

## 🚀 Quick Start

### 1️⃣ Prepare Models
Place your Whisper models in `/data/models/<model_name>/`.  
Example:
```
/data/models/301-final-bf16
```

---

### 2️⃣ Set Environment Variables
Create a `.env` file:
```env
DEFAULT_MODEL_NAME=301-final-bf16
```

---

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

---

### 4️⃣ Run the API Server
```bash
python service.py
```

Or with **Uvicorn** directly:
```bash
uvicorn service:app --host 0.0.0.0 --port 8000
```

---

### 5️⃣ Usage Example

#### **Upload and Transcribe Audio**
```bash
curl -X POST "http://localhost:8000/transcribe/" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@example.wav"
```

Response:
```json
{
    "transcription": "سلام. حال شما چطور است؟",
    "model_used": "301-final-bf16",
    "method": "whisper_auto_chunking"
}
```

#### **List Available Models**
```bash
curl http://localhost:8000/models/
```

#### **Health Check**
```bash
curl http://localhost:8000/
```

---

## 🖥️ Docker Deployment

### **Dockerfile Example**
```dockerfile
FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime
WORKDIR /app/service
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "service.py"]
```

Run:
```bash
docker build -t whisper-farsi-service .
docker run -it --rm -p 8000:8000 whisper-farsi-service
```

---

## 📌 API Endpoints

| Method | Endpoint      | Description                           |
|--------|--------------|---------------------------------------|
| `GET`  | `/`          | Health check                          |
| `GET`  | `/models/`   | List all available Whisper models     |
| `POST` | `/transcribe/`| Upload an audio file and get text     |

---

## 🛠️ Configuration

- **`DEFAULT_MODEL_NAME`** (env var) → The model loaded at startup.
- Models must be stored under `/data/models/<model_name>/`.
- **GPU** is used automatically if available (`torch.cuda.is_available()`).

---

## 📜 License
This project is licensed under the **MIT License**.

---

## 💡 Notes
- Audio files are preprocessed before transcription to improve accuracy.
- Long audio files are split automatically using **Whisper’s chunking** method.
- Works best with clean and clear speech at 16kHz.

