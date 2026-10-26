FROM python:3.12-slim-bookworm

RUN python -m pip install --no-cache-dir pytest==9.1.1

WORKDIR /app
COPY converter.py report.py config.json /app/
COPY resources /app/resources
