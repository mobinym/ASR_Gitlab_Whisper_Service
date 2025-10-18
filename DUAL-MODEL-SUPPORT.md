# Dual Model Format Support

The `faster-whisper-service.py` now supports **BOTH** model formats:

## Supported Formats

### 1. CTranslate2 Format (Faster Whisper)
- **Speed**: 4x faster than HuggingFace
- **Memory**: 50% less VRAM
- **Features**: Full batching, streaming, VAD
- **File**: Contains `model.bin` (CTranslate2 format)

### 2. HuggingFace/PyTorch Format
- **Compatibility**: Works with your existing `203-final` model
- **Features**: Standard chunking, good quality
- **Files**: Contains `pytorch_model.bin`, `config.json`, etc.

## How It Works

The service **automatically detects** the model format:

1. **First attempt**: Tries to load as CTranslate2 model
2. **Fallback**: If that fails, loads as HuggingFace model
3. **Adapts**: Uses the appropriate transcription method

```python
# Automatic detection
if model has 'model.bin':
    → Load with Faster Whisper (CTranslate2)
else if model has 'pytorch_model.bin':
    → Load with Transformers (HuggingFace)
```

## Your Setup

Your `203-final` model at `D:/data/models/203-final` will be loaded as **HuggingFace format**.

## Installation

```bash
# Install all dependencies (includes both)
pip install -r requirements.txt
```

This installs:
- `faster-whisper` - For CTranslate2 models
- `transformers` - For HuggingFace models (your 203-final)
- Both libraries work side-by-side

## Usage

No changes needed! Just use the same API:

```bash
curl -X POST http://localhost:8000/transcribe/ \
  -F "file=@audio.wav" \
  -F "language=fa"
```

The response will include `model_type`:

```json
{
  "transcription": "...",
  "model_type": "huggingface",  ← Shows which format was used
  "model_used": "203-final"
}
```

## Configuration

In `.env`:

```env
# Your existing HuggingFace model
DEFAULT_MODEL_NAME=203-final
MODELS_BASE_DIR=D:/data/models
```

## Convert to CTranslate2 (Optional)

To get 4x speedup, convert your model to CTranslate2:

```bash
pip install ctranslate2
ct2-transformers-converter \
  --model D:/data/models/203-final \
  --output_dir D:/data/models/203-final-ct2 \
  --quantization int8
```

Then update `.env`:
```env
DEFAULT_MODEL_NAME=203-final-ct2
```

## Features by Format

| Feature | CTranslate2 | HuggingFace |
|---------|-------------|-------------|
| Speed | 4x faster | 1x |
| Memory | 50% less | Standard |
| Batching | Full support | Limited |
| Streaming | Yes | No (simulated) |
| VAD Filter | Built-in | No |
| Your existing model | Need conversion | ✅ Works now |

## Logs

Watch the startup logs to see which format is loaded:

**CTranslate2:**
```
INFO - Attempting to load CTranslate2 model...
INFO - ✅ CTranslate2 model loaded
```

**HuggingFace:**
```
WARNING - Failed to load as CTranslate2 model
INFO - Attempting to load HuggingFace model...
INFO - ✅ HuggingFace model loaded successfully
```

## Recommendation

For your current setup:
1. **Now**: Use HuggingFace format (works immediately)
2. **Later**: Convert to CTranslate2 for 4x speed boost

Both formats work perfectly with the same API!
