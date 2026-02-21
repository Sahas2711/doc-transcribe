"""
Speech-to-Text REST API using FastAPI and Whisper
Production-ready implementation with GPU/CPU auto-detection
"""

import os
import logging
import tempfile
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global model instance
model = None

# Configuration
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.webm'}
MODEL_SIZE = "large-v3"  # Options: tiny, base, small, medium, large-v3


def load_model():
    """Load Whisper model once at startup with GPU/CPU auto-detection"""
    global model
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    
    logger.info(f"Loading Whisper model: {MODEL_SIZE}")
    logger.info(f"Device: {device.upper()}")
    logger.info(f"Compute type: {compute_type}")
    
    try:
        model = WhisperModel(
            MODEL_SIZE,
            device=device,
            compute_type=compute_type,
            download_root="./models"
        )
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for model loading"""
    load_model()
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Speech-to-Text API",
    description="Convert audio files to text using Whisper",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "model": MODEL_SIZE,
        "device": "cuda" if torch.cuda.is_available() else "cpu"
    }


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio file to text
    
    Args:
        file: Audio file (wav, mp3, m4a, flac, ogg, webm)
    
    Returns:
        JSON with transcription, language, and duration
    """
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / (1024*1024)}MB"
        )
    
    temp_file = None
    
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        logger.info(f"Processing file: {file.filename} ({file_size / 1024:.2f} KB)")
        
        # Transcribe audio
        segments, info = model.transcribe(
            temp_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # Collect all segments
        transcription = " ".join([segment.text for segment in segments])
        
        logger.info(f"Transcription completed. Language: {info.language}")
        
        return JSONResponse(content={
            "transcription": transcription.strip(),
            "language_detected": info.language,
            "duration_seconds": round(info.duration, 2)
        })
    
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    finally:
        # Cleanup temporary file
        if temp_file and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
