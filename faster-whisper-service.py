import os
import asyncio
import tempfile
import librosa
import numpy as np
import soundfile as sf
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from faster_whisper import WhisperModel, BatchedInferencePipeline
from typing import List, Optional, Dict, Any
import logging
from pydantic import BaseModel, Field
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import torch

# Import settings from config module
from config import settings

# Create models directory if it doesn't exist
os.makedirs(settings.models_base_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Try importing transformers for HuggingFace model support
try:
    from transformers import WhisperProcessor, WhisperForConditionalGeneration, pipeline as hf_pipeline
    TRANSFORMERS_AVAILABLE = True
    logger.info("Transformers library available - supporting both CTranslate2 and HuggingFace models")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers library not available - only CTranslate2 models supported")


class TranscriptionRequest(BaseModel):
    language: Optional[str] = Field(default="fa", description="Language code (e.g., 'fa', 'en')")
    task: Optional[str] = Field(default="transcribe", description="Task: 'transcribe' or 'translate'")
    beam_size: Optional[int] = Field(default=None, description="Beam size for decoding")
    vad_filter: Optional[bool] = Field(default=None, description="Enable Voice Activity Detection")
    word_timestamps: Optional[bool] = Field(default=False, description="Return word-level timestamps")
    chunk_length: Optional[int] = Field(default=30, description="Chunk length in seconds")


class TranscriptionResponse(BaseModel):
    transcription: str
    segments: Optional[List[Dict[str, Any]]] = None
    language: str
    duration: float
    processing_time: float
    model_used: str
    chunks_processed: int


class AudioPreprocessor:
    """Advanced audio preprocessing for better transcription quality."""

    def __init__(self, target_sr=16000, trim_top_db=25, normalization_target_db=-23.0):
        self.target_sr = target_sr
        self.trim_top_db = trim_top_db
        self.normalization_target_db = normalization_target_db
        logger.info("AudioPreprocessor initialized")

    def advanced_trim_silence(self, audio: np.ndarray) -> np.ndarray:
        if audio.size == 0:
            return audio
        try:
            trimmed, _ = librosa.effects.trim(
                audio,
                top_db=self.trim_top_db,
                frame_length=2048,
                hop_length=512
            )
            return trimmed
        except Exception as e:
            logger.warning(f"Trim silence failed: {e}")
            return audio

    def spectral_noise_reduction(self, audio: np.ndarray) -> np.ndarray:
        if audio.size == 0:
            return audio
        try:
            D = librosa.stft(audio, n_fft=2048, hop_length=512)
            magnitude, phase = np.abs(D), np.angle(D)
            energy = np.mean(magnitude, axis=0)
            noise_profile = np.mean(
                magnitude[:, energy < np.percentile(energy, 15)],
                axis=1,
                keepdims=True
            )
            if np.any(noise_profile) and not np.isnan(noise_profile).all():
                magnitude_clean = np.maximum(magnitude - 1.5 * noise_profile, 0)
                audio_clean = librosa.istft(
                    magnitude_clean * np.exp(1j * phase),
                    length=len(audio),
                    hop_length=512
                )
                return audio_clean.astype(np.float32)
            return audio
        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}")
            return audio

    def adaptive_normalization(self, audio: np.ndarray) -> np.ndarray:
        if audio.size == 0:
            return audio
        try:
            rms = np.sqrt(np.mean(audio.astype(np.float64)**2))
            if rms < 1e-7:
                return audio
            peak = np.max(np.abs(audio))
            if peak == 0:
                return audio
            target_rms = 10**(self.normalization_target_db / 20)
            rms_gain = target_rms / rms
            peak_gain = 0.95 / peak
            final_gain = min(rms_gain, peak_gain, 10.0)
            return (audio * final_gain).astype(np.float32)
        except Exception as e:
            logger.warning(f"Normalization failed: {e}")
            return audio

    def process(self, audio_array: np.ndarray, original_sr: int) -> np.ndarray:
        """Full preprocessing pipeline."""
        # Convert to mono if needed
        if len(audio_array.shape) > 1:
            if audio_array.shape[0] < audio_array.shape[1]:
                audio_array = audio_array.T
            audio_array = librosa.to_mono(audio_array.T)
            logger.debug("Converted to mono")

        # Resample if needed
        if original_sr != self.target_sr:
            audio_array = librosa.resample(
                y=audio_array,
                orig_sr=original_sr,
                target_sr=self.target_sr,
                res_type='kaiser_fast'
            )
            logger.debug(f"Resampled from {original_sr}Hz to {self.target_sr}Hz")

        # Apply preprocessing
        trimmed = self.advanced_trim_silence(audio_array)
        denoised = self.spectral_noise_reduction(trimmed)
        normalized = self.adaptive_normalization(denoised)

        return normalized.astype(np.float32)


class WhisperTranscriptionService:
    """High-throughput Whisper transcription service supporting both Faster Whisper and HuggingFace models."""

    def __init__(
        self,
        model_name: str,
        device: str = None,
        compute_type: str = None,
        batch_size: int = None
    ):
        self.model_name = model_name
        self.device = device or settings.device
        self.compute_type = compute_type or settings.compute_type
        self.batch_size = batch_size or settings.batch_size
        self.model = None
        self.batched_model = None
        self.hf_pipeline = None  # HuggingFace pipeline fallback
        self.hf_model = None  # HuggingFace model
        self.hf_processor = None  # HuggingFace processor
        self.hf_device = None  # Device for HuggingFace
        self.hf_torch_dtype = None  # Dtype for HuggingFace
        self.model_type = None  # 'ctranslate2' or 'huggingface'
        self.preprocessor = AudioPreprocessor(
            target_sr=settings.target_sample_rate,
            trim_top_db=settings.trim_top_db,
            normalization_target_db=settings.normalization_target_db
        )
        self.executor = ThreadPoolExecutor(max_workers=settings.max_workers)
        self.load_model()

    def load_model(self):
        """Load model - tries CTranslate2 first, falls back to HuggingFace format."""
        model_path = os.path.join(settings.models_base_dir, self.model_name)

        # Check if local path exists
        if not os.path.isdir(model_path):
            logger.warning(f"Local model not found at {model_path}")
            model_path = self.model_name  # Try as HuggingFace model ID

        # Try loading as CTranslate2 model (Faster Whisper)
        try:
            logger.info(f"Attempting to load CTranslate2 model '{model_path}'...")
            self.model = WhisperModel(
                model_path,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=os.cpu_count() if self.device == "cpu" else 0,
                num_workers=settings.max_workers
            )

            # Create batched inference pipeline
            # Note: API changed in faster-whisper >= 1.0.0
            try:
                # Try new API (no batch_size parameter)
                self.batched_model = BatchedInferencePipeline(model=self.model)
                logger.debug("Using BatchedInferencePipeline without batch_size (new API)")
            except TypeError:
                # Fallback to old API
                self.batched_model = BatchedInferencePipeline(
                    model=self.model,
                    batch_size=self.batch_size
                )
                logger.debug(f"Using BatchedInferencePipeline with batch_size={self.batch_size} (old API)")

            self.model_type = 'ctranslate2'
            logger.info(f"✅ CTranslate2 model loaded - Batch size: {self.batch_size}, Workers: {settings.max_workers}")
            return

        except Exception as e:
            logger.warning(f"Failed to load as CTranslate2 model: {e}")

        # Fallback to HuggingFace format if transformers is available
        if TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Attempting to load HuggingFace model '{model_path}'...")

                # Use local path for local models
                if os.path.isdir(model_path):
                    load_path = model_path
                else:
                    load_path = os.path.join(settings.models_base_dir, self.model_name)

                if not os.path.isdir(load_path):
                    raise FileNotFoundError(f"Model directory not found: {load_path}")

                # Determine device and dtype
                device = "cuda" if self.device == "cuda" and torch.cuda.is_available() else "cpu"
                torch_dtype = torch.float16 if device == "cuda" else torch.float32

                logger.info(f"Loading HuggingFace model on {device} with {torch_dtype}")

                # Load processor and model with memory optimization
                processor = WhisperProcessor.from_pretrained(load_path)
                model = WhisperForConditionalGeneration.from_pretrained(
                    load_path,
                    torch_dtype=torch_dtype,
                    low_cpu_mem_usage=True,  # Reduce memory footprint during loading
                )
                model.to(device)
                model.eval()

                # Disable gradient computation to save memory
                for param in model.parameters():
                    param.requires_grad = False

                # Clear CUDA cache if using GPU
                if device == "cuda":
                    torch.cuda.empty_cache()
                    logger.info(f"CUDA memory allocated: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")

                # Store model components for dynamic pipeline creation
                self.hf_model = model
                self.hf_processor = processor
                self.hf_device = device
                self.hf_torch_dtype = torch_dtype

                # Create initial HuggingFace pipeline (default chunk_length)
                self.hf_pipeline = hf_pipeline(
                    "automatic-speech-recognition",
                    model=model,
                    tokenizer=processor.tokenizer,
                    feature_extractor=processor.feature_extractor,
                    device=device,
                    torch_dtype=torch_dtype,
                    chunk_length_s=30,  # Default value
                    stride_length_s=5,
                    return_timestamps="word",  # Changed to "word" for chunking support
                )

                self.model_type = 'huggingface'
                logger.info(f"✅ HuggingFace model loaded successfully on {device}")
                return

            except Exception as e:
                logger.error(f"Failed to load as HuggingFace model: {e}")
                raise RuntimeError(f"Failed to load model in both CTranslate2 and HuggingFace formats") from e
        else:
            raise RuntimeError(f"Failed to load CTranslate2 model and transformers library not available for fallback")

    def _convert_audio_to_wav(self, input_path: str) -> str:
        """Convert audio file to WAV format using librosa (handles webm, mp3, etc.)"""
        try:
            # Try loading with librosa (supports many formats via ffmpeg)
            audio, sr = librosa.load(input_path, sr=None, mono=False)

            # Create temp WAV file
            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_wav.close()

            # Save as WAV
            sf.write(temp_wav.name, audio.T if len(audio.shape) > 1 else audio, sr)

            logger.info(f"Converted {input_path} to WAV format")
            return temp_wav.name

        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            raise

    async def transcribe(
        self,
        audio_path: str,
        language: str = "fa",
        task: str = "transcribe",
        beam_size: int = None,
        vad_filter: bool = None,
        word_timestamps: bool = False,
        chunk_length: int = 30
    ) -> Dict[str, Any]:
        """Transcribe audio file with chunking support."""

        start_time = datetime.now()

        # Use settings defaults if not provided
        beam_size = beam_size if beam_size is not None else settings.beam_size
        vad_filter = vad_filter if vad_filter is not None else settings.vad_filter

        # Convert to WAV if needed (for WebM, MP3, etc.)
        converted_path = None
        try:
            # Try reading directly first
            audio, sr = sf.read(audio_path)
        except Exception as e:
            logger.warning(f"Failed to read {audio_path} directly, converting to WAV: {e}")
            converted_path = self._convert_audio_to_wav(audio_path)
            audio, sr = sf.read(converted_path)

        try:
            processed_audio = self.preprocessor.process(audio, original_sr=sr)
            duration = len(processed_audio) / settings.target_sample_rate

            logger.info(f"Transcribing {duration:.2f}s audio with {self.model_type} model")

            # Use appropriate transcription method based on model type
            if self.model_type == 'ctranslate2':
                result = await self._transcribe_ctranslate2(
                    processed_audio, language, task, beam_size, vad_filter, word_timestamps
                )
            elif self.model_type == 'huggingface':
                result = await self._transcribe_huggingface(
                    processed_audio, language, task, beam_size, chunk_length
                )
            else:
                raise RuntimeError("No model loaded")

            result["duration"] = duration
            result["processing_time"] = (datetime.now() - start_time).total_seconds()
            result["model_used"] = self.model_name
            result["model_type"] = self.model_type

            logger.info(f"✅ Transcription completed in {result['processing_time']:.2f}s")

            return result

        finally:
            # Cleanup converted file
            if converted_path and os.path.exists(converted_path):
                try:
                    os.unlink(converted_path)
                except:
                    pass

    async def _transcribe_ctranslate2(
        self,
        audio: np.ndarray,
        language: str,
        task: str,
        beam_size: int,
        vad_filter: bool,
        word_timestamps: bool
    ) -> Dict[str, Any]:
        """Transcribe using CTranslate2 (Faster Whisper) model."""

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        segments, info = await loop.run_in_executor(
            self.executor,
            self._transcribe_sync_ctranslate2,
            audio,
            language,
            task,
            beam_size,
            vad_filter,
            word_timestamps
        )

        # Collect segments
        segments_list = []
        full_text = []

        for segment in segments:
            segment_dict = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            }

            if word_timestamps and hasattr(segment, 'words'):
                segment_dict["words"] = [
                    {
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "probability": word.probability
                    }
                    for word in segment.words
                ]

            segments_list.append(segment_dict)
            full_text.append(segment.text)

        transcription = " ".join(full_text).strip()

        return {
            "transcription": transcription,
            "segments": segments_list,
            "language": info.language if hasattr(info, 'language') else language,
            "chunks_processed": len(segments_list)
        }

    async def _transcribe_huggingface(
        self,
        audio: np.ndarray,
        language: str,
        task: str,
        beam_size: int,
        chunk_length: int = 30
    ) -> Dict[str, Any]:
        """Transcribe using HuggingFace transformers model."""

        # Map language codes
        language_map = {"fa": "persian", "en": "english", "ar": "arabic"}
        lang = language_map.get(language, language)

        # Run in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self._transcribe_sync_huggingface,
            audio,
            lang,
            task,
            beam_size,
            chunk_length
        )

        transcription = result["text"].strip()

        # Extract segments if available
        segments_list = []
        audio_duration = len(audio) / settings.target_sample_rate

        # Debug: log the structure of the result
        logger.debug(f"Pipeline result keys: {result.keys()}")

        if "chunks" in result and result["chunks"]:
            chunks = result["chunks"]
            logger.info(f"Received {len(chunks)} chunks from pipeline")

            # For short audio (< chunk_length), combine all word-level chunks into one segment
            # For long audio, group chunks into meaningful segments
            if audio_duration < chunk_length and len(chunks) < 10:
                # Short audio: combine all chunks into one segment with proper timestamps
                first_ts = chunks[0].get("timestamp", [None, None])
                last_ts = chunks[-1].get("timestamp", [None, None])

                start_time = float(first_ts[0]) if first_ts[0] is not None else 0.0
                end_time = float(last_ts[1]) if last_ts[1] is not None else audio_duration

                segments_list = [{
                    "start": start_time,
                    "end": end_time,
                    "text": transcription
                }]
                logger.info(f"Short audio ({audio_duration:.1f}s): combined {len(chunks)} word-level chunks into 1 segment")
            else:
                # Long audio: group word-level chunks into sentence-level segments
                # Group by chunk_length intervals
                current_segment = {"text": "", "start": None, "end": None}

                for i, chunk in enumerate(chunks):
                    ts = chunk.get("timestamp", [None, None])
                    text = chunk.get("text", "")

                    if current_segment["start"] is None:
                        current_segment["start"] = float(ts[0]) if ts[0] is not None else 0.0

                    current_segment["text"] += text
                    current_segment["end"] = float(ts[1]) if ts[1] is not None else audio_duration

                    # Create a new segment every ~30 words or at the end
                    if (i + 1) % 30 == 0 or i == len(chunks) - 1:
                        if current_segment["text"].strip():
                            segments_list.append({
                                "start": current_segment["start"],
                                "end": current_segment["end"],
                                "text": current_segment["text"].strip()
                            })
                        current_segment = {"text": "", "start": None, "end": None}

                logger.info(f"Long audio ({audio_duration:.1f}s): grouped {len(chunks)} word-level chunks into {len(segments_list)} segments")

        # If no segments were created, create one for the full audio as fallback
        if not segments_list:
            logger.warning(f"No chunks in pipeline result, creating single segment for full audio")
            segments_list = [{
                "start": 0.0,
                "end": audio_duration,
                "text": transcription
            }]

        return {
            "transcription": transcription,
            "segments": segments_list,
            "language": language,
            "chunks_processed": len(segments_list)
        }

    def _transcribe_sync_ctranslate2(
        self,
        audio: np.ndarray,
        language: str,
        task: str,
        beam_size: int,
        vad_filter: bool,
        word_timestamps: bool
    ):
        """Synchronous CTranslate2 transcription using batched pipeline."""
        initial_prompt = "این یک متن فارسی است." if language == "fa" else None
        initial_prompt = None
        segments, info = self.batched_model.transcribe(
            audio,
            language=language,
            task=task,
            beam_size=beam_size,
            vad_filter=vad_filter,
            word_timestamps=word_timestamps,
            condition_on_previous_text=True, # تغییر به False
            temperature=0.0,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6,
            initial_prompt=initial_prompt,
                    # پارامترهای اضافی اگر پشتیبانی می‌شوند:
            # repetition_penalty=1.1,  # جلوگیری از تکرار
            # no_repeat_ngram_size=3,  # عدم تکرار 3-gram
            # patience=1.5,  # بهبود کیفیت
            # length_penalty=0.6
        )

        return segments, info

    def _transcribe_sync_huggingface(
        self,
        audio: np.ndarray,
        language: str,
        task: str,
        beam_size: int,
        chunk_length: int = 30
    ):
        """Synchronous HuggingFace transcription with dynamic chunk_length."""

        # Create a pipeline with the specified chunk_length if different from default
        # This avoids reloading the model
        if chunk_length != 30 and hasattr(self, 'hf_model'):
            logger.info(f"Using custom chunk_length: {chunk_length}s")
            pipeline = hf_pipeline(
                "automatic-speech-recognition",
                model=self.hf_model,
                tokenizer=self.hf_processor.tokenizer,
                feature_extractor=self.hf_processor.feature_extractor,
                device=self.hf_device,
                torch_dtype=self.hf_torch_dtype,
                chunk_length_s=chunk_length,
                stride_length_s=min(5, chunk_length // 4),  # Adaptive stride
                return_timestamps="word",  # Use "word" for chunking support
            )
        else:
            pipeline = self.hf_pipeline

        result = pipeline(
            audio,
            generate_kwargs={
                "language": language,
                "task": task,
                "num_beams": beam_size,
            },
            return_timestamps="word"  # Use "word" to get chunks
        )

        return result

    async def transcribe_streaming(
        self,
        audio_path: str,
        language: str = "fa",
        task: str = "transcribe",
        beam_size: int = None,
        vad_filter: bool = None
    ):
        """Stream transcription results as they are generated."""

        # Use settings defaults if not provided
        beam_size = beam_size if beam_size is not None else settings.beam_size
        vad_filter = vad_filter if vad_filter is not None else settings.vad_filter

        # Convert to WAV if needed
        converted_path = None
        try:
            audio, sr = sf.read(audio_path)
        except Exception as e:
            logger.warning(f"Failed to read {audio_path} directly, converting to WAV: {e}")
            converted_path = self._convert_audio_to_wav(audio_path)
            audio, sr = sf.read(converted_path)

        try:
            processed_audio = self.preprocessor.process(audio, original_sr=sr)

            # Only CTranslate2 supports true streaming
            if self.model_type == 'ctranslate2':
                loop = asyncio.get_event_loop()
                segments, _ = await loop.run_in_executor(
                    self.executor,
                    self._transcribe_sync_ctranslate2,
                    processed_audio,
                    language,
                    task,
                    beam_size,
                    vad_filter,
                    False
                )

                # Stream segments as JSON
                for segment in segments:
                    yield json.dumps({
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text
                    }) + "\n"

            elif self.model_type == 'huggingface':
                # HuggingFace doesn't stream, return all at once
                lang_map = {"fa": "persian", "en": "english", "ar": "arabic"}
                lang = lang_map.get(language, language)

                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor,
                    self._transcribe_sync_huggingface,
                    processed_audio,
                    lang,
                    task,
                    beam_size,
                    30  # chunk_length default
                )

                # Return as single chunk
                yield json.dumps({
                    "start": 0.0,
                    "end": len(processed_audio) / settings.target_sample_rate,
                    "text": result["text"].strip()
                }) + "\n"

        finally:
            # Cleanup converted file
            if converted_path and os.path.exists(converted_path):
                try:
                    os.unlink(converted_path)
                except:
                    pass


# Application state
app_state = {
    "service": None,
    "available_models": [],
    "current_model_name": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting Faster Whisper Service...")

    # Discover available models
    if os.path.isdir(settings.models_base_dir):
        app_state["available_models"] = [
            d for d in os.listdir(settings.models_base_dir)
            if os.path.isdir(os.path.join(settings.models_base_dir, d))
        ]

    logger.info(f"Available models: {app_state['available_models']}")

    # Load default model
    default_model = settings.default_model_name

    try:
        logger.info(f"Loading default model: {default_model}")
        app_state["service"] = WhisperTranscriptionService(
            model_name=default_model,
            device=settings.device,
            compute_type=settings.compute_type,
            batch_size=settings.batch_size
        )
        app_state["current_model_name"] = default_model
        logger.info("✅ Service ready!")

    except Exception as e:
        logger.error(f"Failed to load default model: {e}")
        app_state["service"] = None

    yield

    # Shutdown
    logger.info("Shutting down...")
    if app_state["service"]:
        app_state["service"].executor.shutdown(wait=True)
    logger.info("Shutdown complete")


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


@app.get("/", summary="Health check")
def health_check():
    """Service health check."""
    return {
        "status": "ok",
        "service": "faster-whisper",
        "version": "2.0.0",
        "model": app_state["current_model_name"],
        "device": settings.device,
        "compute_type": settings.compute_type,
        "batch_size": settings.batch_size,
        "max_workers": settings.max_workers
    }


@app.get("/models/", summary="List available models")
def get_models():
    """List all available models and current model."""
    return {
        "available_models": app_state["available_models"],
        "current_model": app_state["current_model_name"],
        "device": settings.device,
        "compute_type": settings.compute_type
    }


@app.post("/transcribe/", response_model=TranscriptionResponse, summary="Transcribe audio file")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = "fa",
    task: str = "transcribe",
    beam_size: int = None,
    vad_filter: bool = None,
    word_timestamps: bool = False,
    chunk_length: int = 30
):
    """
    Transcribe an audio file using Faster Whisper with batched processing.

    - **file**: Audio file (wav, mp3, m4a, flac, etc.)
    - **language**: Language code (e.g., 'fa', 'en', 'ar')
    - **task**: 'transcribe' or 'translate'
    - **beam_size**: Beam size for decoding (higher = better quality, slower)
    - **vad_filter**: Enable Voice Activity Detection filtering
    - **word_timestamps**: Return word-level timestamps
    - **chunk_length**: Chunk length in seconds
    """

    service = app_state.get("service")
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Transcription service unavailable. Model not loaded."
        )

    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an audio file."
        )

    temp_file_path = None

    try:
        # Save uploaded file
        suffix = os.path.splitext(file.filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        logger.info(f"Processing file: {file.filename} ({len(content)} bytes)")

        # Transcribe
        result = await service.transcribe(
            audio_path=temp_file_path,
            language=language,
            task=task,
            beam_size=beam_size,
            vad_filter=vad_filter,
            word_timestamps=word_timestamps,
            chunk_length=chunk_length
        )

        return result

    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio: {str(e)}"
        )

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


@app.post("/transcribe/stream/", summary="Stream transcription results")
async def transcribe_audio_stream(
    file: UploadFile = File(...),
    language: str = "fa",
    task: str = "transcribe",
    beam_size: int = None,
    vad_filter: bool = None
):
    """
    Stream transcription results as they are generated (NDJSON format).
    Each line is a JSON object with segment information.
    """

    service = app_state.get("service")
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Transcription service unavailable."
        )

    temp_file_path = None

    try:
        suffix = os.path.splitext(file.filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        async def generate():
            try:
                async for chunk in service.transcribe_streaming(
                    audio_path=temp_file_path,
                    language=language,
                    task=task,
                    beam_size=beam_size,
                    vad_filter=vad_filter
                ):
                    yield chunk
            finally:
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass

        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson"
        )

    except Exception as e:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass

        logger.error(f"Streaming error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=True
    )
