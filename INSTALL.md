# Quick Install Guide

## Step 1: Install Dependencies

Run this command:

```bash
pip install fastapi uvicorn[standard] faster-whisper librosa soundfile numpy pydantic-settings python-multipart python-dotenv
```

**Or** use the batch file (Windows):
```bash
install.bat
```

## Step 2: Configure the Service

Your `.env` file is already configured! It will:
- Download `whisper-base` model automatically (74MB, good for testing)
- Run on CPU with int8 precision
- Use 2 workers and batch size of 4

**To use your local model `203-final` instead:**

Edit `.env` and change:
```env
DEFAULT_MODEL_NAME=203-final
```

Make sure the model exists at: `D:\data\models\203-final\`

## Step 3: Run the Service

```bash
python faster-whisper-service.py
```

**First run will download the model** (this happens only once):
```
INFO - Starting Faster Whisper Service...
INFO - Loading default model: openai/whisper-base
INFO - Downloading model... (this may take a few minutes)
INFO - ✅ Model loaded successfully
INFO - ✅ Service ready!
```

## Step 4: Test It

Open a new terminal and run:

```bash
curl -X POST http://localhost:8000/transcribe/ -F "file=@0.wav" -F "language=fa"
```

You should get a JSON response with your transcription!

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'X'"
Run step 1 again to install all dependencies.

### Model taking too long / using too much RAM
Use a smaller model in `.env`:
```env
DEFAULT_MODEL_NAME=openai/whisper-tiny
```

### Want to use GPU instead?
Edit `.env`:
```env
DEVICE=cuda
COMPUTE_TYPE=float16
BATCH_SIZE=16
```

Then install CUDA PyTorch:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

## What's Next?

- Check [README-FASTER-WHISPER.md](README-FASTER-WHISPER.md) for full documentation
- See [SETUP-GUIDE.md](SETUP-GUIDE.md) for advanced configuration
- Visit `http://localhost:8000/docs` for interactive API documentation

---

**Ready to use!** The service will automatically handle:
- Chunking long audio files
- Noise reduction and preprocessing
- Voice activity detection
- Concurrent requests
