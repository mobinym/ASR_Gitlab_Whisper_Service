FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime



ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


WORKDIR /app/service

ENV PIP_INDEX_URL=http://nexus.aiopt.io:8081/repository/repo-pypi/simple/
ENV PIP_TRUSTED_HOST=nexus.aiopt.io

COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

#COPY whisper-service.py .


EXPOSE 8000


#CMD ["tail", "-f","/dev/null"]
CMD ["python", "whisper-service.py"]
