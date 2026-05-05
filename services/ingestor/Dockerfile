FROM python:3.13-alpine

WORKDIR /app

COPY pazyr_core ./pazyr_core
RUN pip install --no-cache-dir -e ./pazyr_core

COPY services/ingestor ./ingestor
RUN pip install --no-cache-dir -e ./ingestor

CMD ["python", "-m", "ingestor.main"]