#!/usr/bin/env python3
"""
Gradio Live Transcription App
Real-time speech-to-text using microphone input and Whisper streaming API

Features:
- Record from microphone
- Real-time transcription display
- Persian/English/Arabic language support
- Adjustable accuracy settings
- Export transcription

Usage:
    pip install gradio requests numpy soundfile
    python gradio-live-transcription.py
"""

import gradio as gr
import requests
import json
import tempfile
import os
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Optional, Tuple
import time


# Configuration
API_BASE_URL = "http://services.aiopt.io:16000"  # Change to your server
STREAM_ENDPOINT = f"{API_BASE_URL}/transcribe/stream/"
REGULAR_ENDPOINT = f"{API_BASE_URL}/transcribe/"


def check_api_health() -> Tuple[bool, str]:
    """بررسی در دسترس بودن API"""
    try:
        response = requests.get(API_BASE_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            model = data.get('model', 'unknown')
            return True, f"✅ Connected to API (Model: {model})"
        else:
            return False, f"❌ API returned status {response.status_code}"
    except Exception as e:
        return False, f"❌ Cannot connect to API: {str(e)}"


def transcribe_audio(
    audio_data: Optional[Tuple[int, np.ndarray]],
    language: str,
    use_streaming: bool,
    beam_size: int,
    vad_filter: bool
) -> Tuple[str, str]:
    """
    Transcribe audio using Whisper API

    Args:
        audio_data: Tuple of (sample_rate, audio_array) from Gradio microphone
        language: Language code
        use_streaming: Whether to use streaming endpoint
        beam_size: Beam size for decoding
        vad_filter: Enable VAD filter

    Returns:
        Tuple of (transcription_text, status_message)
    """

    if audio_data is None:
        return "", "⚠️ لطفاً ابتدا صدا ضبط کنید"

    sample_rate, audio_array = audio_data

    # Save audio to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_path = temp_file.name
    temp_file.close()

    try:
        # Write audio to file
        sf.write(temp_path, audio_array, sample_rate)

        # Calculate audio duration
        duration = len(audio_array) / sample_rate

        # Prepare request
        with open(temp_path, 'rb') as f:
            files = {'file': ('audio.wav', f, 'audio/wav')}
            data = {
                'language': language,
                'beam_size': beam_size,
                'vad_filter': 'true' if vad_filter else 'false'
            }

            start_time = time.time()

            if use_streaming:
                # Use streaming endpoint
                transcription = transcribe_streaming(files, data)
                elapsed = time.time() - start_time

                status = (f"✅ تکمیل شد (Streaming)\n"
                         f"⏱️ مدت زمان صدا: {duration:.1f}s\n"
                         f"⚡ زمان پردازش: {elapsed:.2f}s\n"
                         f"📊 RTF: {elapsed/duration:.2f}x")
            else:
                # Use regular endpoint
                response = requests.post(REGULAR_ENDPOINT, files=files, data=data, timeout=300)
                elapsed = time.time() - start_time

                if response.status_code == 200:
                    result = response.json()
                    transcription = result.get('transcription', '')

                    status = (f"✅ تکمیل شد (Regular)\n"
                             f"⏱️ مدت زمان صدا: {duration:.1f}s\n"
                             f"⚡ زمان پردازش: {elapsed:.2f}s\n"
                             f"📊 RTF: {elapsed/duration:.2f}x\n"
                             f"🔢 تعداد segments: {result.get('chunks_processed', 'N/A')}")
                else:
                    transcription = ""
                    status = f"❌ خطا: {response.status_code} - {response.text}"

        return transcription, status

    except requests.exceptions.Timeout:
        return "", "❌ خطا: زمان درخواست تمام شد"
    except requests.exceptions.RequestException as e:
        return "", f"❌ خطای شبکه: {str(e)}"
    except Exception as e:
        return "", f"❌ خطا: {str(e)}"
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass


def transcribe_streaming(files: dict, data: dict) -> str:
    """Transcribe using streaming endpoint and combine results"""

    # Reopen file for streaming request
    file_obj = files['file'][1]
    file_obj.seek(0)

    segments = []

    with requests.post(STREAM_ENDPOINT, files=files, data=data, stream=True, timeout=300) as response:
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    segment = json.loads(line.decode('utf-8'))
                    segments.append(segment)
                except json.JSONDecodeError:
                    pass

    # Combine all segments
    full_text = ' '.join(seg.get('text', '').strip() for seg in segments)
    return full_text


def create_demo():
    """Create Gradio interface"""

    # Check API health on startup
    api_ok, api_status = check_api_health()

    with gr.Blocks(title="🎙️ Whisper Live Transcription", theme=gr.themes.Soft()) as demo:

        gr.Markdown("""
        # 🎙️ رونویسی زنده با Whisper

        ضبط صدا از میکروفن و تبدیل به متن به صورت real-time
        """)

        # API Status
        with gr.Row():
            api_status_box = gr.Textbox(
                label="وضعیت API",
                value=api_status,
                interactive=False,
                lines=1
            )
            refresh_btn = gr.Button("🔄 بررسی مجدد", size="sm")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ تنظیمات")

                language = gr.Dropdown(
                    choices=[
                        ("فارسی", "fa"),
                        ("English", "en"),
                        ("العربية", "ar"),
                        ("Türkçe", "tr"),
                        ("Auto Detect", "auto")
                    ],
                    value="fa",
                    label="زبان",
                    interactive=True
                )

                use_streaming = gr.Checkbox(
                    label="استفاده از Streaming API (سریع‌تر)",
                    value=True
                )

                beam_size = gr.Slider(
                    minimum=1,
                    maximum=15,
                    value=5,
                    step=1,
                    label="Beam Size (دقت)",
                    info="بالاتر = دقیق‌تر اما کندتر"
                )

                vad_filter = gr.Checkbox(
                    label="فیلتر سکوت (VAD)",
                    value=True
                )

                gr.Markdown("""
                ### 📝 راهنما:
                1. روی دکمه میکروفن کلیک کنید
                2. شروع به صحبت کنید
                3. دوباره کلیک کنید تا ضبط متوقف شود
                4. روی "رونویسی" کلیک کنید

                **نکته:** برای بهترین نتیجه در محیط بدون سروصدا صحبت کنید
                """)

            with gr.Column(scale=2):
                gr.Markdown("### 🎤 ضبط صدا")

                audio_input = gr.Audio(
                    sources=["microphone"],
                    type="numpy",
                    label="میکروفن",
                    interactive=True
                )

                transcribe_btn = gr.Button(
                    "🚀 رونویسی",
                    variant="primary",
                    size="lg"
                )

                gr.Markdown("### 📄 متن رونویسی شده")

                transcription_output = gr.Textbox(
                    label="نتیجه",
                    placeholder="متن رونویسی شده اینجا نمایش داده می‌شود...",
                    lines=8,
                    interactive=True,
                    show_copy_button=True
                )

                status_output = gr.Textbox(
                    label="وضعیت",
                    interactive=False,
                    lines=5
                )

                with gr.Row():
                    clear_btn = gr.Button("🗑️ پاک کردن", size="sm")
                    export_btn = gr.Button("💾 ذخیره متن", size="sm")

                export_file = gr.File(label="فایل خروجی", visible=False)

        # Examples
        gr.Markdown("### 💡 نکات:")
        gr.Markdown("""
        - **Streaming API**: برای دریافت سریع‌تر نتایج (توصیه می‌شود)
        - **Regular API**: برای دریافت اطلاعات کامل‌تر (segments, timestamps, etc.)
        - **Beam Size 5**: متعادل بین سرعت و دقت
        - **Beam Size 10+**: دقت بیشتر برای صداهای پیچیده
        - **VAD Filter**: برای حذف خودکار قسمت‌های سکوت
        """)

        # Event handlers
        def refresh_api_status():
            ok, msg = check_api_health()
            return msg

        def export_text(text):
            if not text:
                return None

            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix='.txt',
                mode='w',
                encoding='utf-8'
            )
            temp_file.write(text)
            temp_file.close()

            return temp_file.name

        # Wire up events
        refresh_btn.click(
            fn=refresh_api_status,
            outputs=api_status_box
        )

        transcribe_btn.click(
            fn=transcribe_audio,
            inputs=[audio_input, language, use_streaming, beam_size, vad_filter],
            outputs=[transcription_output, status_output]
        )

        clear_btn.click(
            fn=lambda: ("", ""),
            outputs=[transcription_output, status_output]
        )

        export_btn.click(
            fn=export_text,
            inputs=transcription_output,
            outputs=export_file
        )

    return demo


def main():
    """Main entry point"""

    print("="*60)
    print("🎙️  Whisper Live Transcription - Gradio Interface")
    print("="*60)
    print()

    # Check API
    print("Checking API connection...")
    api_ok, api_msg = check_api_health()
    print(api_msg)

    if not api_ok:
        print()
        print("⚠️  WARNING: Cannot connect to API!")
        print(f"   Make sure the Whisper service is running at {API_BASE_URL}")
        print()
        print("   To start the service:")
        print("   docker-compose up -d whisper-gpu")
        print()
        response = input("Continue anyway? [y/N]: ")
        if response.lower() != 'y':
            return

    print()
    print("Starting Gradio interface...")
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
