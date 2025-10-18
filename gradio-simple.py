#!/usr/bin/env python3
"""
Simple Gradio Whisper Interface
Minimal example for microphone transcription

Usage:
    pip install gradio requests soundfile
    python gradio-simple.py
"""

import gradio as gr
import requests
import tempfile
import soundfile as sf


# API Configuration
API_URL = "http://localhost:16000/transcribe/"


def transcribe(audio, language="fa"):
    """Transcribe audio from microphone"""

    if audio is None:
        return "لطفاً ابتدا صدا ضبط کنید"

    sample_rate, audio_data = audio

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        sf.write(f.name, audio_data, sample_rate)

        # Send to API
        with open(f.name, 'rb') as audio_file:
            files = {'file': audio_file}
            data = {'language': language}

            try:
                response = requests.post(API_URL, files=files, data=data, timeout=300)

                if response.status_code == 200:
                    result = response.json()
                    return result['transcription']
                else:
                    return f"خطا: {response.status_code}"

            except Exception as e:
                return f"خطا: {str(e)}"


# Create interface
demo = gr.Interface(
    fn=transcribe,
    inputs=[
        gr.Audio(sources=["microphone"], type="numpy", label="🎤 میکروفن"),
        gr.Dropdown(
            choices=[("فارسی", "fa"), ("English", "en"), ("العربية", "ar")],
            value="fa",
            label="زبان"
        )
    ],
    outputs=gr.Textbox(label="📄 متن رونویسی شده", lines=5, show_copy_button=True),
    title="🎙️ رونویسی صوت با Whisper",
    description="ضبط صدا از میکروفن و تبدیل به متن",
    examples=None,
    theme=gr.themes.Soft()
)


if __name__ == "__main__":
    print("Starting Gradio interface at http://localhost:7860")
    demo.launch(server_name="0.0.0.0", server_port=7860)
