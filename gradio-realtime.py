#!/usr/bin/env python3
"""
Real-time Live Transcription with Gradio
Simulates streaming by processing audio chunks as they arrive

Usage:
    pip install gradio requests soundfile numpy
    python gradio-realtime.py
"""

import gradio as gr
import requests
import tempfile
import soundfile as sf
import numpy as np
import time
import io
from pathlib import Path
from collections import deque


# API Configuration
API_URL = "http://localhost:16000/transcribe/"
STREAM_API_URL = "http://localhost:16000/transcribe/stream/"

# Streaming configuration
CHUNK_DURATION = 2  # seconds of audio per chunk
OVERLAP = 0.5  # seconds overlap between chunks


def split_audio_into_chunks(audio_data, sample_rate, chunk_duration=2, overlap=0.5):
    """
    Split audio into overlapping chunks for progressive transcription

    Args:
        audio_data: Audio samples (numpy array)
        sample_rate: Sample rate in Hz
        chunk_duration: Duration of each chunk in seconds
        overlap: Overlap duration in seconds

    Yields:
        Tuples of (chunk_audio, start_time, end_time)
    """
    chunk_samples = int(chunk_duration * sample_rate)
    overlap_samples = int(overlap * sample_rate)
    step = chunk_samples - overlap_samples

    for i in range(0, len(audio_data), step):
        chunk = audio_data[i:i + chunk_samples]

        # Skip if chunk is too small
        if len(chunk) < sample_rate * 0.5:  # At least 0.5 seconds
            continue

        start_time = i / sample_rate
        end_time = (i + len(chunk)) / sample_rate

        yield chunk, start_time, end_time


def transcribe_chunk(audio_chunk, sample_rate, language, beam_size=5):
    """
    Transcribe a single audio chunk

    Returns:
        Transcription text or empty string on error
    """
    try:
        # Save chunk to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            sf.write(f.name, audio_chunk, sample_rate)
            temp_path = f.name

        try:
            # Send to API
            with open(temp_path, 'rb') as audio_file:
                files = {'file': audio_file}
                data = {
                    'language': language,
                    'beam_size': beam_size,
                    'vad_filter': 'true'
                }

                response = requests.post(API_URL, files=files, data=data, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    return result.get('transcription', '').strip()
                else:
                    return ""

        finally:
            # Cleanup
            import os
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        print(f"Error transcribing chunk: {e}")
        return ""


def progressive_transcribe(audio, language="fa", beam_size=5, chunk_duration=2):
    """
    Transcribe audio progressively, simulating real-time streaming

    Args:
        audio: Tuple of (sample_rate, audio_data) from Gradio
        language: Language code
        beam_size: Beam size for decoding
        chunk_duration: Duration of each chunk

    Yields:
        Tuples of (cumulative_text, status_message, progress_value)
    """
    if audio is None:
        yield "لطفاً ابتدا صدا ضبط کنید", "❌ خطا: بدون ورودی", 0
        return

    sample_rate, audio_data = audio

    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)

    total_duration = len(audio_data) / sample_rate

    yield "", f"⏳ در حال پردازش {total_duration:.1f} ثانیه صدا...", 0

    # Split into chunks
    chunks = list(split_audio_into_chunks(
        audio_data,
        sample_rate,
        chunk_duration=chunk_duration,
        overlap=0.5
    ))

    transcriptions = []
    processed_chunks = 0
    total_chunks = len(chunks)

    for chunk_audio, start_time, end_time in chunks:
        # Transcribe chunk
        chunk_text = transcribe_chunk(chunk_audio, sample_rate, language, beam_size)

        if chunk_text:
            transcriptions.append(chunk_text)

        processed_chunks += 1
        progress = processed_chunks / total_chunks

        # Combine all transcriptions so far
        cumulative_text = ' '.join(transcriptions)

        # Status message
        status = (
            f"⏱️ پردازش chunk {processed_chunks}/{total_chunks}\n"
            f"🎯 زمان: {start_time:.1f}s - {end_time:.1f}s\n"
            f"📝 طول متن: {len(cumulative_text)} کاراکتر"
        )

        yield cumulative_text, status, progress

        # Small delay to simulate real-time
        time.sleep(0.1)

    # Final result
    final_text = ' '.join(transcriptions)
    final_status = (
        f"✅ تکمیل شد!\n"
        f"⏱️ مدت صدا: {total_duration:.1f}s\n"
        f"🔢 تعداد chunks: {total_chunks}\n"
        f"📝 طول نهایی: {len(final_text)} کاراکتر"
    )

    yield final_text, final_status, 1.0


def create_demo():
    """Create Gradio interface with progressive transcription"""

    with gr.Blocks(title="🎙️ Real-time Transcription", theme=gr.themes.Soft()) as demo:

        gr.Markdown("""
        # 🎙️ رونویسی زنده (شبیه‌سازی Real-time)

        این رابط صدای شما را به chunks کوچک تقسیم کرده و به صورت تدریجی رونویسی می‌کند.
        """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ تنظیمات")

                language = gr.Dropdown(
                    choices=[
                        ("فارسی", "fa"),
                        ("English", "en"),
                        ("العربية", "ar")
                    ],
                    value="fa",
                    label="زبان"
                )

                beam_size = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=5,
                    step=1,
                    label="Beam Size (دقت)",
                    info="بالاتر = دقیق‌تر اما کندتر"
                )

                chunk_duration = gr.Slider(
                    minimum=1,
                    maximum=5,
                    value=2,
                    step=0.5,
                    label="طول هر Chunk (ثانیه)",
                    info="کوچکتر = به‌روزرسانی سریعتر"
                )

                gr.Markdown("""
                ### 📝 راهنما:
                1. روی دکمه میکروفن کلیک کنید
                2. شروع به صحبت کنید (2-30 ثانیه)
                3. دوباره کلیک کنید تا ضبط متوقف شود
                4. روی "شروع رونویسی تدریجی" کلیک کنید
                5. متن به صورت تدریجی نمایش داده می‌شود

                **نکته:** هر chunk حدود {chunk_duration} ثانیه است
                """)

            with gr.Column(scale=2):
                gr.Markdown("### 🎤 ضبط صدا")

                audio_input = gr.Audio(
                    sources=["microphone"],
                    type="numpy",
                    label="میکروفن"
                )

                transcribe_btn = gr.Button(
                    "🚀 شروع رونویسی تدریجی",
                    variant="primary",
                    size="lg"
                )

                progress_bar = gr.Progress()

                gr.Markdown("### 📄 متن در حال رونویسی...")

                transcription_output = gr.Textbox(
                    label="نتیجه (Live Update)",
                    placeholder="متن به صورت تدریجی اینجا ظاهر می‌شود...",
                    lines=10,
                    interactive=False,
                    show_copy_button=True
                )

                status_output = gr.Textbox(
                    label="وضعیت",
                    lines=4,
                    interactive=False
                )

                progress_output = gr.Slider(
                    minimum=0,
                    maximum=1,
                    value=0,
                    label="پیشرفت",
                    interactive=False
                )

                with gr.Row():
                    clear_btn = gr.Button("🗑️ پاک کردن")

        # Event handlers
        def run_progressive_transcribe(audio, lang, beam, chunk_dur):
            """Wrapper to handle progress updates"""
            for text, status, progress in progressive_transcribe(
                audio, lang, beam, chunk_dur
            ):
                yield text, status, progress

        transcribe_btn.click(
            fn=run_progressive_transcribe,
            inputs=[audio_input, language, beam_size, chunk_duration],
            outputs=[transcription_output, status_output, progress_output]
        )

        clear_btn.click(
            fn=lambda: ("", "", 0),
            outputs=[transcription_output, status_output, progress_output]
        )

        # Examples
        gr.Markdown("""
        ---
        ### 💡 نکات بهینه‌سازی:

        - **Chunk Duration کوچک (1-2s)**: به‌روزرسانی سریع‌تر، اما دقت ممکن است کمتر باشد
        - **Chunk Duration بزرگ (3-5s)**: دقت بهتر، اما به‌روزرسانی کندتر
        - **Beam Size 5**: متعادل برای استفاده روزمره
        - **Beam Size 10**: برای دقت بالاتر در صداهای مهم

        ### ⚠️ محدودیت:
        این یک شبیه‌سازی client-side است. برای transcription واقعاً real-time (مثل Google Voice Typing)،
        نیاز به WebSocket و streaming واقعی audio chunks است.
        """)

    return demo


def main():
    """Main entry point"""

    print("="*60)
    print("🎙️  Progressive Real-time Transcription - Gradio Interface")
    print("="*60)
    print()

    # Check API
    try:
        response = requests.get("http://localhost:16000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Connected to API (Model: {data.get('model', 'unknown')})")
        else:
            print(f"⚠️  API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print()
        print("⚠️  Make sure the Whisper service is running:")
        print("   docker-compose up -d whisper-gpu")
        print()

    print()
    print("Starting Gradio interface...")
    print("This will open in your browser at http://localhost:7860")
    print()

    # Create and launch demo
    demo = create_demo()

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()
