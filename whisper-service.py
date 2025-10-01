import os
import tempfile
import librosa
import numpy as np
import soundfile as sf
import torch
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from transformers import WhisperProcessor, WhisperForConditionalGeneration, pipeline
from typing import List
import logging
from dotenv import load_dotenv

load_dotenv() 

MODELS_BASE_DIR = "/data/models"
TARGET_SR = 16000

os.makedirs(MODELS_BASE_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app_state = {
    "whisper_pipeline": None,  
    "audio_preprocessor": None,
    "available_models": [],
    "current_model_name": None
}

class AudioPreprocessor:
    def __init__(self, target_sr=16000, trim_top_db=25, normalization_target_db=-23.0):
        self.target_sr = target_sr
        self.trim_top_db = trim_top_db
        self.normalization_target_db = normalization_target_db
        logger.info("Advanced AudioPreprocessor initialized.")

    def advanced_trim_silence(self, audio: np.ndarray) -> np.ndarray:
        if audio.size == 0: return audio
        try:
            trimmed, _ = librosa.effects.trim(audio, top_db=self.trim_top_db, frame_length=1024, hop_length=256)
            return trimmed
        except Exception:
            return audio

    def spectral_noise_reduction(self, audio: np.ndarray) -> np.ndarray:
        if audio.size == 0: return audio
        try:
            D = librosa.stft(audio)
            magnitude, phase = np.abs(D), np.angle(D)
            energy = np.mean(magnitude, axis=0)
            noise_profile = np.mean(magnitude[:, energy < np.percentile(energy, 20)], axis=1, keepdims=True)
            if np.any(noise_profile) and not np.isnan(noise_profile).all():
                magnitude_clean = np.maximum(magnitude - 2.0 * noise_profile, 0)
                audio_clean = librosa.istft(magnitude_clean * np.exp(1j * phase), length=len(audio))
                return audio_clean.astype(np.float32)
            return audio
        except Exception:
            return audio

    def dynamic_range_compression(self, audio: np.ndarray) -> np.ndarray:
        if audio.size == 0: return audio
        try:
            threshold, ratio = 0.3, 3.0
            above_threshold_indices = np.where(np.abs(audio) > threshold)[0]
            if above_threshold_indices.size > 0:
                audio[above_threshold_indices] = np.sign(audio[above_threshold_indices]) * (threshold + (np.abs(audio[above_threshold_indices]) - threshold) / ratio)
            return audio
        except Exception:
            return audio

    def adaptive_normalization(self, audio: np.ndarray) -> np.ndarray:
        if audio.size == 0: return audio
        try:
            rms = np.sqrt(np.mean(audio.astype(np.float64)**2))
            if rms < 1e-7: return audio
            peak = np.max(np.abs(audio))
            if peak == 0: return audio
            target_rms = 10**(self.normalization_target_db / 20)
            rms_gain = target_rms / rms
            peak_gain = 0.98 / peak
            final_gain = min(rms_gain, peak_gain, 10.0)
            return (audio * final_gain).astype(np.float32)
        except Exception:
            return audio
    
    def process(self, audio_array: np.ndarray, original_sr: int) -> np.ndarray:
        """Runs the full preprocessing pipeline."""
        if len(audio_array.shape) > 1 and audio_array.shape[1] > 1:
            audio_array = librosa.to_mono(audio_array.T)
            logger.info("Converted stereo audio to mono.")

        if original_sr != self.target_sr:
            audio_array = librosa.resample(y=audio_array, orig_sr=original_sr, target_sr=self.target_sr, res_type='kaiser_best')
            logger.info(f"Resampled audio from {original_sr}Hz to {self.target_sr}Hz.")
        
        trimmed = self.advanced_trim_silence(audio_array)
        denoised = self.spectral_noise_reduction(trimmed)
        compressed = self.dynamic_range_compression(denoised)
        normalized = self.adaptive_normalization(compressed)
        
        logger.info("Advanced audio processing complete.")
        return normalized.astype(np.float32)


def load_transcription_model(model_name: str):
    """یک مدل مشخص را از پوشه آن بارگذاری می‌کند."""
    model_path = os.path.join(MODELS_BASE_DIR, model_name)
    if not os.path.isdir(model_path):
        raise FileNotFoundError(f"Model directory not found: {model_path}")

    logger.info(f"Loading model '{model_name}'...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if device == "cuda" else torch.float32

    processor = WhisperProcessor.from_pretrained(model_path)
    model = WhisperForConditionalGeneration.from_pretrained(model_path, torch_dtype=torch_dtype)
    model.to(device)
    model.eval()

    
    whisper_pipeline = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        device=device,
        torch_dtype=torch_dtype,
        chunk_length_s=20,  
        stride_length_s=5,
        return_timestamps=True,  
    )

    logger.info(f"✅ Model '{model_name}' loaded successfully with auto-chunking on device '{device}'.")
    
    return whisper_pipeline


app = FastAPI(
    title="🎙️ Farsi Speech-to-Text Service (Whisper Auto-Chunking Only)",
    description="سرویسی برای تبدیل گفتار به متن با chunking خودکار Whisper - فقط یک روش!",
    version="3.0.0"
)

@app.on_event("startup")
def startup_event():
    """این تابع در زمان شروع به کار سرور اجرا می‌شود و مدل را بر اساس فایل .env بارگذاری می‌کند."""
    app_state["available_models"] = [d for d in os.listdir(MODELS_BASE_DIR) if os.path.isdir(os.path.join(MODELS_BASE_DIR, d))]
    
    if not app_state["available_models"]:
        logger.warning(f"No models found in '{MODELS_BASE_DIR}' directory. The transcribe endpoint will not work.")
    else:
        logger.info(f"Available models found: {app_state['available_models']}")

    default_model_name = os.getenv("DEFAULT_MODEL_NAME")
    
    if default_model_name and default_model_name in app_state["available_models"]:
        try:
            logger.info(f"Attempting to load default model from .env: '{default_model_name}'")
            whisper_pipeline = load_transcription_model(default_model_name)
            app_state["whisper_pipeline"] = whisper_pipeline
            app_state["current_model_name"] = default_model_name
        except Exception as e:
            logger.error(f"❌ Failed to load the specified model '{default_model_name}': {e}")
            app_state["whisper_pipeline"] = None
            app_state["current_model_name"] = None
    elif default_model_name:
         logger.warning(f"Model '{default_model_name}' specified in .env not found in '{MODELS_BASE_DIR}'.")
    else:
        logger.warning("DEFAULT_MODEL_NAME not set in .env file. No model will be loaded at startup.")
    
    app_state["audio_preprocessor"] = AudioPreprocessor(target_sr=TARGET_SR)


@app.get("/models/", summary="دریافت لیست و وضعیت مدل‌ها")
def get_models():
    """لیستی از تمام مدل‌های موجود و نام مدل فعال فعلی را برمی‌گرداند."""
    return {
        "available_models": app_state["available_models"],
        "current_model": app_state["current_model_name"]
    }



def transcribe_audio(whisper_pipeline, audio_array: np.ndarray, sample_rate: int) -> str:
    """
    تبدیل صوت به متن با Whisper Auto-Chunking
    """
    duration = len(audio_array) / sample_rate
    logger.info(f"🎯 Transcribing {duration:.2f}s audio with Whisper auto-chunking")
    
    try:
        
        result = whisper_pipeline(
            audio_array,
            generate_kwargs={
                "language": "persian",
                "task": "transcribe",
                "num_beams": 5,
            }
        )
        
        transcription = result["text"].strip()
        logger.info("✅ Whisper auto-chunking completed successfully")
        return transcription
        
    except Exception as e:
        logger.error(f"❌ Whisper pipeline failed: {e}")
        raise


@app.post("/transcribe/", summary="تبدیل فایل صوتی به متن")
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """یک فایل صوتی را با استفاده از Whisper chunking خودکار به متن تبدیل می‌کند."""
    whisper_pipeline = app_state.get("whisper_pipeline")
    preprocessor = app_state.get("audio_preprocessor")

    if not whisper_pipeline:
        raise HTTPException(status_code=503, detail="Transcription service is unavailable. No model is loaded.")

    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")

    temp_file_path = None
    try:
        suffix = os.path.splitext(file.filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        audio, sr = sf.read(temp_file_path)
        processed_audio = preprocessor.process(audio, original_sr=sr)

       
        prediction = transcribe_audio(whisper_pipeline, processed_audio, TARGET_SR)
        
        return {
            "transcription": prediction, 
            "model_used": app_state["current_model_name"],
            "method": "whisper_auto_chunking"
        }

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing audio file: {str(e)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@app.get("/", include_in_schema=False)
def read_root():
    return {"status": "ok", "method": "whisper_auto_chunking", "version": "3.0.0"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
