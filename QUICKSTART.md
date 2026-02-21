# 🚀 Quick Start Guide

## Fastest Way to Run

### Option 1: Local (Python)

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

Server starts at: `http://localhost:8000`

### Option 2: Docker

```bash
# Build
docker build -t stt-api .

# Run
docker run -p 8000:8000 stt-api
```

## Test the API

```bash
# Health check
curl http://localhost:8000/

# Transcribe audio
curl -X POST http://localhost:8000/transcribe \
  -F "file=@your-audio.mp3"
```

## Expected Response

```json
{
  "transcription": "Your transcribed text here",
  "language_detected": "en",
  "duration_seconds": 12.45
}
```

## Model Download

First run will download the model (~3GB for large-v3). This happens automatically.

## Change Model Size

Edit `main.py`:
```python
MODEL_SIZE = "base"  # Options: tiny, base, small, medium, large-v3
```

Smaller models = faster but less accurate.

## AWS EC2 Deployment

```bash
# 1. Launch EC2 (t3.large or g4dn.xlarge)
# 2. SSH into instance
# 3. Install Docker
curl -fsSL https://get.docker.com | sh

# 4. Upload files and run
docker build -t stt-api .
docker run -d -p 8000:8000 stt-api

# 5. Access via public IP
curl http://YOUR-EC2-IP:8000/
```

## Troubleshooting

**Port in use?**
```python
# Change port in main.py
uvicorn.run("main:app", port=8001)
```

**Out of memory?**
```python
# Use smaller model
MODEL_SIZE = "base"
```

**GPU not working?**
```bash
# Check CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

---

**That's it! You're ready to transcribe audio.** 🎉
