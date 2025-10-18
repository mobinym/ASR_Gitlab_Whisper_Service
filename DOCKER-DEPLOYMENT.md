# Docker Deployment Guide

Complete guide for deploying Faster Whisper Service with Docker.

## Quick Start

### GPU Deployment (Recommended)

```bash
# Start GPU service
docker-compose up -d whisper-gpu

# Check logs
docker-compose logs -f whisper-gpu

# Test
curl -X POST http://localhost:8000/transcribe/ -F "file=@audio.wav" -F "language=fa"
```

### CPU Deployment

```bash
# Start CPU service
docker-compose --profile cpu up -d whisper-cpu

# Check logs
docker-compose logs -f whisper-cpu

# Test (note port 8001)
curl -X POST http://localhost:8001/transcribe/ -F "file=@audio.wav" -F "language=fa"
```

---

## Files Overview

- **Dockerfile** - Container image definition
- **docker-compose.yml** - Service orchestration
- **.dockerignore** - Exclude files from build

---

## Configuration

### 1. Update docker-compose.yml

Edit volume paths to match your system:

```yaml
volumes:
  # Windows
  - D:/data/models:/data/models:ro

  # Linux
  - /data/models:/data/models:ro

  # Mac
  - ~/data/models:/data/models:ro
```

### 2. Set Environment Variables

In `docker-compose.yml`:

```yaml
environment:
  - DEFAULT_MODEL_NAME=203-final
  - MODELS_BASE_DIR=/data/models
  - DEVICE=cuda  # or 'cpu'
  - COMPUTE_TYPE=float16  # or 'int8' for CPU
  - MAX_WORKERS=4
  - BATCH_SIZE=16
```

### 3. Custom PyPI Index (Optional)

If using a custom PyPI server:

```yaml
build:
  args:
    PIP_INDEX_URL: http://nexus.aiopt.io:8081/repository/repo-pypi/simple/
    PIP_TRUSTED_HOST: nexus.aiopt.io
```

Or use default PyPI:

```yaml
build:
  args:
    PIP_INDEX_URL: https://pypi.org/simple
    PIP_TRUSTED_HOST: ""
```

---

## Building

### Build GPU Image

```bash
docker-compose build whisper-gpu
```

### Build CPU Image

```bash
docker-compose build whisper-cpu
```

### Build with Custom Args

```bash
docker build \
  --build-arg PIP_INDEX_URL=https://pypi.org/simple \
  -t whisper-service:latest .
```

---

## Running

### Start Services

```bash
# GPU service (default)
docker-compose up -d whisper-gpu

# CPU service
docker-compose --profile cpu up -d whisper-cpu

# Both services
docker-compose --profile cpu up -d
```

### Stop Services

```bash
# Stop all
docker-compose down

# Stop specific service
docker-compose stop whisper-gpu
```

### Restart Services

```bash
docker-compose restart whisper-gpu
```

---

## Monitoring

### View Logs

```bash
# Follow logs
docker-compose logs -f whisper-gpu

# Last 100 lines
docker-compose logs --tail=100 whisper-gpu

# Since 10 minutes ago
docker-compose logs --since 10m whisper-gpu
```

### Check Status

```bash
# Service status
docker-compose ps

# Health check
docker inspect --format='{{.State.Health.Status}}' whisper-service-gpu
```

### Resource Usage

```bash
# Container stats
docker stats whisper-service-gpu

# GPU usage (if NVIDIA)
nvidia-smi
```

---

## Testing

### Health Check

```bash
curl http://localhost:8000/
```

Response:
```json
{
  "status": "ok",
  "service": "faster-whisper",
  "model": "203-final",
  "device": "cuda"
}
```

### Transcribe Audio

```bash
curl -X POST http://localhost:8000/transcribe/ \
  -F "file=@audio.wav" \
  -F "language=fa" \
  -F "beam_size=5"
```

### Interactive API Docs

Visit: http://localhost:8000/docs

---

## Advanced Usage

### Custom .env File

```bash
# Mount custom .env
docker run -d \
  -v D:/data/models:/data/models:ro \
  -v $(pwd)/.env:/app/.env:ro \
  -p 8000:8000 \
  whisper-service:gpu
```

### Multiple Models

Run multiple services with different models:

```yaml
# docker-compose.override.yml
version: '3.8'

services:
  whisper-farsi:
    extends:
      service: whisper-gpu
    container_name: whisper-farsi
    ports:
      - "8001:8000"
    environment:
      - DEFAULT_MODEL_NAME=farsi-model

  whisper-english:
    extends:
      service: whisper-gpu
    container_name: whisper-english
    ports:
      - "8002:8000"
    environment:
      - DEFAULT_MODEL_NAME=english-model
```

Run:
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

### Volume for Model Cache

```yaml
volumes:
  - model-cache:/root/.cache/huggingface
```

This caches downloaded HuggingFace models.

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs whisper-gpu

# Common issues:
# 1. Model not found → Check volume path
# 2. CUDA error → Check GPU drivers
# 3. Port conflict → Change port in docker-compose.yml
```

### GPU Not Detected

```bash
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# If fails, install nvidia-container-toolkit:
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### Out of Memory

Reduce batch size in `docker-compose.yml`:

```yaml
environment:
  - BATCH_SIZE=4  # Reduce from 16
  - MAX_WORKERS=2  # Reduce from 4
```

### Model Loading Fails

```bash
# Check model files exist
docker run -it --rm -v D:/data/models:/data/models whisper-service:gpu ls -la /data/models/203-final

# Should show:
# config.json
# pytorch_model.bin
# etc.
```

---

## Production Deployment

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml whisper

# Scale service
docker service scale whisper_whisper-gpu=3

# Check status
docker service ls
docker service ps whisper_whisper-gpu
```

### Using Kubernetes

Convert to Kubernetes:

```bash
# Install kompose
curl -L https://github.com/kubernetes/kompose/releases/download/v1.31.2/kompose-linux-amd64 -o kompose
chmod +x kompose

# Convert
./kompose convert -f docker-compose.yml

# Apply
kubectl apply -f whisper-gpu-deployment.yaml
kubectl apply -f whisper-gpu-service.yaml
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name whisper.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # For large audio files
        client_max_body_size 100M;
        proxy_read_timeout 300s;
    }
}
```

---

## Performance Tuning

### GPU Optimization

```yaml
environment:
  - DEVICE=cuda
  - COMPUTE_TYPE=int8_float16  # Fastest
  - BATCH_SIZE=32  # Max throughput
  - MAX_WORKERS=8
```

### CPU Optimization

```yaml
environment:
  - DEVICE=cpu
  - COMPUTE_TYPE=int8  # Fastest for CPU
  - BATCH_SIZE=4
  - MAX_WORKERS=2
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
```

---

## Security

### Run as Non-Root

Add to Dockerfile:

```dockerfile
# Create user
RUN useradd -m -u 1000 whisper && \
    chown -R whisper:whisper /app

USER whisper
```

### Read-Only Filesystem

```yaml
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp
  - /app/tmp
```

### Network Isolation

```yaml
networks:
  whisper-net:
    driver: bridge
    internal: true  # No internet access
```

---

## Backup & Recovery

### Backup Configuration

```bash
# Backup .env and docker-compose.yml
tar -czf whisper-config-backup.tar.gz .env docker-compose.yml

# Backup models (if needed)
tar -czf whisper-models-backup.tar.gz D:/data/models/203-final
```

### Restore

```bash
# Extract config
tar -xzf whisper-config-backup.tar.gz

# Rebuild and restart
docker-compose up -d --build
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/docker.yml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build image
        run: docker build -t whisper-service:latest .

      - name: Push to registry
        run: docker push whisper-service:latest
```

---

## Useful Commands

```bash
# View container info
docker inspect whisper-service-gpu

# Execute command in container
docker exec -it whisper-service-gpu bash

# Copy files from container
docker cp whisper-service-gpu:/app/logs ./logs

# Save image
docker save whisper-service:gpu | gzip > whisper-service-gpu.tar.gz

# Load image
docker load < whisper-service-gpu.tar.gz

# Cleanup
docker system prune -a
```

---

## Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify volumes: `docker-compose config`
3. Test connectivity: `docker exec whisper-service-gpu curl localhost:8000`
4. Review [SETUP-GUIDE.md](SETUP-GUIDE.md)

---

**Ready for production deployment!** 🚀
