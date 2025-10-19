# Faster Whisper Service

A **high-throughput, production-ready** FastAPI-based speech-to-text service supporting both **CTranslate2 (Faster Whisper)** and **HuggingFace (PyTorch)** model formats, optimized for Persian/Farsi transcription with multi-format audio support.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch 2.7+](https://img.shields.io/badge/PyTorch-2.7+-red.svg)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.x-green.svg)](https://fastapi.tiangolo.com/)

---

## Features

- ⚡ **4x faster** than standard Whisper (when using CTranslate2)
- 🔄 **Dual model format support** - Automatic format detection (CTranslate2/HuggingFace)
- 🎯 **Advanced chunking** with Voice Activity Detection (VAD)
- 🌊 **Streaming support** for real-time transcription (NDJSON format)
- 🔧 **Type-safe configuration** with Pydantic Settings
- 🐳 **Production-ready Docker** deployment with GPU/CPU/Accuracy profiles
- 📊 **Batched inference** for maximum throughput
- 🎙️ **Multi-format audio support** - WebM, MP3, WAV, FLAC, M4A, OGG, AAC, etc.
- 🛡️ **Enterprise features** - Health checks, logging, CORS support
- 🎛️ **Advanced audio preprocessing** - Noise reduction, normalization, silence trimming
- 🔧 **bfloat16 support** for better accuracy on modern GPUs (Ampere+)

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Clone repository
git clone <repo-url>
cd whisper-service

# 2. Create models directory and place your models
mkdir -p /data/models
# Copy your Whisper model to /data/models/<model_name>

# 3. Run with Docker Compose (GPU)
docker-compose up -d

# 4. Check health
curl http://localhost:16000/
```

### Option 2: Direct Python

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
nano .env  # Edit DEFAULT_MODEL_NAME and MODELS_BASE_DIR

# 3. Run service
python faster-whisper-service.py

# 4. Check health
curl http://localhost:8000/
```

---

## API Endpoints

### Health Check
```bash
GET /
```

**Response:**
```json
{
  "status": "ok",
  "service": "faster-whisper",
  "version": "2.0.0",
  "model": "203-final",
  "device": "cuda",
  "compute_type": "float16",
  "batch_size": 16,
  "max_workers": 4
}
```

### List Available Models
```bash
GET /models/
```

**Response:**
```json
{
  "available_models": ["203-final", "301-final-bf16"],
  "current_model": "203-final",
  "device": "cuda",
  "compute_type": "float16"
}
```

### Transcribe Audio
```bash
POST /transcribe/
```

**Parameters:**
- `file` (required): Audio file (WAV, MP3, WebM, FLAC, M4A, OGG, AAC, etc.)
- `language` (optional): Language code (e.g., 'fa', 'en', 'ar'). Default: 'fa'
- `task` (optional): 'transcribe' or 'translate'. Default: 'transcribe'
- `beam_size` (optional): Beam size for decoding (1-10). Default: 5
- `vad_filter` (optional): Enable Voice Activity Detection. Default: true
- `word_timestamps` (optional): Return word-level timestamps. Default: false
- `chunk_length` (optional): Chunk length in seconds. Default: 30

**Example:**
```bash
# Basic transcription (Persian)
curl -X POST http://localhost:8000/transcribe/ \
  -F "file=@audio.wav" \
  -F "language=fa"

# Advanced parameters
curl -X POST http://localhost:8000/transcribe/ \
  -F "file=@audio.mp3" \
  -F "language=en" \
  -F "beam_size=10" \
  -F "vad_filter=true" \
  -F "word_timestamps=true" \
  -F "chunk_length=30"

# Multi-format support (WebM from browser recording)
curl -X POST http://localhost:8000/transcribe/ \
  -F "file=@recording.webm" \
  -F "language=fa"
```

**Response:**
```json
{
  "transcription": "سلام. حال شما چطور است؟",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "سلام."
    },
    {
      "start": 2.5,
      "end": 5.0,
      "text": "حال شما چطور است؟"
    }
  ],
  "language": "fa",
  "duration": 5.0,
  "processing_time": 0.8,
  "model_used": "203-final",
  "model_type": "huggingface",
  "chunks_processed": 2
}
```

### Stream Transcription Results
```bash
POST /transcribe/stream/
```

**Parameters:** Same as `/transcribe/` (except `word_timestamps` and `chunk_length`)

**Example:**
```bash
curl -X POST http://localhost:8000/transcribe/stream/ \
  -F "file=@audio.wav" \
  -F "language=fa" \
  --no-buffer
```

**Response (NDJSON):**
```json
{"start": 0.0, "end": 2.5, "text": "سلام."}
{"start": 2.5, "end": 5.0, "text": "حال شما چطور است؟"}
```

---

## Deployment Options

### 1. Docker Compose (Production)

The project includes three deployment profiles:

#### GPU Deployment (Default - Port 16000)
Optimized for production with balanced speed/accuracy:
```bash
docker-compose up -d
```

Configuration:
- Device: CUDA
- Compute Type: float16
- Batch Size: 16
- Max Workers: 4
- Beam Size: 5

#### CPU Deployment (Port 8001)
For systems without GPU:
```bash
docker-compose --profile cpu up -d
```

Configuration:
- Device: CPU
- Compute Type: int8
- Batch Size: 4
- Max Workers: 2
- Beam Size: 5

#### High-Accuracy Deployment (Port 16001)
For best transcription quality:
```bash
docker-compose --profile accuracy up -d
```

Configuration:
- Device: CUDA (Ampere+ GPU required)
- Compute Type: bfloat16
- Batch Size: 8
- Max Workers: 2
- Beam Size: 10

### 2. Development Mode

Live code reloading for development:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Edit code locally, changes auto-reload in container.

### 3. Manual Docker

```bash
# Build
docker build -t whisper-service:latest .

# Run GPU
docker run -d \
  --gpus all \
  -v /data/models:/data/models:ro \
  -p 8000:8000 \
  -e DEFAULT_MODEL_NAME=203-final \
  -e DEVICE=cuda \
  -e COMPUTE_TYPE=float16 \
  whisper-service:latest

# Run CPU
docker run -d \
  -v /data/models:/data/models:ro \
  -p 8000:8000 \
  -e DEFAULT_MODEL_NAME=203-final \
  -e DEVICE=cpu \
  -e COMPUTE_TYPE=int8 \
  whisper-service:latest
```

---

## Configuration

All settings can be configured via environment variables or `.env` file.

### Environment Variables

```env
# Model Configuration
DEFAULT_MODEL_NAME=203-final          # Model name or HuggingFace ID
MODELS_BASE_DIR=/data/models          # Local models directory

# Device Configuration
DEVICE=cuda                           # cuda | cpu
COMPUTE_TYPE=float16                  # float32 | bfloat16 | float16 | int8_float16 | int8

# Performance Configuration
MAX_WORKERS=4                         # Number of worker threads (1-32)
BATCH_SIZE=16                         # Batch size for inference (1-64)

# Transcription Settings
VAD_FILTER=true                       # Voice Activity Detection
BEAM_SIZE=5                           # Beam size for decoding (1-10)

# Audio Processing
TARGET_SAMPLE_RATE=16000              # Target sample rate (Hz)
TRIM_TOP_DB=25                        # Silence trimming threshold (dB)
NORMALIZATION_TARGET_DB=-23.0         # Loudness normalization target (LUFS)

# Server Configuration
HOST=0.0.0.0                          # Server host
PORT=8000                             # Server port (1-65535)
LOG_LEVEL=INFO                        # DEBUG | INFO | WARNING | ERROR | CRITICAL
```

### Compute Types Comparison

| Compute Type | Accuracy | Speed | Memory | Use Case |
|--------------|----------|-------|--------|----------|
| float32 | Best | Slowest | Highest | Highest quality (research) |
| bfloat16 | Excellent | Fast | Medium | Production (high accuracy) |
| float16 | Good | Faster | Low | Production (balanced) |
| int8_float16 | Acceptable | Fast | Lower | Production (speed priority) |
| int8 | Acceptable | Fastest | Lowest | CPU deployment |

---

## Model Support

### Dual Format Support

The service automatically detects and loads models in either format:

#### 1. CTranslate2 Format (Faster - 4x speed)

Model directory structure:
```
/data/models/model-name/
├── model.bin
├── config.json
├── vocabulary.txt
└── tokenizer.json
```

**Performance:** 4x faster than PyTorch, 50% less VRAM

#### 2. HuggingFace Format (Compatible)

Model directory structure:
```
/data/models/model-name/
├── pytorch_model.bin
├── config.json
├── tokenizer_config.json
├── preprocessor_config.json
└── ...
```

**Compatibility:** Works with existing PyTorch Whisper models

### Model Loading Strategy

1. Try to load as **CTranslate2** model (faster)
2. If fails, fallback to **HuggingFace** model (compatible)
3. Both formats use the same API

**No manual configuration needed!**

---

## Architecture

### Core Components

- **FastAPI**: Async REST API with auto-generated docs
- **Faster Whisper**: CTranslate2-based Whisper implementation (4x faster)
- **Transformers**: HuggingFace PyTorch models (backward compatibility)
- **Librosa**: Multi-format audio processing with ffmpeg backend
- **Pydantic Settings**: Type-safe configuration management
- **ThreadPoolExecutor**: Non-blocking model inference

### Audio Processing Pipeline

1. **Format Detection & Conversion**
   - Supports: WAV, MP3, WebM, FLAC, M4A, OGG, AAC, etc.
   - Automatic conversion to WAV via librosa + ffmpeg

2. **Preprocessing**
   - Convert to mono
   - Resample to 16kHz (kaiser_fast)
   - Trim silence (configurable threshold)
   - Spectral noise reduction
   - Adaptive loudness normalization (-23 LUFS)

3. **Transcription**
   - CTranslate2: Batched inference with VAD
   - HuggingFace: Smart chunking with word-level timestamps

4. **Post-processing**
   - Smart segment grouping
   - Timestamp extraction
   - Metadata collection

---

## Performance

### Benchmarks

**CTranslate2 Mode (GPU - RTX 4090):**
- 30s audio: ~0.6s processing time (Real-Time Factor: 0.02)
- Throughput: 30+ concurrent requests
- VRAM: ~2GB

**HuggingFace Mode (GPU - RTX 4090):**
- 30s audio: ~2.5s processing time (Real-Time Factor: 0.08)
- Throughput: 8-16 concurrent requests
- VRAM: ~4GB

**CPU Mode (Intel i7):**
- 30s audio: ~15s processing time (int8 quantization)
- Throughput: 2-4 concurrent requests

### Optimization Tips

1. **Use CTranslate2 format** for 4x speed improvement
2. **Enable VAD filter** to skip silence
3. **Adjust batch size** based on GPU memory
4. **Use int8 quantization** on CPU for speed
5. **Use bfloat16** on Ampere+ GPUs for best accuracy

---

## Supported Audio Formats

Thanks to librosa + ffmpeg backend:

✅ WAV, MP3, FLAC, OGG, M4A, AAC, WebM, Opus, WMA, etc.

**Automatic conversion:** Service automatically converts unsupported formats to WAV before processing.

**Browser recording:** Works seamlessly with WebM from browser MediaRecorder API.

---

## Requirements

### System Requirements

- **Python**: 3.11+
- **PyTorch**: 2.7.0+
- **CUDA**: 12.8 (for GPU)
- **ffmpeg**: For multi-format audio support
- **GPU**: NVIDIA GPU with 4GB+ VRAM (optional but recommended)

### Python Dependencies

```
fastapi
uvicorn[standard]
librosa
numpy
soundfile
python-dotenv
python-multipart
resampy
pydantic-settings
faster-whisper>=1.0.0
torch>=2.7.0
ctranslate2>=4.5.0
transformers>=4.30.0
```

---

## API Documentation

Once the service is running, visit:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Interactive API documentation with request/response examples and Try-it-out functionality.

---

## Monitoring & Logging

### Health Checks

```bash
# Docker health check (automatic)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3

# Manual check
curl http://localhost:8000/
```

### Logs

```bash
# Docker logs
docker-compose logs -f whisper-gpu

# Log levels
LOG_LEVEL=DEBUG   # Detailed debugging
LOG_LEVEL=INFO    # Service events (default)
LOG_LEVEL=WARNING # Warnings only
LOG_LEVEL=ERROR   # Errors only
```

### Log Rotation

Automatic log rotation configured in docker-compose:
- Max size: 10MB per file
- Max files: 3
- Total: 30MB per container

---

## Troubleshooting

### Issue: Model not loaded

**Cause:** Model path incorrect or format incompatible

**Solution:**
```bash
# Check model exists
ls /data/models/203-final

# Verify format
ls /data/models/203-final/
# CTranslate2: model.bin, config.json, vocabulary.txt
# HuggingFace: pytorch_model.bin, config.json, tokenizer_config.json

# Check logs
docker-compose logs whisper-gpu | grep -i "model"
```

### Issue: CUDA out of memory

**Cause:** Batch size too large for GPU

**Solution:**
```env
# Reduce batch size
BATCH_SIZE=4

# Use quantization
COMPUTE_TYPE=int8_float16

# Or switch to CPU
docker-compose --profile cpu up -d
```

### Issue: Slow transcription

**Solution:**
1. Verify GPU is being used: Check logs for "cuda"
2. Convert model to CTranslate2 format (4x speed)
3. Adjust batch size and workers for your hardware

### Issue: Unsupported audio format

**Solution:** Already handled! Service automatically converts via librosa + ffmpeg.

Ensure ffmpeg is installed:
```bash
# In Docker: Already included
# Local: sudo apt-get install ffmpeg
```

---

## Development

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
nano .env  # Edit configuration

# Run with auto-reload
uvicorn faster-whisper-service:app --reload --host 0.0.0.0 --port 8000
```

### Docker Development

```bash
# Run with live reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Edit code locally
# Changes auto-reload in container
```

### Testing

```bash
# Test health endpoint
curl http://localhost:8000/

# Test transcription
curl -X POST http://localhost:8000/transcribe/ \
  -F "file=@test.wav" \
  -F "language=fa"

# Test streaming
curl -X POST http://localhost:8000/transcribe/stream/ \
  -F "file=@test.wav" \
  -F "language=fa" \
  --no-buffer

# Test multi-format
curl -X POST http://localhost:8000/transcribe/ \
  -F "file=@test.webm" \
  -F "language=en"
```

---

## Project Structure

```
whisper-service/
├── faster-whisper-service.py    # Main FastAPI application (931 lines)
├── config.py                     # Pydantic settings (98 lines)
├── requirements.txt              # Python dependencies
├── .env.example                  # Example environment variables
├── Dockerfile                    # Production Docker image
├── docker-compose.yml            # Production orchestration (3 profiles)
├── docker-compose.dev.yml        # Development configuration
├── .dockerignore                 # Docker build exclusions
├── .gitignore                    # Git exclusions
├── README.md                     # This file
└── CLAUDE.md                     # Technical documentation
```

---

## License

MIT License - See LICENSE file for details.

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Update documentation
5. Submit a pull request

For bug reports and feature requests, please open an issue on GitHub.

---

## Credits

Built with:
- [Faster Whisper](https://github.com/SYSTRAN/faster-whisper) - CTranslate2 implementation
- [OpenAI Whisper](https://github.com/openai/whisper) - Original Whisper model
- [CTranslate2](https://github.com/OpenNMT/CTranslate2) - Fast inference engine
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Librosa](https://librosa.org/) - Audio processing
- [PyTorch](https://pytorch.org/) - Deep learning framework

---

## Support

For questions, issues, or contributions:
- 📖 Check [CLAUDE.md](CLAUDE.md) for technical documentation
- 🐛 Open an issue on GitHub
- 📧 Contact maintainers

---

**Version:** 2.0.0
**Last Updated:** 2025-10-19
**Status:** Production Ready ✅
