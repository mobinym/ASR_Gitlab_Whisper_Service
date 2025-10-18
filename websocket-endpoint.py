"""
WebSocket endpoint for real-time audio streaming transcription
Add this to faster-whisper-service.py
"""

from fastapi import WebSocket, WebSocketDisconnect
import numpy as np
import io
import struct

@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio transcription.

    Protocol:
    1. Client connects
    2. Client sends JSON config: {"language": "fa", "beam_size": 5}
    3. Client sends audio chunks as binary data
    4. Server responds with JSON transcription segments
    5. Client sends empty message to signal end
    """

    await websocket.accept()
    service = app_state.get("service")

    if not service:
        await websocket.send_json({"error": "Service unavailable"})
        await websocket.close()
        return

    try:
        # Receive configuration
        config = await websocket.receive_json()
        language = config.get("language", "fa")
        beam_size = config.get("beam_size", 5)
        chunk_duration = config.get("chunk_duration", 3)  # seconds

        logger.info(f"WebSocket session started: lang={language}, beam={beam_size}")

        audio_buffer = []
        sample_rate = 16000
        chunk_samples = int(chunk_duration * sample_rate)

        while True:
            # Receive audio chunk
            try:
                message = await websocket.receive()

                # Check for text messages (control signals)
                if "text" in message:
                    text_data = message["text"]
                    if text_data == "END":
                        break
                    continue

                # Process binary audio data
                if "bytes" in message:
                    audio_data = message["bytes"]

                    # Convert bytes to numpy array (assuming int16 PCM)
                    audio_chunk = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                    audio_buffer.extend(audio_chunk)

                    # Process when we have enough audio
                    if len(audio_buffer) >= chunk_samples:
                        # Extract chunk
                        chunk_to_process = np.array(audio_buffer[:chunk_samples])
                        audio_buffer = audio_buffer[chunk_samples//2:]  # 50% overlap

                        # Transcribe chunk
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                        sf.write(temp_file.name, chunk_to_process, sample_rate)

                        try:
                            # Quick transcription
                            result = await service.transcribe(
                                audio_path=temp_file.name,
                                language=language,
                                beam_size=beam_size,
                                vad_filter=True
                            )

                            # Send result
                            await websocket.send_json({
                                "text": result["transcription"],
                                "duration": result["duration"],
                                "timestamp": time.time()
                            })

                        finally:
                            os.unlink(temp_file.name)

            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"error": str(e)})

    finally:
        try:
            await websocket.close()
        except:
            pass
