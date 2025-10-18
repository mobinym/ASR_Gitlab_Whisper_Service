# Quick Setup Guide for Faster Whisper Service

## Problem: "Transcription service unavailable. Model not loaded."

This happens when:
1. Dependencies are not installed
2. Model path doesn't exist
3. Wrong configuration for CPU/GPU

## Solution

### Step 1: Install Dependencies

Run the installation script:

```bash
# Windows
install.bat

# Linux/Mac
pip install -r requirements.txt
```

### Step 2: Configure Your Model

You have **two options**:

#### Option A: Use HuggingFace Models (Recommended - Easy)

Edit `.env` and set:

```env
DEFAULT_MODEL_NAME=openai/whisper-base
# Or: openai/whisper-small, openai/whisper-medium, openai/whisper-large-v3

MODELS_BASE_DIR=/data/models  # This can stay, it's only for local models
```

The model will be **automatically downloaded** on first run from HuggingFace.

**Available models:**
- `openai/whisper-tiny` - Fastest, lowest accuracy (39M params)
- `openai/whisper-base` - Good balance (74M params) ✅ Recommended for testing
- `openai/whisper-small` - Better accuracy (244M params)
- `openai/whisper-medium` - High accuracy (769M params)
- `openai/whisper-large-v3` - Best accuracy (1550M params)

#### Option B: Use Local Model

If you have a local model at `D:\data\models\203-final`:

1. Check if it's in the correct format (faster-whisper/CTranslate2 format)
2. Update `.env`:

```env
DEFAULT_MODEL_NAME=203-final
MODELS_BASE_DIR=D:/data/models
```

**Important:** If your model is in HuggingFace format (PyTorch), you need to convert it:

```bash
pip install ctranslate2
ct2-transformers-converter --model /path/to/pytorch/model --output_dir /data/models/203-final --quantization int8
```

### Step 3: Configure for CPU or GPU

#### For CPU (Current Configuration):

```env
DEVICE=cpu
COMPUTE_TYPE=int8
MAX_WORKERS=2
BATCH_SIZE=4
```

#### For GPU (CUDA):

```env
DEVICE=cuda
COMPUTE_TYPE=float16
MAX_WORKERS=4
BATCH_SIZE=16
```

### Step 4: Run the Service

```bash
python faster-whisper-service.py
```

You should see:

```
INFO - Loading model '...'
INFO - ✅ Model loaded successfully - Batch size: 16, Workers: 4
INFO - ✅ Service ready!
```

### Step 5: Test

```bash
curl -X POST http://localhost:8000/transcribe/ \
  -F "file=@0.wav" \
  -F "language=fa"
```

## Quick Start (Easiest Way)

1. Install dependencies:
   ```bash
   pip install fastapi uvicorn faster-whisper librosa soundfile numpy pydantic-settings python-multipart
   ```

2. Edit `.env`:
   ```env
   DEFAULT_MODEL_NAME=openai/whisper-base
   DEVICE=cpu
   COMPUTE_TYPE=int8
   ```

3. Run:
   ```bash
   python faster-whisper-service.py
   ```

4. Wait for model download (only happens once)

5. Test with your audio file!

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'librosa'"
**Solution:** Run `install.bat` or `pip install -r requirements.txt`

### Error: "Model directory not found"
**Solution:** Use HuggingFace model name instead: `openai/whisper-base`

### Error: "CUDA out of memory"
**Solution:** Reduce `BATCH_SIZE` to 4 or 8, or use CPU

### Error: "Unsupported compute type 'float16' for CPU"
**Solution:** Change `COMPUTE_TYPE=int8` in `.env`

### Slow transcription
- Use smaller model: `openai/whisper-base` or `openai/whisper-small`
- Reduce `BEAM_SIZE` to 1 or 3
- Enable `VAD_FILTER=true`

## Recommended Configurations

### Development/Testing (Fast):
```env
DEFAULT_MODEL_NAME=openai/whisper-base
DEVICE=cpu
COMPUTE_TYPE=int8
BATCH_SIZE=4
BEAM_SIZE=3
```

### Production (CPU, Balanced):
```env
DEFAULT_MODEL_NAME=openai/whisper-medium
DEVICE=cpu
COMPUTE_TYPE=int8
BATCH_SIZE=8
BEAM_SIZE=5
```

### Production (GPU, Maximum Performance):
```env
DEFAULT_MODEL_NAME=openai/whisper-large-v3
DEVICE=cuda
COMPUTE_TYPE=int8_float16
BATCH_SIZE=32
BEAM_SIZE=5
MAX_WORKERS=8
```

---

**Still having issues?** Check the service logs for detailed error messages.
