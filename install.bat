@echo off
echo Installing Faster Whisper Service dependencies...
echo.

echo Step 1: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 2: Installing core dependencies...
pip install fastapi uvicorn[standard] python-dotenv python-multipart pydantic-settings

echo.
echo Step 3: Installing audio processing libraries...
pip install numpy soundfile librosa resampy

echo.
echo Step 4: Installing Faster Whisper and dependencies...
pip install faster-whisper

echo.
echo Step 5: Installing PyTorch (this may take a while)...
pip install torch --index-url https://download.pytorch.org/whl/cpu

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your configuration
echo 2. Run: python faster-whisper-service.py
echo.
pause
